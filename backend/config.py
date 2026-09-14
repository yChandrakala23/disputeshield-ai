import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

class Settings:
    PROJECT_NAME: str = "DisputeShield AI"
    VERSION: str = "2.0.0"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    
    # API & Security
    API_KEY: str = os.getenv("API_KEY", "")  # Optional API key protection if set
    CORS_ORIGINS: list[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "https://disputeshield-ai.vercel.app",
        "https://disputeshield.vercel.app",
    ]
    
    # Database
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        f"sqlite:///{DATA_DIR / 'disputeshield.db'}"
    )
    
    # Model Artifact
    MODEL_PATH: Path = DATA_DIR / "model.joblib"
    METRICS_PATH: Path = DATA_DIR / "evaluation_metrics.json"
    AUDIT_LOG_PATH: Path = DATA_DIR / "audit_log.jsonl"
    
    # LLM Settings
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    GROQ_MODEL: str = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    LLM_TIMEOUT_SECONDS: float = 8.0
    
    # Policy Thresholds (Configurable)
    CONTEST_THRESHOLD: float = 0.65
    CONCEDE_THRESHOLD: float = 0.35
    FALSE_POSITIVE_COST_INR: float = 550.0

settings = Settings()
