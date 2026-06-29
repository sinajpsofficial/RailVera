from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Dict, Any

from app.database.connection import get_db
from app.core.security import get_current_active_admin
from app.models.case import Case
from app.models.user import User
from app.models.document import Document
from app.core.llm_client import LLMClient
from app.models.user import User as UserModel # Avoid shadowing

router = APIRouter()

@router.get("/metrics", response_model=Dict[str, Any])
async def get_system_metrics(
    db: AsyncSession = Depends(get_db),
    current_admin: UserModel = Depends(get_current_active_admin)
):
    """
    Returns system-wide metrics for the administrative dashboard.
    """
    metrics: Dict[str, Any] = {}

    # Total cases
    result = await db.execute(select(func.count(Case.id)))
    metrics["total_cases"] = result.scalar() or 0

    # Cases by status
    result = await db.execute(select(Case.status, func.count(Case.id)).group_by(Case.status))
    metrics["cases_by_status"] = {row[0]: row[1] for row in result.all()}

    # Total users
    result = await db.execute(select(func.count(User.id)))
    metrics["total_users"] = result.scalar() or 0

    # Total documents processed
    result = await db.execute(select(func.count(Document.id)).where(Document.processing_status == "done"))
    metrics["processed_documents"] = result.scalar() or 0

    return metrics

@router.get("/llm/health", response_model=Dict[str, Any])
async def get_llm_health(
    current_admin: UserModel = Depends(get_current_active_admin)
):
    """
    Checks the health and availability of the primary LLM provider.
    """
    client = LLMClient()
    try:
        # A simple ping prompt to verify connectivity and parsing
        response = await client.generate(
            prompt="Reply with exactly the word 'OK'.",
            retrieved_rules=[],
            extracted_facts={},
            missing_documents=[]
        )
        return {
            "status": "healthy",
            "provider_response": response,
            "message": "LLM API is reachable and responding correctly."
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "message": "Failed to communicate with LLM provider."
        }
