import logging
from datetime import datetime, timezone
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.chat_fact_parser import ChatFactParser
from app.core.document_demand_engine import DocumentDemandEngine
from app.core.eligibility_engine import EligibilityEngine
from app.core.security import get_current_user
from app.database.connection import get_db
from app.models.case import Case
from app.models.conversation import Conversation
from app.models.user import User
from app.schemas.case import CaseCreate, CaseResponse, CaseReviewRequest, CaseReviewResponse, ConversationResponse
from app.schemas.eligibility import EligibilityCheckResponse
from app.utils.audit_service import AuditService, AuditAction

logger = logging.getLogger(__name__)
router = APIRouter()


# ── Helper ─────────────────────────────────────────────────────────────────────

async def _fetch_case_or_404(case_id: UUID, db: AsyncSession) -> Case:
    result = await db.execute(select(Case).where(Case.id == case_id))
    case_obj = result.scalars().first()
    if not case_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found")
    return case_obj


def _assert_owner_or_admin(case_obj: Case, current_user: User) -> None:
    if case_obj.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")


# ── Create Case ───────────────────────────────────────────────────────────────

@router.post("/", response_model=CaseResponse, status_code=status.HTTP_201_CREATED)
async def create_case(
    case_in: CaseCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    demand_engine = DocumentDemandEngine()
    domain_req = demand_engine.requirements.get(case_in.domain, {})
    required_docs = domain_req.get("mandatory", [])

    demand_res = demand_engine.check(
        domain=case_in.domain,
        submitted_doc_types=[],
        employee_facts={}
    )

    db_case = Case(
        user_id=current_user.id,
        domain=case_in.domain,
        query_text=case_in.query_text,
        status="blocked" if not demand_res.all_present else "open",
        required_documents=required_docs,
        submitted_documents=[],
        missing_documents=demand_res.missing,
        extracted_facts={},
        rules_applied=[],
        review_status="draft",
    )
    db.add(db_case)
    await db.commit()
    await db.refresh(db_case)

    await AuditService.log(
        db=db,
        user_id=current_user.id,
        action=AuditAction.CASE_CREATED,
        resource_type="case",
        resource_id=db_case.id,
        payload={"domain": case_in.domain, "query_text": case_in.query_text},
        response_status=201,
        request=request,
    )
    return db_case


# ── Get My Cases ───────────────────────────────────────────────────────────────

@router.get("/me", response_model=List[CaseResponse])
async def get_my_cases(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    stmt = select(Case).where(Case.user_id == current_user.id).order_by(Case.created_at.desc())
    result = await db.execute(stmt)
    return result.scalars().all()


# ── Get Cases by User (admin) ─────────────────────────────────────────────────

@router.get("/user/{user_id}", response_model=List[CaseResponse])
async def get_user_cases(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.id != user_id and current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
    stmt = select(Case).where(Case.user_id == user_id).order_by(Case.created_at.desc())
    result = await db.execute(stmt)
    return result.scalars().all()


# ── Get Pending Cases (admin only) ───────────────────────────────────────────

@router.get("/pending", response_model=List[CaseResponse])
async def get_pending_cases(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only Personnel Officers (admin role) may access pending cases."
        )
    stmt = select(Case).where(Case.review_status == "pending_review").order_by(Case.created_at.desc())
    result = await db.execute(stmt)
    return result.scalars().all()


# ── Get Case Conversation History ────────────────────────────────────────────

@router.get("/{case_id}/conversation", response_model=List[ConversationResponse])
async def get_case_conversation(
    case_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    case_obj = await _fetch_case_or_404(case_id, db)
    _assert_owner_or_admin(case_obj, current_user)
    
    stmt = select(Conversation).where(Conversation.case_id == case_id).order_by(Conversation.created_at.asc())
    result = await db.execute(stmt)
    return result.scalars().all()


# ── Get Single Case ───────────────────────────────────────────────────────────

@router.get("/{case_id}", response_model=CaseResponse)
async def get_case(
    case_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    case_obj = await _fetch_case_or_404(case_id, db)
    _assert_owner_or_admin(case_obj, current_user)
    return case_obj


# ── Reply to Case (chat + re-evaluation) ─────────────────────────────────────

class CaseReplyRequest(BaseModel):
    message: str


@router.post("/{case_id}/reply", response_model=EligibilityCheckResponse)
async def reply_to_case(
    case_id: UUID,
    req: CaseReplyRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Accepts a free-text reply from the employee, extracts facts via the LLM-powered
    ChatFactParser, merges them into the case, re-runs eligibility, and returns
    the updated result. The AI decision is set to review_status='pending_review'
    once a Eligible/Not Eligible conclusion is reached.
    """
    case_obj = await _fetch_case_or_404(case_id, db)
    _assert_owner_or_admin(case_obj, current_user)

    # 1. Save user message
    user_conv = Conversation(
        user_id=current_user.id,
        case_id=case_id,
        role="user",
        message=req.message,
        message_type="text"
    )
    db.add(user_conv)

    # 2. Parse facts from the message (LLM + regex fallback)
    parser = ChatFactParser()
    new_facts = parser.parse(req.message)
    merged_facts = dict(case_obj.extracted_facts or {})
    merged_facts.update(new_facts)
    case_obj.extracted_facts = merged_facts
    db.add(case_obj)
    await db.commit()
    await db.refresh(case_obj)

    # 3. Load full conversation history
    conv_stmt = select(Conversation).where(
        Conversation.case_id == case_id
    ).order_by(Conversation.created_at.asc())
    conv_res = await db.execute(conv_stmt)
    history = [{"role": c.role, "message": c.message} for c in conv_res.scalars().all()]

    # 4. Re-run eligibility engine
    engine = EligibilityEngine()
    eval_result = await engine.evaluate(
        query=case_obj.query_text or req.message,
        domain=case_obj.domain,
        submitted_docs=case_obj.submitted_documents or [],
        extracted_facts=case_obj.extracted_facts or {},
        conversation_history=history,
        db=db
    )

    # 5. Save AI response to conversation
    ai_conv = Conversation(
        user_id=current_user.id,
        case_id=case_id,
        role="assistant",
        message=eval_result.administrative_notes or eval_result.eligibility_status,
        message_type="text",
        rules_cited=[r.get("rule_id") for r in eval_result.supporting_rules if r.get("rule_id")]
    )
    db.add(ai_conv)

    # 6. Update Case with AI decision
    case_obj.decision = eval_result.decision
    case_obj.confidence = eval_result.confidence_level
    case_obj.decision_reasoning = eval_result.administrative_notes
    case_obj.rules_applied = [
        r.get("rule_id") for r in eval_result.supporting_rules if r.get("rule_id")
    ]

    if eval_result.decision in ("Eligible", "Not Eligible"):
        case_obj.status = "evaluated"
        # Move to pending_review so a Personnel Officer must approve before PDF
        case_obj.review_status = "pending_review"
    elif eval_result.document_demand_notice:
        case_obj.status = "blocked"

    db.add(case_obj)
    await db.commit()

    # 7. Audit log
    await AuditService.log(
        db=db,
        user_id=current_user.id,
        action=AuditAction.CASE_EVALUATED,
        resource_type="case",
        resource_id=case_obj.id,
        payload={
            "domain": case_obj.domain,
            "decision": eval_result.decision,
            "confidence": eval_result.confidence_level,
            "facts_count": len(merged_facts),
            "rules_count": len(eval_result.supporting_rules),
        },
        response_status=200,
        request=request,
    )

    logger.info(
        f"[Cases] Case {case_id} evaluated: decision='{eval_result.decision}', "
        f"confidence='{eval_result.confidence_level}', review_status='{case_obj.review_status}'"
    )

    return EligibilityCheckResponse(
        case_id=case_obj.id,
        decision=eval_result.decision,
        eligibility_status=eval_result.eligibility_status,
        supporting_rules=eval_result.supporting_rules,
        supporting_facts=eval_result.supporting_facts,
        missing_information=eval_result.missing_information,
        risk_indicators=eval_result.risk_indicators,
        administrative_notes=eval_result.administrative_notes,
        confidence_level=eval_result.confidence_level,
        follow_up_questions=eval_result.follow_up_questions,
        document_demand_notice=eval_result.document_demand_notice
    )


# ── HITL Review Endpoint ──────────────────────────────────────────────────────

@router.post("/{case_id}/review", response_model=CaseReviewResponse)
async def review_case(
    case_id: UUID,
    review_req: CaseReviewRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Personnel Officer (admin role only) reviews and approves or rejects
    the AI-generated eligibility decision for a case.

    - Only cases with review_status='pending_review' can be reviewed.
    - Approval unlocks PDF report generation.
    - Rejection requires the employee to provide more information or re-apply.
    - Every review action is recorded in the audit log with the officer's notes.
    """
    # Only admins (Personnel Officers) may review
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only Personnel Officers (admin role) may review AI decisions."
        )

    case_obj = await _fetch_case_or_404(case_id, db)

    # Guard: only pending_review cases can be acted on
    if case_obj.review_status != "pending_review":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"This case cannot be reviewed in its current state. "
                f"review_status='{case_obj.review_status}'. "
                "Only cases with review_status='pending_review' may be approved or rejected."
            )
        )

    now = datetime.now(timezone.utc)
    action = review_req.action.lower()

    if action == "approve":
        case_obj.review_status = "approved"
        case_obj.status = "approved"
        audit_action = AuditAction.CASE_REVIEW_APPROVED
        message = (
            f"Case {case_id} has been APPROVED by Personnel Officer {current_user.name}. "
            "PDF report may now be generated."
        )
        logger.info(f"[Review] Case {case_id} APPROVED by {current_user.id} ({current_user.name})")

    else:  # reject
        case_obj.review_status = "rejected"
        case_obj.status = "rejected"
        audit_action = AuditAction.CASE_REVIEW_REJECTED
        message = (
            f"Case {case_id} has been REJECTED by Personnel Officer {current_user.name}. "
            "The employee has been notified and may re-submit with additional information."
        )
        logger.info(f"[Review] Case {case_id} REJECTED by {current_user.id} ({current_user.name})")

    case_obj.reviewed_by = current_user.id
    case_obj.review_notes = review_req.notes
    case_obj.reviewed_at = now
    db.add(case_obj)
    await db.commit()
    await db.refresh(case_obj)

    # Audit log — includes the officer's notes for legal record
    await AuditService.log(
        db=db,
        user_id=current_user.id,
        action=audit_action,
        resource_type="case",
        resource_id=case_obj.id,
        payload={
            "action": action,
            "review_notes": review_req.notes,
            "case_domain": case_obj.domain,
            "ai_decision": case_obj.decision,
            "ai_confidence": case_obj.confidence,
        },
        response_status=200,
        request=request,
    )

    return CaseReviewResponse(
        case_id=case_obj.id,
        review_status=case_obj.review_status,
        reviewed_by=current_user.id,
        review_notes=review_req.notes,
        reviewed_at=now,
        message=message,
    )
