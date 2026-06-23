from typing import Optional
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str
    DATABASE_URL_SYNC: Optional[str] = None   # used by migrations.py only
    SECRET_KEY: str = "dev-secret-change-in-production"
    OLLAMA_URL: str = "http://localhost:11434"
    UPLOAD_DIR: str = "./uploads"
    REPORTS_DIR: str = "./reports"
    MAX_FILE_SIZE_MB: int = 20
    OCR_QUALITY_THRESHOLD: float = 0.70
    EMBEDDING_MODEL: str = "BAAI/bge-small-en-v1.5"
    RERANKER_MODEL: str = "BAAI/bge-reranker-base"
    LLM_MODEL: str = "qwen3"

    class Config:
        env_file = ".env"
        extra = "ignore"   # silently ignore unknown env vars

settings = Settings()
