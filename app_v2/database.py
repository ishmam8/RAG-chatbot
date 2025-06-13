from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from app_v2.config import settings

# Create the SQLAlchemy engine (connect to SQLite)
engine = create_engine(settings.SQLALCHEMY_DATABASE_URL)

# SessionLocal is a factory for new Session objects
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

# Base class for ORM models
Base = declarative_base()

