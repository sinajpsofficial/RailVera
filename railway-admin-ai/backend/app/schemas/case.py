from pydantic import BaseModel
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
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
