from app_v2.database import Base, engine
from app_v2 import models  # ✅ triggers model registration

def init_db():
    """
    Import all ORM models here, then create tables.
    Call this at app startup to ensure the DB and tables exist.
    """
    Base.metadata.create_all(bind=engine)