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
    # LLM Provider — set to "gemini" to use Google Gemini API instead of local Ollama
    LLM_PROVIDER: str = "gemini"          # "ollama" | "gemini"
    GEMINI_API_KEY: Optional[str] = None   # Required when LLM_PROVIDER="gemini"
    GEMINI_MODEL: str = "gemini-2.5-flash"


    ALLOWED_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000,https://rail-vera.vercel.app"

    class Config:
        env_file = ".env"
        extra = "ignore"   # silently ignore unknown env vars

settings = Settings()
