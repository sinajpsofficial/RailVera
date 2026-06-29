from sqlalchemy import String, Text, TIMESTAMP, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import Mapped, mapped_column
import uuid
import datetime
from app.database.connection import Base
from typing import Optional, List, Dict, Any

class EligibilityReport(Base):
    __tablename__ = "eligibility_reports"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    case_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("cases.id", ondelete="CASCADE"))
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    domain: Mapped[Optional[str]] = mapped_column(String(100))
    decision: Mapped[Optional[str]] = mapped_column(String(100))
    eligibility_status: Mapped[Optional[str]] = mapped_column(String(50))
    supporting_rules: Mapped[List[Dict[str, Any]]] = mapped_column(JSONB, default=list)
    supporting_facts: Mapped[List[Dict[str, Any]]] = mapped_column(JSONB, default=list)
    missing_information: Mapped[List[str]] = mapped_column(JSONB, default=list)
    risk_indicators: Mapped[List[str]] = mapped_column(JSONB, default=list)
    administrative_notes: Mapped[Optional[str]] = mapped_column(Text)
    confidence_level: Mapped[Optional[str]] = mapped_column(String(50))
    report_pdf_path: Mapped[Optional[str]] = mapped_column(String(500))
    generated_at: Mapped[datetime.datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
