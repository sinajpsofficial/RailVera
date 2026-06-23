from sqlalchemy import Column, String, Text, TIMESTAMP, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
import uuid
from app.database.connection import Base

class EligibilityReport(Base):
    __tablename__ = "eligibility_reports"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    case_id = Column(UUID(as_uuid=True), ForeignKey("cases.id", ondelete="CASCADE"))
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    domain = Column(String(100))
    decision = Column(String(100))
    eligibility_status = Column(String(50))
    supporting_rules = Column(JSONB, default=list)
    supporting_facts = Column(JSONB, default=list)
    missing_information = Column(JSONB, default=list)
    risk_indicators = Column(JSONB, default=list)
    administrative_notes = Column(Text)
    confidence_level = Column(String(50))
    report_pdf_path = Column(String(500))
    generated_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
