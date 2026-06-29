from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime


class CaseCreate(BaseModel):
    domain: str
    query_text: Optional[str] = None


class CaseResponse(BaseModel):
    id: UUID
    user_id: UUID
    domain: str
    query_text: Optional[str] = None
    status: str
    required_documents: List[str] = []
    submitted_documents: List[str] = []
    missing_documents: List[str] = []
    extracted_facts: Dict[str, Any] = {}
    decision: Optional[str] = None
    confidence: Optional[str] = None
    decision_reasoning: Optional[str] = None
    rules_applied: List[str] = []
    # HITL review fields
    review_status: str = "draft"
    reviewed_by: Optional[UUID] = None
    review_notes: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CaseReviewRequest(BaseModel):
    """Request body for a Personnel Officer to approve or reject an AI decision."""
    action: str = Field(
        ...,
        description="Must be exactly 'approve' or 'reject'",
        pattern="^(approve|reject)$"
    )
    notes: str = Field(
        ...,
        min_length=10,
        description="Mandatory written justification from the reviewing officer (minimum 10 characters)."
    )


class CaseReviewResponse(BaseModel):
    """Response after a review action."""
    case_id: UUID
    review_status: str           # approved | rejected
    reviewed_by: UUID
    review_notes: str
    reviewed_at: datetime
    message: str                 # Human-readable confirmation

    class Config:
        from_attributes = True


class ConversationResponse(BaseModel):
    """Response representing a historical conversation message."""
    id: UUID
    role: str
    message: str
    message_type: str
    rules_cited: List[str] = []
    created_at: datetime

    class Config:
        from_attributes = True
