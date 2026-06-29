from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID

from app.database.connection import get_db
from app.models.case import Case
from app.models.conversation import Conversation
from app.models.user import User
from app.schemas.eligibility import EligibilityCheckRequest, EligibilityCheckResponse
from app.core.security import get_current_user
from app.core.eligibility_engine import EligibilityEngine

router = APIRouter()

@router.post("/check", response_model=EligibilityCheckResponse)
async def check_eligibility(
    req: EligibilityCheckRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # 1. Fetch Case
    stmt = select(Case).where(Case.id == req.case_id)
    result = await db.execute(stmt)
    case_obj = result.scalars().first()
    if not case_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Case not found"
        )
    
    # 2. Check Permissions
    if case_obj.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to run eligibility checks for this case"
        )
    
    # 3. Retrieve Conversation History for Case
    conv_stmt = select(Conversation).where(Conversation.case_id == req.case_id).order_by(Conversation.created_at.asc())
    conv_res = await db.execute(conv_stmt)
    conversations = conv_res.scalars().all()
    history = [{"role": c.role, "message": c.message} for c in conversations]
    
    # 4. Instantiate Engine and Evaluate
    engine = EligibilityEngine()
    eval_result = await engine.evaluate(
        query=case_obj.query_text or f"Check eligibility for {case_obj.domain}",
        domain=case_obj.domain,
        submitted_docs=case_obj.submitted_documents or [],
        extracted_facts=case_obj.extracted_facts or {},
        conversation_history=history,
        db=db
    )
    
    # 5. Update Case Object based on evaluation result
    case_obj.decision = eval_result.decision
    case_obj.confidence = eval_result.confidence_level
    case_obj.decision_reasoning = eval_result.administrative_notes
    case_obj.rules_applied = [
        r.get("rule_id") for r in eval_result.supporting_rules if r.get("rule_id")
    ]
    
    # Update Case status
    if eval_result.decision in ["Eligible", "Not Eligible"]:
        case_obj.status = "evaluated"
        case_obj.review_status = "pending_review"
    elif "Blocked" in eval_result.eligibility_status or eval_result.document_demand_notice:
        case_obj.status = "blocked"
    else:
        case_obj.status = "open"
        
    db.add(case_obj)
    await db.commit()
    await db.refresh(case_obj)
    
    # 6. Return response
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
