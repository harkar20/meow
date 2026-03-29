from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from .database import engine, Base
from .models import user, session  # noqa: F401 - ensure models are registered
from .routes.auth import router as auth_router
from .routes.session import router as session_router
from .config import settings

# Create all tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Meowmeow API",
    description="Intelligent Symptom Analysis & Risk Assessment Platform",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:5174", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/api")
app.include_router(session_router, prefix="/api")

@app.get("/")
def root():
    return {"status": "Meowmeow API running", "version": "1.0.0"}

@app.get("/health")
def health():
    return {"status": "healthy"}

@app.get("/health/db")
def health_db():
    # Why: quick Postman/browser check for PostgreSQL (or configured DB) connectivity.
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return {"status": "healthy", "database": "connected"}
    except SQLAlchemyError as exc:
        return {"status": "degraded", "database": "disconnected", "detail": str(exc)}
