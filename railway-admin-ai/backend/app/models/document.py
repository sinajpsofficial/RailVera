from sqlalchemy import Column, String, Text, Integer, Boolean, Numeric, TIMESTAMP, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
import uuid
from app.database.connection import Base

class Document(Base):
    __tablename__ = "documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    case_id = Column(UUID(as_uuid=True), ForeignKey("cases.id", ondelete="SET NULL"), nullable=True)
    original_filename = Column(String(255), nullable=False)
    stored_filename = Column(String(255), nullable=False)
    storage_path = Column(String(500), nullable=False)
    document_type = Column(String(100))
    classification_confidence = Column(Numeric(5, 4))
    ocr_quality_score = Column(Numeric(5, 4))
    is_readable = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    rejection_reason = Column(Text)
    extracted_facts = Column(JSONB, default=dict)
    raw_text = Column(Text)
    file_size_bytes = Column(Integer)
    mime_type = Column(String(100))
    # Background processing state: pending → processing → done | failed
    processing_status = Column(String(20), default="pending", nullable=False)
    processing_error = Column(Text, nullable=True)       # set if processing_status == 'failed'
    uploaded_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    processed_at = Column(TIMESTAMP(timezone=True))
