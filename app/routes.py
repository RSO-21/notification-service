import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session

from app import models
from app.database import get_db_session as get_db
from app.schemas import NotificationOut

router = APIRouter()
logger = logging.getLogger(__name__)

def get_tenant_id(x_tenant_id: Optional[str] = Header(None)) -> str:
    return x_tenant_id or "public"

def get_db_with_schema(tenant_id: str = Depends(get_tenant_id)):
    return get_db(schema=tenant_id)

@router.get("/", response_model=List[NotificationOut])
def list_notifications(
    user_id: str,
    unread_only: bool = False,
    limit: int = 50,
    db: Session = Depends(get_db_with_schema),
):
    q = db.query(models.Notification).filter(models.Notification.user_id == user_id)
    if unread_only:
        q = q.filter(models.Notification.is_read == False)  # noqa: E712
    return q.order_by(models.Notification.created_at.desc()).limit(limit).all()

@router.post("/{notification_id}/read", response_model=NotificationOut)
def mark_read(
    notification_id: int,
    db: Session = Depends(get_db_with_schema),
):
    n = db.query(models.Notification).filter(models.Notification.id == notification_id).first()
    if not n:
        raise HTTPException(status_code=404, detail="Notification not found")
    n.is_read = True
    db.commit()
    db.refresh(n)
    return n
