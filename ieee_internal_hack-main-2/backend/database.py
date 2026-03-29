from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from .config import settings

database_url = settings.DATABASE_URL
if database_url.startswith("postgres://"):
    # Why: SQLAlchemy expects postgresql:// while some platforms provide postgres://.
    database_url = database_url.replace("postgres://", "postgresql://", 1)

# SQLite needs connect_args for thread safety
connect_args = {}
if database_url.startswith("sqlite"):
    connect_args["check_same_thread"] = False

engine = create_engine(database_url, connect_args=connect_args, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
