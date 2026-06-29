from pydantic import BaseModel
from typing import Optional, Dict, Any
from uuid import UUID
from datetime import datetime


class DocumentResponse(BaseModel):
    id: UUID
    user_id: UUID
    case_id: Optional[UUID] = None
    original_filename: str
    stored_filename: str
    storage_path: str
    document_type: Optional[str] = None
    classification_confidence: Optional[float] = None
    ocr_quality_score: Optional[float] = None
    is_readable: bool
    is_verified: bool
    rejection_reason: Optional[str] = None
    extracted_facts: Dict[str, Any] = {}
    raw_text: Optional[str] = None
    file_size_bytes: Optional[int] = None
    mime_type: Optional[str] = None
    # Background processing state
    processing_status: str = "pending"   # pending | processing | done | failed
    processing_error: Optional[str] = None
    uploaded_at: datetime
    processed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class DocumentStatusResponse(BaseModel):
    """Lightweight status-check response — avoids sending large raw_text on polling."""
    id: UUID
    processing_status: str
    document_type: Optional[str] = None
    classification_confidence: Optional[float] = None
    ocr_quality_score: Optional[float] = None
    is_readable: bool
    is_verified: bool
    rejection_reason: Optional[str] = None
    extracted_facts: Dict[str, Any] = {}
    processed_at: Optional[datetime] = None
    processing_error: Optional[str] = None

    class Config:
        from_attributes = True
