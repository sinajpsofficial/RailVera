from sqlalchemy import Column, String, Text, ARRAY, TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector
import uuid
from app.database.connection import Base


class Rule(Base):
    """
    Represents a single structured rule extracted from rules.md.
    The embedding column stores a 384-float vector for semantic search.
    """
    __tablename__ = "rules"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    rule_id = Column(String(50), unique=True, nullable=False)
    rule_name = Column(String(255), nullable=False)
    domain = Column(String(100), nullable=False)
    source = Column(String(50), default="rules.md")
    chapter = Column(String(100))
    section = Column(String(100))
    description = Column(Text, nullable=False)
    eligibility_conditions = Column(JSONB, default=list)
    required_documents = Column(JSONB, default=list)
    disqualifying_conditions = Column(JSONB, default=list)
    exceptions = Column(JSONB, default=list)
    decision_logic = Column(Text)
    authority = Column(String(255))
    related_rules = Column(ARRAY(Text), default=list)
    embedding = Column(Vector(384))
    raw_text = Column(Text, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
