from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime

class ReportGenerateRequest(BaseModel):
    case_id: UUID

class ReportResponse(BaseModel):
    id: UUID
    case_id: UUID
    user_id: UUID
    domain: Optional[str] = None
    decision: Optional[str] = None
    eligibility_status: Optional[str] = None
    supporting_rules: List[Dict[str, Any]] = []
    supporting_facts: List[Dict[str, Any]] = []
    missing_information: List[str] = []
    risk_indicators: List[str] = []
    administrative_notes: Optional[str] = None
    confidence_level: Optional[str] = None
    report_pdf_path: Optional[str] = None
    generated_at: datetime

    class Config:
        from_attributes = True
