from pydantic import ConfigDict
from pydantic_settings import BaseSettings
from typing import Optional
import os

class Settings(BaseSettings):
    # ============ JWT Settings =========================
    SECRET_KEY: str = "CHANGE_THIS_TO_A_RANDOM_STRING"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60  # 1 hour
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7  # 30 days
    

    # ============ Database Settings =====================
    SQLALCHEMY_DATABASE_URL: str = "postgresql://postgres:password@localhost:5432/ragbotdb"


    # ============ LLM And VectorStore Settings ============
    OPENAI_API_KEY: str     = os.getenv("OPENAI_API_KEY")
    # QDRANT_URL: str       = os.getenv("QDRANT_URL")
    # QDRANT_API_KEY: str   = os.getenv("QDRANT_API_KEY")
    # BUCKET_NAME: str      = os.getenv("BUCKET_NAME", "smart-buildr-s3")
    FAISS_BASE_PATH: str   = os.getenv("FAISS_BASE_PATH", "faiss_db")
    FAISS_PDF_PATH: str    = os.path.join(FAISS_BASE_PATH, "pdf_index")
    FAISS_CSV_PATH: str    = os.path.join(FAISS_BASE_PATH, "csv_index")
    # Vector store collection names
    PDF_COLLECTION: str   = "buildsmart-pdf-collection"
    CSV_COLLECTION: str   = "buildsmart-csv-collection"


    # ============ AWS S3 Settings ==========================
    AWS_ACCESS_KEY_ID: str       = os.getenv("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY: str   = os.getenv("AWS_SECRET_ACCESS_KEY")
    AWS_REGION: str              = os.getenv("AWS_REGION")
    S3_BUCKET_NAME : str         = os.getenv("S3_BUCKET_NAME")


    # ============ Project MetaData Mapping ==================
    PROJECTS: dict = {
        "project_id_1": {
            "name": "Project One",
            "intro": "Location: 378 Stevens Drive"
        },
        "project_id_2": {
            "name": "Project Two",
            "intro": "Location: 10811 164th St Surrey"
        },
        "project_id_3": {
            "name": "Project Three",
            "intro": "Location: 9845 182a St"
        },
    }

    
    model_config = ConfigDict(
        extra="ignore",
        env_file=".env"
    )


settings = Settings()