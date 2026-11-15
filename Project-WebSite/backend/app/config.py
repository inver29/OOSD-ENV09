from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="APP_", env_file=ROOT / ".env", extra="ignore")

    db_server: str = r".\MSSQLSERVER08"
    db_name: str = "ENV09"
    db_driver: str = "ODBC Driver 17 for SQL Server"
    db_trusted: bool = True
    db_user: str = ""
    db_password: str = ""
    cookie_secure: bool = False
    session_hours: int = Field(default=8, ge=1, le=24)
    seed_demo: bool = False
    demo_password: str = ""
    otel_endpoint: str = ""
    log_level: str = "INFO"
    expiry_worker: bool = True
    storage_dir: Path = ROOT / "backend" / "storage" / "uploads"
    frontend_dir: Path = ROOT / "frontend" / "dist"
    max_upload_bytes: int = 8 * 1024 * 1024


settings = Settings()
