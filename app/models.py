from sqlalchemy import Column, Integer, String, Boolean, DateTime, JSON
from datetime import datetime
from app.database import Base

class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True, nullable=False)

    type = Column(String, nullable=False, default="INFO")
    title = Column(String, nullable=False)
    message = Column(String, nullable=False)

    meta = Column(JSON, nullable=True)
    is_read = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
