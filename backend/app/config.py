import os
from functools import lru_cache

class Settings:
    SECRET_KEY: str = os.environ["SECRET_KEY"]
    DATABASE_URL: str = os.environ["DATABASE_URL"]
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://redis:6379/0")
    CORS_ORIGINS: list = os.getenv("CORS_ORIGINS", "http://localhost").split(",")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 15))
    REFRESH_TOKEN_EXPIRE_DAYS: int = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", 7))
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "./uploads")
    TEMP_EXPORT_DIR: str = os.getenv("TEMP_EXPORT_DIR", "./exports")

@lru_cache()
def get_settings() -> Settings:
    return Settings()
