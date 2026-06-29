from sqlalchemy import String, Text, TIMESTAMP, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy.sql import func
from sqlalchemy.orm import Mapped, mapped_column
import uuid
import datetime
from app.database.connection import Base
from typing import List, Dict, Optional, Any

class Case(Base):
    __tablename__ = "cases"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    domain: Mapped[str] = mapped_column(String(100), nullable=False)
    query_text: Mapped[Optional[str]] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(50), default="open")
    required_documents: Mapped[List[str]] = mapped_column(JSONB, default=list)
    submitted_documents: Mapped[List[str]] = mapped_column(JSONB, default=list)
    missing_documents: Mapped[List[str]] = mapped_column(JSONB, default=list)
    extracted_facts: Mapped[Dict[str, Any]] = mapped_column(JSONB, default=dict)
    decision: Mapped[Optional[str]] = mapped_column(String(100))
    confidence: Mapped[Optional[str]] = mapped_column(String(50))
    decision_reasoning: Mapped[Optional[str]] = mapped_column(Text)
    rules_applied: Mapped[List[str]] = mapped_column(ARRAY(String), default=list)
    review_status: Mapped[str] = mapped_column(String(30), default="draft", nullable=False)
    reviewed_by: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    review_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    reviewed_at: Mapped[Optional[datetime.datetime]] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime.datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())
