from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel

from app.database.connection import get_db
from app.models.case import Case
from app.models.conversation import Conversation
from app.schemas.case import CaseCreate, CaseResponse
from app.schemas.eligibility import EligibilityCheckResponse
from app.core.security import get_current_user
from app.models.user import User
from app.core.document_demand_engine import DocumentDemandEngine
from app.core.eligibility_engine import EligibilityEngine
from app.core.chat_fact_parser import ChatFactParser

router = APIRouter()


@router.post("/", response_model=CaseResponse, status_code=status.HTTP_201_CREATED)
async def create_case(
    case_in: CaseCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Retrieve standard requirements for the domain
    demand_engine = DocumentDemandEngine()
    domain_req = demand_engine.requirements.get(case_in.domain, {})
    required_docs = domain_req.get("mandatory", [])
    
    # Evaluate initial checklist
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
        rules_applied=[]
    )
    db.add(db_case)
    await db.commit()
    await db.refresh(db_case)
    return db_case

@router.get("/me", response_model=List[CaseResponse])
async def get_my_cases(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    stmt = select(Case).where(Case.user_id == current_user.id).order_by(Case.created_at.desc())
    result = await db.execute(stmt)
    return result.scalars().all()

@router.get("/user/{user_id}", response_model=List[CaseResponse])
async def get_user_cases(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Only admin or the user themselves can retrieve this
    if current_user.id != user_id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access these cases"
        )
    stmt = select(Case).where(Case.user_id == user_id).order_by(Case.created_at.desc())
    result = await db.execute(stmt)
    return result.scalars().all()

@router.get("/{case_id}", response_model=CaseResponse)
async def get_case(
    case_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    stmt = select(Case).where(Case.id == case_id)
    result = await db.execute(stmt)
    case_obj = result.scalars().first()
    if not case_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Case not found"
        )
    if case_obj.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this case"
        )
    return case_obj


class CaseReplyRequest(BaseModel):
    message: str


@router.post("/{case_id}/reply", response_model=EligibilityCheckResponse)
async def reply_to_case(
    case_id: UUID,
    req: CaseReplyRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Accepts a free-text reply from the user, extracts structured facts from it,
    merges those facts into the case record, saves the conversation turn, then
    re-evaluates eligibility and returns the updated result.
    """
    # 1. Fetch case
    stmt = select(Case).where(Case.id == case_id)
    result = await db.execute(stmt)
    case_obj = result.scalars().first()
    if not case_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found")
    if case_obj.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")

    # 2. Save user message to conversation history
    user_conv = Conversation(
        user_id=current_user.id,
        case_id=case_id,
        role="user",
        message=req.message,
        message_type="text"
    )
    db.add(user_conv)

    # 3. Parse facts from user's free-text reply and merge into case
    parser = ChatFactParser()
    new_facts = parser.parse(req.message)

    # Merge: only overwrite keys where we extracted a real value
    merged_facts = dict(case_obj.extracted_facts or {})
    merged_facts.update(new_facts)
    case_obj.extracted_facts = merged_facts
    db.add(case_obj)
    await db.commit()
    await db.refresh(case_obj)

    # 4. Load full conversation history for the engine
    conv_stmt = select(Conversation).where(
        Conversation.case_id == case_id
    ).order_by(Conversation.created_at.asc())
    conv_res = await db.execute(conv_stmt)
    conversations = conv_res.scalars().all()
    history = [{"role": c.role, "message": c.message} for c in conversations]

    # 5. Re-run eligibility engine with updated facts
    engine = EligibilityEngine()
    eval_result = await engine.evaluate(
        query=case_obj.query_text or req.message,
        domain=case_obj.domain,
        submitted_docs=case_obj.submitted_documents or [],
        extracted_facts=case_obj.extracted_facts or {},
        conversation_history=history,
        db=db
    )

    # 6. Save AI reply to conversation
    ai_conv = Conversation(
        user_id=current_user.id,
        case_id=case_id,
        role="assistant",
        message=eval_result.administrative_notes or eval_result.eligibility_status,
        message_type="text",
        rules_cited=[r.get("rule_id") for r in eval_result.supporting_rules if r.get("rule_id")]
    )
    db.add(ai_conv)

    # 7. Update case decision
    case_obj.decision = eval_result.decision
    case_obj.confidence = eval_result.confidence_level
    case_obj.decision_reasoning = eval_result.administrative_notes
    case_obj.rules_applied = [
        r.get("rule_id") for r in eval_result.supporting_rules if r.get("rule_id")
    ]
    if eval_result.decision in ["Eligible", "Not Eligible"]:
        case_obj.status = "evaluated"
    elif eval_result.document_demand_notice:
        case_obj.status = "blocked"
    db.add(case_obj)
    await db.commit()

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

