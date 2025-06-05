from pydantic import ConfigDict
from pydantic_settings import BaseSettings
from typing import Optional
import os

class Settings(BaseSettings):
    # ============ JWT Settings ============
    SECRET_KEY: str = "CHANGE_THIS_TO_A_RANDOM_STRING"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60  # 1 hour
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7  # 30 days

    # Using SQLite file-based DB in the project root.
    SQLALCHEMY_DATABASE_URL: str = "sqlite:///./users.db"


    OPENAI_API_KEY: str     = os.getenv("OPENAI_API_KEY")
    # QDRANT_URL: str       = os.getenv("QDRANT_URL")
    # QDRANT_API_KEY: str   = os.getenv("QDRANT_API_KEY")
    # BUCKET_NAME: str      = os.getenv("BUCKET_NAME", "smart-buildr-s3")
    
    AWS_ACCESS_KEY_ID: str       = os.getenv("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY: str   = os.getenv("AWS_SECRET_ACCESS_KEY")
    AWS_REGION: str              = os.getenv("AWS_REGION")
    S3_BUCKET_NAME : str         = os.getenv("S3_BUCKET_NAME")

    FAISS_BASE_PATH: str   = os.getenv("FAISS_BASE_PATH", "faiss_db")
    FAISS_PDF_PATH: str    = os.path.join(FAISS_BASE_PATH, "pdf_index")
    FAISS_CSV_PATH: str    = os.path.join(FAISS_BASE_PATH, "csv_index")
    
    # Vector store collection names
    PDF_COLLECTION: str   = "buildsmart-pdf-collection"
    CSV_COLLECTION: str   = "buildsmart-csv-collection"
    
    model_config = ConfigDict(
        extra="ignore",
        env_file=".env"  # Moved env_file here
    )


settings = Settings()