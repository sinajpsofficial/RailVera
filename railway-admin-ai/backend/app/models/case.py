from sqlalchemy import Column, String, Text, TIMESTAMP, ARRAY, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
import uuid
from app.database.connection import Base

class Case(Base):
    __tablename__ = "cases"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    domain = Column(String(100), nullable=False)
    query_text = Column(Text)
    status = Column(String(50), default="open")
    required_documents = Column(JSONB, default=list)
    submitted_documents = Column(JSONB, default=list)
    missing_documents = Column(JSONB, default=list)
    extracted_facts = Column(JSONB, default=dict)
    decision = Column(String(100))
    confidence = Column(String(50))
    decision_reasoning = Column(Text)
    rules_applied = Column(ARRAY(String), default=list)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())
