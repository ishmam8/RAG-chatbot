from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from .config import settings

# Create the SQLAlchemy engine (connect to SQLite)
engine = create_engine(
    settings.SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},  # needed only for SQLite
)

# SessionLocal is a factory for new Session objects
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

# Base class for ORM models
Base = declarative_base()


def init_db():
    """
    Import all ORM models here, then create tables.
    Call this at app startup to ensure the DB and tables exist.
    """
    import app_v2.models  # noqa: F401 (bring in all models)
    Base.metadata.create_all(bind=engine)