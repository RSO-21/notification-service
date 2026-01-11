from typing import Optional
from fastapi import Depends, FastAPI, Header, status, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from prometheus_fastapi_instrumentator import Instrumentator

from app.routes import router as notifications_router
from app.database import engine, Base, get_db_session
from fastapi.middleware.cors import CORSMiddleware

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Notification Microservice", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:4200",  # Angular dev
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(notifications_router, prefix="/notifications")

Instrumentator().instrument(app).expose(app)

def get_tenant_id(x_tenant_id: Optional[str] = Header(None)) -> str:
    """Extract tenant ID from header, default to public"""
    return x_tenant_id or "public"

def get_db_with_schema(tenant_id: str = Depends(get_tenant_id)):
    with get_db_session(schema=tenant_id) as db:
        yield db

@app.get("/health", tags=["health"])
def health(db: Session = Depends(get_db_with_schema)):
    try:
        db.execute(text("SELECT 1"))
        return {"status": "ok", "db": "ok"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database unavailable: {e}",
        )

@app.get("/")
def read_root():
    return {"message": "Welcome to the Notification Microservice"}
