import os
import sys
from unittest.mock import MagicMock

os.environ.setdefault("SECRET_KEY", "test-secret-key")
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
os.environ.setdefault("ENVIRONMENT", "test")

db_mock = MagicMock()
db_mock.AsyncSessionLocal = MagicMock()
db_mock.engine = MagicMock()
db_mock.get_db = MagicMock()
sys.modules["app.database"] = db_mock
