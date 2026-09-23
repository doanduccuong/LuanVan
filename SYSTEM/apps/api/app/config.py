from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Touchpoint CRM API"
    app_env: str = "development"
    database_url: str = "sqlite:///./touchpoint_crm.db"
    jwt_signing_key: str = "development-only-change-me-32-bytes-minimum"
    access_token_ttl_seconds: int = 8 * 60 * 60
    cookie_secure: bool = False
    initial_user_email: str = "manager@example.com"
    initial_user_password: str = "demo1234"
    vision_base_url: str = "http://vision:8001"
    vision_request_timeout_seconds: float = 30.0
    max_upload_bytes: int = 8 * 1024 * 1024
    face_threshold_artifact_path: Path = Path("artifacts/face-threshold.json")
    visit_idle_timeout_seconds: int = 30 * 60
    late_event_tolerance_seconds: int = 5 * 60
    system_timezone: str = "Asia/Ho_Chi_Minh"


@lru_cache
def get_settings() -> Settings:
    return Settings()
