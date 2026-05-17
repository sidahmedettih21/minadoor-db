from functools import lru_cache
from typing import List
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    DATABASE_URL: str
    SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    REDIS_URL: str = "redis://redis:6379/0"
    CORS_ORIGINS: str = "http://localhost"
    UPLOAD_DIR: str = "./uploads"
    TEMP_EXPORT_DIR: str = "./exports"
    ADMIN_EMAIL: str = "admin@minadoor.com"
    ADMIN_PASSWORD: str = ""
    MAX_UPLOAD_MB: int = 10
    ENVIRONMENT: str = "production"

    @field_validator("SECRET_KEY")
    @classmethod
    def secret_key_strength(cls, v: str) -> str:
        if len(v) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters")
        return v

    @field_validator("JWT_ALGORITHM")
    @classmethod
    def algorithm_allowlist(cls, v: str) -> str:
        allowed = {"HS256", "HS384", "HS512", "RS256"}
        if v not in allowed:
            raise ValueError(f"JWT_ALGORITHM must be one of {allowed}")
        return v

    def cors_origins_list(self) -> List[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]


@lru_cache()
def get_settings() -> Settings:
    return Settings()
