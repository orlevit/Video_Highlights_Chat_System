import os
from typing import List

from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """Application settings."""
    
    # API settings
    API_PREFIX: str = "/api"
    
    # Database settings
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://user:password@db:5432/videohighlights")
    
    # CORS settings
    CORS_ORIGINS: List[str] = [
        "http://localhost:8501",  # Streamlit default port
        "http://frontend:8501",    # Docker container name
        "http://localhost:3000",   # Alternative frontend port
    ]
    
    # Security settings
    SECRET_KEY: str = os.getenv("SECRET_KEY", "super-secret-key-for-development-only")
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
