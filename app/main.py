from fastapi import FastAPI
from sqlalchemy.orm import Session
from sqlalchemy import text
from prometheus_fastapi_instrumentator import Instrumentator

from app.routes import router as notifications_router
from app.database import engine, Base, get_db_session

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Notification Microservice", version="1.0.0")
app.include_router(notifications_router, prefix="/notifications")

Instrumentator().instrument(app).expose(app)

@app.get("/health")
def health_check():
    try:
        db: Session = get_db_session()
        db.execute(text("SELECT 1"))
        return {"status": "ok", "db": "ok"}
    except Exception as e:
        return {"status": "error", "db": "error", "detail": str(e)}
    finally:
        try:
            db.close()
        except Exception:
            pass

@app.get("/")
def read_root():
    return {"message": "Welcome to the Notification Microservice"}
