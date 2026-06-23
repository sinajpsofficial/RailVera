from sqlalchemy import Column, String, Text, TIMESTAMP, ForeignKey, ARRAY
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid
from app.database.connection import Base

class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    case_id = Column(UUID(as_uuid=True), ForeignKey("cases.id", ondelete="CASCADE"))
    role = Column(String(20), nullable=False)
    message = Column(Text, nullable=False)
    message_type = Column(String(50), default="text")
    rules_cited = Column(ARRAY(String), default=list)
    documents_cited = Column(ARRAY(UUID(as_uuid=True)), default=list)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
