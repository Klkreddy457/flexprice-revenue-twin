import os
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "Flexprice Revenue Twin"
    API_V1_STR: str = "/api"
    
    # DB URL - check env or fallback to local SQLite
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./flexprice.db")
    
    # LLM Settings
    GEMINI_API_KEY: Optional[str] = os.getenv("GEMINI_API_KEY")
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    LLM_MODEL: str = os.getenv("LLM_MODEL", "gemini-1.5-flash")
    
    # Flexprice API Settings
    FLEXPRICE_API_KEY: Optional[str] = os.getenv("FLEXPRICE_API_KEY")
    FLEXPRICE_URL: str = os.getenv("FLEXPRICE_URL", "https://api.flexprice.io")

    class Config:
        case_sensitive = True

settings = Settings()
