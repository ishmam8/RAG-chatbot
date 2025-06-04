from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # ============ JWT Settings ============
    SECRET_KEY: str = "CHANGE_THIS_TO_A_RANDOM_STRING"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60  # 1 hour
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7  # 30 days

    # ============ Database Settings ============
    # Using SQLite file-based DB in the project root.
    SQLALCHEMY_DATABASE_URL: str = "sqlite:///./users.db"

    # ============ External API Settings (Add these) ============
    QDRANT_API_KEY: Optional[str] = None # Or str if it's always required
    QDRANT_CLIENT_URL: Optional[str] = None # Or str if it's always required
    OPENAI_API_KEY: Optional[str] = None # Or str if it's always required

    # openai_api_key = Optional[str] = None


    class Config:
        env_file = ".env"  # you can override any of the above via a .env file


settings = Settings()