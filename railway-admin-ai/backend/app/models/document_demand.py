from sqlalchemy import Column, String, Text, TIMESTAMP, ForeignKey, ARRAY
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid
from app.database.connection import Base

class DocumentDemand(Base):
    __tablename__ = "document_demands"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    case_id = Column(UUID(as_uuid=True), ForeignKey("cases.id", ondelete="CASCADE"))
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    demanded_document = Column(String(255), nullable=False)
    reason = Column(Text, nullable=False)
    rule_citations = Column(ARRAY(String), default=list)
    demanded_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    fulfilled_at = Column(TIMESTAMP(timezone=True), nullable=True)
    fulfilled_by_document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id"), nullable=True)
    status = Column(String(50), default="pending")
