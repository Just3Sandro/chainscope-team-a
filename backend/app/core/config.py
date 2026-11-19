from functools import lru_cache
from pathlib import Path
from typing import Literal
from urllib.parse import urlsplit

from pydantic import SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: Literal["dev", "test", "prod"] = "dev"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    database_url: SecretStr
    evidence_storage_dir: Path = Path("/var/lib/chainscope/evidences")
    cors_allowed_origins: str = ""
    smtp_host: str = "mailpit"
    smtp_port: int = 1025

    @field_validator("database_url")
    @classmethod
    def validate_database_url(cls, value: SecretStr) -> SecretStr:
        if not value.get_secret_value().startswith("postgresql+psycopg://"):
            raise ValueError("DATABASE_URL must use postgresql+psycopg")
        return value

    @field_validator("cors_allowed_origins")
    @classmethod
    def validate_origins(cls, value: str) -> str:
        for origin in filter(None, (item.strip() for item in value.split(","))):
            parsed = urlsplit(origin)
            if (
                "*" in origin
                or parsed.scheme not in {"http", "https"}
                or not parsed.netloc
                or parsed.username
                or parsed.password
                or parsed.path
                or parsed.query
                or parsed.fragment
            ):
                raise ValueError("CORS requires explicit HTTP(S) origins")
        return value

    @property
    def cors_origins(self) -> list[str]:
        return [
            item.strip()
            for item in self.cors_allowed_origins.split(",")
            if item.strip()
        ]


@lru_cache
def get_settings() -> Settings:
    return Settings()
