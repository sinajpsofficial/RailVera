from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from uuid import UUID

class EligibilityCheckRequest(BaseModel):
    case_id: UUID

class EligibilityCheckResponse(BaseModel):
    case_id: UUID
    decision: str
    eligibility_status: str
    supporting_rules: List[Dict[str, Any]] = []
    supporting_facts: List[Dict[str, Any]] = []
    missing_information: List[str] = []
    risk_indicators: List[str] = []
    administrative_notes: str = ""
    confidence_level: str
    follow_up_questions: List[str] = []
    document_demand_notice: str = ""

    class Config:
        from_attributes = True
