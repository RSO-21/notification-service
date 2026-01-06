from datetime import datetime
from pydantic import BaseModel
from typing import Optional, Dict, Any

class NotificationCreate(BaseModel):
    user_id: str
    type: str = "INFO"
    title: str
    message: str
    meta: Optional[Dict[str, Any]] = None

class NotificationOut(BaseModel):
    id: int
    user_id: str
    type: str
    title: str
    message: str
    meta: Optional[dict] = None
    is_read: bool
    created_at: datetime

    class Config:
        from_attributes = True
