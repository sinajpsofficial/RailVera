from sqlalchemy import String, Text, ARRAY, TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector
from sqlalchemy.orm import Mapped, mapped_column
import uuid
import datetime
from app.database.connection import Base
from typing import List, Dict, Optional, Any


class Rule(Base):
    """
    Represents a single structured rule extracted from rules.md.
    The embedding column stores a 384-float vector for semantic search.
    """
    __tablename__ = "rules"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    rule_id: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    rule_name: Mapped[str] = mapped_column(String(255), nullable=False)
    domain: Mapped[str] = mapped_column(String(100), nullable=False)
    source: Mapped[str] = mapped_column(String(50), default="rules.md")
    chapter: Mapped[Optional[str]] = mapped_column(String(100))
    section: Mapped[Optional[str]] = mapped_column(String(100))
    description: Mapped[str] = mapped_column(Text, nullable=False)
    eligibility_conditions: Mapped[List[Dict[str, Any]]] = mapped_column(JSONB, default=list)
    required_documents: Mapped[List[str]] = mapped_column(JSONB, default=list)
    disqualifying_conditions: Mapped[List[Dict[str, Any]]] = mapped_column(JSONB, default=list)
    exceptions: Mapped[List[Dict[str, Any]]] = mapped_column(JSONB, default=list)
    decision_logic: Mapped[Optional[str]] = mapped_column(Text)
    authority: Mapped[Optional[str]] = mapped_column(String(255))
    related_rules: Mapped[List[str]] = mapped_column(ARRAY(Text), default=list)
    embedding: Mapped[Any] = mapped_column(Vector(384))
    raw_text: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
