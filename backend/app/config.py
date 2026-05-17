import os

# Secrets – no defaults, will crash if not set
SECRET_KEY = os.environ["SECRET_KEY"]
DATABASE_URL = os.environ["DATABASE_URL"]

# Redis
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")

# CORS – split by commas
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost").split(",")

# JWT
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 15))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", 7))

# Uploads
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "./uploads")
TEMP_EXPORT_DIR = os.getenv("TEMP_EXPORT_DIR", "./exports")
