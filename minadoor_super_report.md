# MINADOOR TRAVEL DB – FULL STATE REPORT
Generated: Sun May 17 02:21:28 PM CET 2026

## 1. Project Structure
```
.
./backend
./backend/alembic
./backend/alembic/env.py
./backend/alembic.ini
./backend/alembic/__init__.py
./backend/alembic/__pycache__
./backend/alembic/script.py.mako
./backend/alembic/versions
./backend/alembic/versions/001_initial.py
./backend/alembic/versions/__pycache__
./backend/app
./backend/app/auth.py
./backend/app/config.py
./backend/app/database.py
./backend/app/dependencies.py
./backend/app/__init__.py
./backend/app/locales
./backend/app/locales/ar.json
./backend/app/locales/en.json
./backend/app/locales/fr.json
./backend/app/logger.py
./backend/app/main.py
./backend/app/middleware
./backend/app/middleware/__init__.py
./backend/app/middleware/request_id.py
./backend/app/middleware/upload.py
./backend/app/middleware/version.py
./backend/app/models.py
./backend/app/__pycache__
./backend/app/routers
./backend/app/routers/auth.py
./backend/app/routers/clients.py
./backend/app/routers/exports.py
./backend/app/routers/health.py
./backend/app/routers/__init__.py
./backend/app/routers/templates.py
./backend/app/routers/travel_types.py
./backend/app/routers/users.py
./backend/app/schemas.py
./backend/app/services
./backend/app/services/export_service.py
./backend/app/services/import_service.py
./backend/app/services/__init__.py
./backend/app/utils
./backend/app/utils/i18n.py
./backend/app/utils/__init__.py
./backend/app/utils/upload_validator.py
./backend/Dockerfile
./backend/entrypoint.sh
./backend/manage.py
./backend/requirements.txt
./backend/tests
./backend/tests/fixtures
./backend/tests/fixtures/valid_en.csv
./backend/tests/fixtures/valid_en.xlsx
./backend/tests/test_import.py
./docker
./docker-compose.yml
./docker/postgres
./docker/postgres/init.sql
./fix_all.sh
./frontend
./frontend/assets
./frontend/assets/logo.png
./frontend/css
./frontend/css/app.css
./frontend/index.html
./frontend/js
./frontend/js/app.js
./frontend/locales
./frontend/locales/ar.json
./frontend/locales/en.json
./frontend/locales/fr.json
./frontend/travel_types.html
./generate_super_report.sh
./minadoor-db-enhanced
./minadoor_super_report.md
./nginx
./nginx/nginx.conf
./old_version
./README.md
./scripts
./scripts/backup.sh
./test.csv
```

## 2. Docker Environment
### docker-compose.yml
```yaml
version: '3.8'

services:
  db:
    image: postgres:16
    environment:
      POSTGRES_USER: minadoor
      POSTGRES_PASSWORD: ${DB_PASS:-minadoor_secret}
      POSTGRES_DB: minadoordb
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./docker/postgres/init.sql:/docker-entrypoint-initdb.d/init.sql
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U minadoor"]
      interval: 5s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 3s
      retries: 5

  api:
    build: ./backend
    env_file:
      - .env
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
    volumes:
      - ./backend/app:/app/app
      - uploads:/app/uploads
      - exports:/app/exports
    ports:
      - "8000:8000"

  frontend:
    image: nginx:alpine
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/conf.d/default.conf
      - ./frontend:/usr/share/nginx/html
    ports:
      - "80:80"
    depends_on:
      - api

volumes:
  postgres_data:
  uploads:
  exports:
```

### .env (sanitised)
```
# Database
DATABASE_URL=***REDACTED***

# JWT
SECRET_KEY=***REDACTED***
JWT_ALGORITHM=***REDACTED***
ACCESS_TOKEN_EXPIRE_MINUTES=***REDACTED***
REFRESH_TOKEN_EXPIRE_DAYS=***REDACTED***

# Redis
REDIS_URL=***REDACTED***

# CORS (comma separated)
CORS_ORIGINS=***REDACTED***

# Uploads
UPLOAD_DIR=***REDACTED***
TEMP_EXPORT_DIR=***REDACTED***

# Admin
ADMIN_EMAIL=***REDACTED***
ADMIN_PASSWORD=***REDACTED***
DB_PASS=***REDACTED***
```

## 3. Backend Core Files
### main.py
```python
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.config import CORS_ORIGINS
from app.logger import logger
from app.middleware.upload import UploadValidationMiddleware
from app.middleware.version import VersionHeaderMiddleware
from app.routers import auth, clients, exports, health, templates, travel_types, users

app = FastAPI(title="MinaDoor Travel DB", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(UploadValidationMiddleware)
app.add_middleware(VersionHeaderMiddleware)

# Exception handlers for safe error responses
@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )

@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    return JSONResponse(
        status_code=400,
        content={"detail": str(exc)}
    )

# Include routers
app.include_router(auth.router)
app.include_router(clients.router)
app.include_router(exports.router)
app.include_router(health.router)
app.include_router(templates.router)
app.include_router(travel_types.router)
app.include_router(users.router)

@app.get("/")
async def root():
    return {"message": "MinaDoor Travel DB API v1"}

# For serving frontend static files (optional)
```

### config.py
```python
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
```

### database.py
```python
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.config import get_settings

settings = get_settings()

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=(settings.ENVIRONMENT == "development"),
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,        # detect stale connections
    pool_recycle=1800,         # recycle after 30 min
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
```

### models.py
```python
from sqlalchemy import Column, Integer, String, Date, Boolean, ForeignKey, Text, Index, TIMESTAMP, func, text
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    full_name = Column(String(100), nullable=False)
    role = Column(String(20), default="agent")
    preferred_lang = Column(String(5), default="en")
    is_active = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

class TravelType(Base):
    __tablename__ = "travel_types"
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(30), unique=True, nullable=False)
    name_en = Column(String(100), nullable=False)
    name_fr = Column(String(100), nullable=False)
    name_ar = Column(String(100), nullable=False)
    is_active = Column(Boolean, default=True)

class Client(Base):
    __tablename__ = "clients"
    id = Column(Integer, primary_key=True, index=True)
    created_by = Column(Integer, ForeignKey("users.id"))
    surname = Column(String(100), nullable=False)
    given_name = Column(String(100), nullable=False)
    father_name = Column(String(100), nullable=False)
    mother_name = Column(String(100))
    passport_number = Column(String(30), nullable=False)
    nationality = Column(String(50), nullable=False)
    date_of_birth = Column(Date)
    passport_issue_date = Column(Date)
    passport_expiry = Column(Date)
    gender = Column(String(1))
    travel_type_id = Column(Integer, ForeignKey("travel_types.id"), nullable=False)
    payment_method = Column(String(30), default="cash")
    travel_date = Column(Date, nullable=False)
    status = Column(String(20), default="active")
    notes = Column(Text)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())
    archived = Column(Boolean, default=False)

    creator = relationship("User")

    __table_args__ = (
        Index("idx_clients_passport", "passport_number", postgresql_where=text("NOT archived")),
        Index("idx_clients_names_trgm", "surname", "given_name", "father_name",
              postgresql_using="gin",
              postgresql_ops={
                  "surname": "gin_trgm_ops",
                  "given_name": "gin_trgm_ops",
                  "father_name": "gin_trgm_ops"
              }),
        Index("idx_clients_travel_type", "travel_type_id", postgresql_where=text("NOT archived")),
        Index("idx_clients_status", "status", postgresql_where=text("NOT archived")),
        Index("idx_clients_travel_date", "travel_date", postgresql_where=text("NOT archived")),
    )
```

### schemas.py
```python
from pydantic import BaseModel, validator, EmailStr
from typing import Optional, List
from datetime import date
import re

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    role: str = "agent"

    @validator("password")
    def password_strength(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        if not re.search(r"[A-Z]", v):
            raise ValueError("Must contain an uppercase letter")
        if not re.search(r"[a-z]", v):
            raise ValueError("Must contain a lowercase letter")
        if not re.search(r"\d", v):
            raise ValueError("Must contain a digit")
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", v):
            raise ValueError("Must contain a special character")
        return v

class ClientBase(BaseModel):
    surname: str
    given_name: str
    father_name: str
    mother_name: Optional[str] = None
    passport_number: str
    nationality: str
    date_of_birth: Optional[date] = None
    passport_issue_date: Optional[date] = None
    passport_expiry: Optional[date] = None
    gender: Optional[str] = None
    travel_type_id: int
    payment_method: str = "cash"
    travel_date: date
    notes: Optional[str] = None

    @validator("gender")
    def validate_gender(cls, v):
        if v and v.upper() not in ("M", "F"):
            raise ValueError("Gender must be M or F")
        return v.upper() if v else v

    @validator("passport_expiry")
    def expiry_after_issue(cls, v, values):
        if v and values.get("passport_issue_date") and v < values["passport_issue_date"]:
            raise ValueError("Expiry must be after issue date")
        return v

    @validator("travel_date")
    def travel_not_past(cls, v):
        if v < date.today():
            raise ValueError("Travel date cannot be in the past")
        return v

class ClientCreate(ClientBase):
    pass

class ClientUpdate(BaseModel):
    surname: Optional[str] = None
    given_name: Optional[str] = None
    father_name: Optional[str] = None
    mother_name: Optional[str] = None
    passport_number: Optional[str] = None
    nationality: Optional[str] = None
    date_of_birth: Optional[date] = None
    passport_issue_date: Optional[date] = None
    passport_expiry: Optional[date] = None
    gender: Optional[str] = None
    travel_type_id: Optional[int] = None
    payment_method: Optional[str] = None
    travel_date: Optional[date] = None
    status: Optional[str] = None
    notes: Optional[str] = None

class ClientResponse(ClientBase):
    id: int
    created_at: date
    updated_at: date
    created_by: Optional[int] = None
    archived: bool

    class Config:
        orm_mode = True

class TravelTypeCreate(BaseModel):
    code: str
    name_en: str
    name_fr: str
    name_ar: str

class TravelTypeResponse(TravelTypeCreate):
    id: int
    is_active: bool

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class UserResponse(BaseModel):
    id: int
    email: str
    full_name: str
    role: str
    preferred_lang: str
    is_active: bool

class ImportPreview(BaseModel):
    validation_id: str
    total_rows: int
    valid_rows: int
    errors: List[dict]
```

### auth.py
```python
from datetime import datetime, timedelta
from jose import jwt
import uuid
from app.config import SECRET_KEY, JWT_ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES, REFRESH_TOKEN_EXPIRE_DAYS
from app.dependencies import redis_client

def create_tokens(user_id: int) -> tuple:
    now = datetime.utcnow()
    access_exp = now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    refresh_exp = now + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    jti = str(uuid.uuid4())
    access_payload = {
        "sub": user_id,
        "exp": access_exp,
        "type": "access"
    }
    refresh_payload = {
        "sub": user_id,
        "exp": refresh_exp,
        "type": "refresh",
        "jti": jti
    }
    access_token = jwt.encode(access_payload, SECRET_KEY, algorithm=JWT_ALGORITHM)
    refresh_token = jwt.encode(refresh_payload, SECRET_KEY, algorithm=JWT_ALGORITHM)
    return access_token, refresh_token

def decode_token(token: str) -> dict:
    return jwt.decode(token, SECRET_KEY, algorithms=[JWT_ALGORITHM])

async def rotate_refresh_token(old_refresh_token: str, user_id: int) -> str:
    """Invalidate old refresh token and return new access + refresh"""
    payload = decode_token(old_refresh_token)
    jti = payload.get("jti")
    exp = payload.get("exp")
    # Add old token to blocklist until its original expiry
    ttl = max(0, int(exp - datetime.utcnow().timestamp()))
    if ttl > 0:
        await redis_client.setex(f"bl:{jti}", ttl, "revoked")
    # Create new pair
    access_token, new_refresh_token = create_tokens(user_id)
    return access_token, new_refresh_token

def get_password_hash(password: str) -> str:
    from passlib.context import CryptContext
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    from passlib.context import CryptContext
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    return pwd_context.verify(plain_password, hashed_password)
```

### dependencies.py
```python
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from app.config import SECRET_KEY, JWT_ALGORITHM
from app.database import get_db
from app.models import User
from sqlalchemy.ext.asyncio import AsyncSession
from functools import wraps
import redis.asyncio as redis
import os
from datetime import datetime

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")
redis_client = redis.from_url(os.getenv("REDIS_URL", "redis://redis:6379/0"), decode_responses=True)

def rate_limit(max_requests: int, window: int):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            request: Request = kwargs.get("request")
            if not request:
                raise HTTPException(status_code=500, detail="No request object")
            client_ip = request.client.host
            key = f"ratelimit:{client_ip}:{func.__name__}"
            current = await redis_client.get(key)
            if current and int(current) >= max_requests:
                raise HTTPException(status_code=429, detail="Too many requests")
            pipe = redis_client.pipeline()
            pipe.incr(key)
            pipe.expire(key, window)
            await pipe.execute()
            return await func(*args, **kwargs)
        return wrapper
    return decorator

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[JWT_ALGORITHM])
        user_id: int = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = await db.get(User, user_id)
    if user is None or not user.is_active:
        raise credentials_exception
    return user

async def get_current_active_user(
    current_user: User = Depends(get_current_user),
):
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

async def get_admin_user(
    current_user: User = Depends(get_current_active_user),
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not enough permissions")
    return current_user

async def get_refresh_token_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
):
    """Validate refresh token, check blocklist, return user."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[JWT_ALGORITHM])
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid token type")
        jti = payload.get("jti")
        if not jti:
            raise HTTPException(status_code=401, detail="Missing JTI")
        # Check Redis blocklist
        if await redis_client.exists(f"bl:{jti}"):
            raise HTTPException(status_code=401, detail="Token revoked")
        user_id: int = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401)
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    user = await db.get(User, user_id)
    if user is None or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found")
    return user
```

## 4. Routers
### auth.py
```python
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models import User
from app.schemas import Token
from app.auth import create_tokens, rotate_refresh_token, verify_password
from app.dependencies import get_refresh_token_user, rate_limit

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])

@router.post("/login", response_model=Token)
@rate_limit(max_requests=5, window=60)
async def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    user = await db.get(User, form_data.username)  # username = email
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user")
    access, refresh = create_tokens(user.id)
    return {"access_token": access, "refresh_token": refresh}

@router.post("/refresh", response_model=Token)
@rate_limit(max_requests=10, window=60)
async def refresh_token(
    request: Request,
    current_user: User = Depends(get_refresh_token_user),
    token: str = Depends(OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login"))  # we need the raw token
):
    # get_refresh_token_user already validated token & blocklist
    # token is passed via dependency, but we need the raw string; use Depends as above
    access, new_refresh = await rotate_refresh_token(token, current_user.id)
    return {"access_token": access, "refresh_token": new_refresh}

@router.post("/logout")
async def logout(
    current_user: User = Depends(get_refresh_token_user),
    token: str = Depends(OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login"))
):
    # We'll invalidate refresh token by adding to blocklist
    await rotate_refresh_token(token, current_user.id)  # just call rotation to blacklist
    return {"detail": "Logged out"}
```

### clients.py
```python
import math
import uuid
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, BackgroundTasks
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models import Client, TravelType
from app.schemas import ClientCreate, ClientUpdate, ClientResponse, PaginatedClients, ExportRequest, ImportPreview
from app.dependencies import get_current_active_user, redis_client
from app.utils.upload_validator import validate_import_file
from app.services import import_service, export_service

import json

router = APIRouter(prefix="/api/v1/clients", tags=["clients"])

SORTABLE_COLS = {"surname", "given_name", "travel_date", "created_at", "status"}


@router.get("/", response_model=PaginatedClients)
async def list_clients(
    search: Optional[str] = Query(None, max_length=100),
    travel_type: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    gender: Optional[str] = Query(None),
    travel_date_from: Optional[str] = Query(None),
    travel_date_to: Optional[str] = Query(None),
    sort: Optional[str] = Query("-travel_date"),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    base_q = select(Client).where(Client.archived == False).options(
        selectinload(Client.travel_type)
    )

    if search:
        # Fixed: or_() instead of | operator; similarity via pg_trgm
        base_q = base_q.where(
            or_(
                func.similarity(Client.surname, search) > 0.3,
                func.similarity(Client.given_name, search) > 0.3,
                func.similarity(Client.father_name, search) > 0.3,
                Client.passport_number.ilike(f"%{search}%"),
            )
        )

    if travel_type:
        # Fixed: use JOIN instead of non-existent .has()
        base_q = base_q.join(TravelType, Client.travel_type_id == TravelType.id).where(
            TravelType.code == travel_type
        )

    if status:
        base_q = base_q.where(Client.status == status)

    if gender:
        base_q = base_q.where(Client.gender == gender.upper())

    if travel_date_from:
        base_q = base_q.where(Client.travel_date >= travel_date_from)

    if travel_date_to:
        base_q = base_q.where(Client.travel_date <= travel_date_to)

    # Count total for pagination
    count_q = select(func.count()).select_from(base_q.subquery())
    total = (await db.execute(count_q)).scalar_one()

    # Sorting
    col_name = sort.lstrip("-") if sort else "travel_date"
    if col_name not in SORTABLE_COLS:
        col_name = "travel_date"
    col = getattr(Client, col_name)
    order = col.desc() if (sort or "").startswith("-") else col.asc()
    base_q = base_q.order_by(order)

    # Pagination
    base_q = base_q.offset((page - 1) * limit).limit(limit)
    clients = (await db.execute(base_q)).scalars().all()

    return PaginatedClients(
        total=total,
        page=page,
        limit=limit,
        pages=math.ceil(total / limit) if total else 0,
        items=clients,
    )


@router.post("/", response_model=ClientResponse, status_code=201)
async def create_client(
    client: ClientCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    # Check duplicate passport for non-archived clients
    existing = await db.execute(
        select(Client).where(
            Client.passport_number == client.passport_number,
            Client.archived == False,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Client with this passport already exists")

    db_client = Client(**client.model_dump(), created_by=current_user.id)
    db.add(db_client)
    await db.commit()
    await db.refresh(db_client)
    return db_client


@router.get("/{client_id}", response_model=ClientResponse)
async def get_client(
    client_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    result = await db.execute(
        select(Client)
        .where(Client.id == client_id, Client.archived == False)
        .options(selectinload(Client.travel_type))
    )
    client = result.scalar_one_or_none()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    return client


@router.patch("/{client_id}", response_model=ClientResponse)
async def update_client(
    client_id: int,
    client_update: ClientUpdate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    result = await db.execute(
        select(Client).where(Client.id == client_id, Client.archived == False)
    )
    client = result.scalar_one_or_none()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    for field, value in client_update.model_dump(exclude_unset=True).items():
        setattr(client, field, value)
    await db.commit()
    await db.refresh(client)
    return client


@router.delete("/{client_id}", status_code=204)
async def delete_client(
    client_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    result = await db.execute(
        select(Client).where(Client.id == client_id, Client.archived == False)
    )
    client = result.scalar_one_or_none()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    client.archived = True
    await db.commit()


@router.post("/import/preview", response_model=ImportPreview)
async def import_preview(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    await validate_import_file(file)
    content = await file.read()
    return await import_service.parse_and_validate(content, file.filename)


@router.post("/import/confirm")
async def import_confirm(
    validation_id: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    cached = await redis_client.get(f"import:{validation_id}")
    if not cached:
        raise HTTPException(status_code=404, detail="Validation session expired or not found")
    data = json.loads(cached)
    return await import_service.commit_import(validation_id, data.get("rows", []))


@router.post("/export")
async def export_request(
    body: ExportRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    job_id = str(uuid.uuid4())
    await redis_client.setex(
        f"export:{job_id}",
        3600,
        json.dumps({"status": "pending"}),
    )
    background_tasks.add_task(
        export_service.create_export_job,
        job_id,
        body.model_dump(),
        current_user.id,
    )
    return {"job_id": job_id}
```

### exports.py
```python
import json
import os
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from app.dependencies import get_current_active_user, redis_client
from app.schemas import ExportStatus

router = APIRouter(prefix="/api/v1/exports", tags=["exports"])


@router.get("/{job_id}/status", response_model=ExportStatus)
async def export_status(
    job_id: str,
    current_user=Depends(get_current_active_user),
):
    # Actually read from Redis (was always returning "completed" before)
    raw = await redis_client.get(f"export:{job_id}")
    if not raw:
        raise HTTPException(status_code=404, detail="Export job not found")
    data = json.loads(raw)
    return ExportStatus(
        job_id=job_id,
        status=data.get("status", "unknown"),
        error=data.get("error"),
        download_url=f"/api/v1/exports/{job_id}/download" if data.get("status") == "completed" else None,
    )


@router.get("/{job_id}/download")
async def export_download(
    job_id: str,
    current_user=Depends(get_current_active_user),
):
    raw = await redis_client.get(f"export:{job_id}")
    if not raw:
        raise HTTPException(status_code=404, detail="Export job not found")
    data = json.loads(raw)
    if data.get("status") != "completed":
        raise HTTPException(status_code=425, detail=f"Export not ready: {data.get('status')}")
    filepath = data.get("filepath", "")
    if not filepath or not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="Export file not found on disk")
    fmt = data.get("format", "xlsx")
    media_types = {
        "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "csv": "text/csv",
        "pdf": "application/pdf",
    }
    return FileResponse(
        path=filepath,
        media_type=media_types.get(fmt, "application/octet-stream"),
        filename=f"clients_export.{fmt}",
    )
```

### health.py
```python
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.database import get_db
from app.dependencies import redis_client

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/")
async def health_check(db: AsyncSession = Depends(get_db)):
    """Deep health check: DB + Redis connectivity."""
    db_ok = False
    redis_ok = False
    try:
        await db.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        pass
    try:
        await redis_client.ping()
        redis_ok = True
    except Exception:
        pass

    status = "ok" if (db_ok and redis_ok) else "degraded"
    return {
        "status": status,
        "db": "ok" if db_ok else "error",
        "redis": "ok" if redis_ok else "error",
    }
```

### __init__.py
```python
from . import auth, clients, exports, health, templates, travel_types, users
```

### templates.py
```python
from fastapi import APIRouter, Query
from fastapi.responses import FileResponse
import os

router = APIRouter(prefix="/api/v1/templates", tags=["templates"])

@router.get("/{lang}")
async def download_template(lang: str = "en"):
    return {"message": f"Template for {lang}"}
```

### travel_types.py
```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from app.database import get_db
from app.models import TravelType
from app.schemas import TravelTypeCreate, TravelTypeResponse
from app.dependencies import get_current_active_user, get_admin_user

router = APIRouter(prefix="/api/v1/travel-types", tags=["travel_types"])

@router.get("/", response_model=List[TravelTypeResponse])
async def list_travel_types(db: AsyncSession = Depends(get_db), current_user = Depends(get_current_active_user)):
    result = await db.execute(select(TravelType).where(TravelType.is_active == True))
    return result.scalars().all()

@router.post("/", response_model=TravelTypeResponse, status_code=201)
async def create_travel_type(
    travel_type: TravelTypeCreate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_admin_user)
):
    db_type = TravelType(**travel_type.dict())
    db.add(db_type)
    await db.commit()
    await db.refresh(db_type)
    return db_type

@router.delete("/{type_id}", status_code=204)
async def delete_travel_type(
    type_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_admin_user)
):
    result = await db.execute(select(TravelType).where(TravelType.id == type_id))
    travel_type = result.scalar_one_or_none()
    if not travel_type:
        raise HTTPException(status_code=404, detail="Travel type not found")
    travel_type.is_active = False
    await db.commit()
    return
```

### users.py
```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from app.database import get_db
from app.models import User
from app.schemas import UserCreate, UserResponse
from app.dependencies import get_current_active_user, get_admin_user
from app.auth import get_password_hash

router = APIRouter(prefix="/api/v1/users", tags=["users"])

@router.get("/", response_model=List[UserResponse])
async def list_users(db: AsyncSession = Depends(get_db), current_user = Depends(get_admin_user)):
    result = await db.execute(select(User).where(User.is_active == True))
    return result.scalars().all()

@router.post("/", response_model=UserResponse, status_code=201)
async def create_user(
    user: UserCreate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_admin_user)
):
    existing = await db.execute(select(User).where(User.email == user.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")
    db_user = User(
        email=user.email,
        password_hash=get_password_hash(user.password),
        full_name=user.full_name,
        role=user.role
    )
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user
```

## 5. Services & Utils
### export_service.py
```python
import os
import csv
import json
from datetime import datetime
from typing import Dict, Any
from sqlalchemy import select, or_
from sqlalchemy.orm import selectinload
from openpyxl import Workbook
from app.database import AsyncSessionLocal
from app.models import Client, TravelType
from app.dependencies import redis_client
from app.config import get_settings

settings = get_settings()

HEADERS_I18N = {
    "en": ["Surname", "Given Name", "Father Name", "Mother Name", "Passport", "Nationality",
           "Travel Type", "Travel Date", "Status", "Gender", "Payment", "Notes"],
    "fr": ["Nom", "Prénom", "Nom du père", "Nom de la mère", "Passeport", "Nationalité",
           "Type de voyage", "Date de voyage", "Statut", "Genre", "Paiement", "Remarques"],
    "ar": ["اللقب", "الاسم", "اسم الأب", "اسم الأم", "جواز السفر", "الجنسية",
           "نوع السفر", "تاريخ السفر", "الحالة", "الجنس", "الدفع", "ملاحظات"],
}


async def create_export_job(job_id: str, filters: Dict[str, Any], user_id: int):
    try:
        async with AsyncSessionLocal() as db:
            q = select(Client).where(Client.archived == False).options(
                selectinload(Client.travel_type)
            )
            if filters.get("search"):
                term = f"%{filters['search']}%"
                q = q.where(or_(
                    Client.surname.ilike(term),
                    Client.given_name.ilike(term),
                    Client.father_name.ilike(term),
                    Client.passport_number.ilike(term),
                ))
            if filters.get("travel_type"):
                q = q.join(TravelType, Client.travel_type_id == TravelType.id).where(
                    TravelType.code == filters["travel_type"]
                )
            if filters.get("status"):
                q = q.where(Client.status == filters["status"])
            if filters.get("gender"):
                q = q.where(Client.gender == filters["gender"])
            if filters.get("travel_date_from"):
                q = q.where(Client.travel_date >= filters["travel_date_from"])
            if filters.get("travel_date_to"):
                q = q.where(Client.travel_date <= filters["travel_date_to"])

            items = (await db.execute(q)).scalars().all()

        lang = filters.get("header_lang", "en")
        fmt = filters.get("format", "xlsx")
        os.makedirs(settings.TEMP_EXPORT_DIR, exist_ok=True)
        filepath = os.path.join(settings.TEMP_EXPORT_DIR, f"{job_id}.{fmt}")
        headers = HEADERS_I18N.get(lang, HEADERS_I18N["en"])

        def row_data(c):
            tt_attr = f"name_{lang}"
            tt = getattr(c.travel_type, tt_attr, None) or (c.travel_type.name_en if c.travel_type else "")
            return [
                c.surname, c.given_name, c.father_name, c.mother_name or "",
                c.passport_number, c.nationality, tt,
                c.travel_date.isoformat() if c.travel_date else "",
                c.status, c.gender or "", c.payment_method, c.notes or "",
            ]

        if fmt == "csv":
            with open(filepath, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f)
                writer.writerow(headers)
                for c in items:
                    writer.writerow(row_data(c))

        elif fmt == "xlsx":
            wb = Workbook()
            ws = wb.active
            ws.title = "Clients"
            ws.append(headers)
            for c in items:
                ws.append(row_data(c))
            wb.save(filepath)

        elif fmt == "pdf":
            from weasyprint import HTML
            title = {"en": "Client List", "fr": "Liste des clients", "ar": "قائمة العملاء"}.get(lang, "Client List")
            rtl = lang == "ar"
            rows_html = "".join(
                f"<tr>{''.join(f'<td>{v}</td>' for v in row_data(c)[:9])}</tr>"
                for c in items
            )
            html = f"""<!DOCTYPE html>
<html dir="{'rtl' if rtl else 'ltr'}">
<head><meta charset="utf-8">
<style>
body{{font-family:sans-serif;margin:40px}}
h1{{color:#1e40af}}
table{{width:100%;border-collapse:collapse;margin-top:20px}}
th{{background:#1e40af;color:white;padding:8px;text-align:{'right' if rtl else 'left'}}}
td{{border:1px solid #ddd;padding:6px}}
tr:nth-child(even){{background:#f8fafc}}
.footer{{margin-top:20px;font-size:10px;color:#666;text-align:center}}
</style></head>
<body>
<h1>MinaDoor – {title}</h1>
<table>
<tr>{''.join(f'<th>{h}</th>' for h in headers[:9])}</tr>
{rows_html}
</table>
<div class="footer">Generated {datetime.now().strftime('%Y-%m-%d %H:%M')}</div>
</body></html>"""
            HTML(string=html).write_pdf(filepath)

        # Fixed: await async Redis call
        await redis_client.setex(
            f"export:{job_id}",
            3600,
            json.dumps({"status": "completed", "filepath": filepath, "format": fmt}),
        )

    except Exception as exc:
        # Fixed: await async Redis call
        await redis_client.setex(
            f"export:{job_id}",
            3600,
            json.dumps({"status": "failed", "error": str(exc)}),
        )
```

### import_service.py
```python
from sqlalchemy import select
from app.database import async_session
from app.models import Client
from app.schemas import ClientCreate
from typing import List, Tuple
import uuid

async def parse_and_validate(file_content: bytes, filename: str) -> dict:
    # placeholder – actual import logic here
    # Returns validation_id, rows, errors
    return {
        "validation_id": str(uuid.uuid4()),
        "total_rows": 0,
        "valid_rows": 0,
        "errors": []
    }

async def commit_import(validation_id: str, rows: List[ClientCreate]) -> dict:
    # Insert into DB, skip duplicates by passport_number
    async with async_session() as session:
        existing_passports = set(
            (await session.execute(
                select(Client.passport_number).where(Client.passport_number.in_([r.passport_number for r in rows]))
            )).scalars().all()
        )
        new_clients = []
        skipped = 0
        for row in rows:
            if row.passport_number in existing_passports:
                skipped += 1
                continue
            client = Client(**row.dict())
            session.add(client)
            new_clients.append(client)
        await session.commit()
        return {"imported": len(new_clients), "skipped": skipped}
```

### __init__.py
```python
```

### i18n.py
```python
import json
from pathlib import Path
from fastapi import Request

locales = {}
locales_dir = Path(__file__).parent.parent / "locales"
for lang in ("en", "fr", "ar"):
    with open(locales_dir / f"{lang}.json", encoding="utf-8") as f:
        locales[lang] = json.load(f)

def get_translated_error(request: Request, key: str, **kwargs) -> str:
    lang = request.headers.get("accept-language", "en")[:2]
    if lang not in locales:
        lang = "en"
    template = locales[lang].get(key, key)
    return template.format(**kwargs) if kwargs else template
```

### __init__.py
```python
```

### upload_validator.py
```python
from fastapi import UploadFile, HTTPException

ALLOWED_CONTENT_TYPES = [
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "text/csv"
]

async def validate_import_file(file: UploadFile):
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(status_code=400, detail="Invalid file type. Use .xlsx or .csv")
    # Check magic bytes
    header = await file.read(4)
    await file.seek(0)
    if file.filename.endswith('.xlsx') and header[:2] != b'PK':
        raise HTTPException(status_code=400, detail="Corrupted file")
    # Max size 10MB
    if file.size and file.size > 10 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="File too large (max 10 MB)")
```

## 6. Migration
### alembic/versions/001_initial.py
```python
"""Initial migration

Revision ID: 001
Revises: None
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")

    op.create_table(
        'users',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('full_name', sa.String(100), nullable=False),
        sa.Column('role', sa.String(20), nullable=False, server_default='agent'),
        sa.Column('preferred_lang', sa.String(5), nullable=True, server_default='en'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email'),
    )
    op.create_index('ix_users_email', 'users', ['email'])

    op.create_table(
        'travel_types',
        sa.Column('id', sa.SmallInteger(), autoincrement=True, nullable=False),
        sa.Column('code', sa.String(30), nullable=False),
        sa.Column('name_en', sa.String(100), nullable=False),
        sa.Column('name_fr', sa.String(100), nullable=False),
        sa.Column('name_ar', sa.String(100), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('code'),
    )

    op.create_table(
        'clients',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('created_by', sa.BigInteger(), nullable=True),
        sa.Column('surname', sa.String(100), nullable=False),
        sa.Column('given_name', sa.String(100), nullable=False),
        sa.Column('father_name', sa.String(100), nullable=False),
        sa.Column('mother_name', sa.String(100), nullable=True),
        sa.Column('passport_number', sa.String(30), nullable=False),
        sa.Column('nationality', sa.String(50), nullable=False),
        sa.Column('date_of_birth', sa.Date(), nullable=True),
        sa.Column('passport_issue_date', sa.Date(), nullable=True),
        sa.Column('passport_expiry', sa.Date(), nullable=True),
        sa.Column('gender', sa.CHAR(1), nullable=True),
        sa.Column('travel_type_id', sa.SmallInteger(), nullable=False),
        sa.Column('payment_method', sa.String(30), nullable=True, server_default='cash'),
        sa.Column('travel_date', sa.Date(), nullable=False),
        sa.Column('status', sa.String(20), nullable=False, server_default='active'),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('archived', sa.Boolean(), nullable=False, server_default='false'),
        sa.CheckConstraint("gender IN ('M','F')", name='check_gender'),
        sa.CheckConstraint("status IN ('active','completed','cancelled','pending')", name='check_status'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['travel_type_id'], ['travel_types.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id'),
    )

    # DB-level updated_at trigger (not relying on SQLAlchemy onupdate)
    op.execute("""
        CREATE OR REPLACE FUNCTION update_updated_at()
        RETURNS TRIGGER AS $$
        BEGIN NEW.updated_at = NOW(); RETURN NEW; END;
        $$ LANGUAGE plpgsql;
    """)
    op.execute("""
        CREATE TRIGGER trg_clients_updated_at
        BEFORE UPDATE ON clients
        FOR EACH ROW EXECUTE FUNCTION update_updated_at();
    """)

    # Indexes
    op.create_index('idx_clients_names', 'clients', ['surname', 'given_name', 'father_name'],
                    postgresql_using='gin',
                    postgresql_ops={
                        'surname': 'gin_trgm_ops',
                        'given_name': 'gin_trgm_ops',
                        'father_name': 'gin_trgm_ops',
                    })
    op.create_index('idx_clients_passport', 'clients', ['passport_number'],
                    postgresql_where=sa.text('NOT archived'))
    op.create_index('idx_clients_status', 'clients', ['status'],
                    postgresql_where=sa.text('NOT archived'))
    op.create_index('idx_clients_travel_date', 'clients', ['travel_date'],
                    postgresql_where=sa.text('NOT archived'))
    op.create_index('idx_clients_travel_type', 'clients', ['travel_type_id'],
                    postgresql_where=sa.text('NOT archived'))

    op.create_table(
        'audit_log',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.BigInteger(), nullable=True),
        sa.Column('action', sa.String(20), nullable=True),
        sa.Column('table_name', sa.String(50), nullable=True),
        sa.Column('record_id', sa.BigInteger(), nullable=True),
        sa.Column('old_data', postgresql.JSONB(), nullable=True),
        sa.Column('new_data', postgresql.JSONB(), nullable=True),
        sa.Column('changed_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )

    # Fixed: use op.execute instead of broken op.bulk_insert with string table name
    op.execute("""
        INSERT INTO travel_types (code, name_en, name_fr, name_ar) VALUES
        ('cash_umrah',       'Cash Umrah',         'Omra au comptant',       'عمرة نقدًا'),
        ('cash_hajj',        'Cash Hajj',          'Hajj au comptant',       'حج نقدًا'),
        ('instalment_umrah', 'Instalment Umrah',   'Omra à tempérament',     'عمرة بالتقسيط'),
        ('instalment_hajj',  'Instalment Hajj',    'Hajj à tempérament',     'حج بالتقسيط'),
        ('organised_travel', 'Organised Travel',   'Voyage organisé',        'سفر منظم')
    """)

    # Seed admin user – password is CHANGE_ME (hash: bcrypt of "CHANGE_ME_ADMIN_PASSWORD")
    # NOTE: manage.py handles real admin seeding from ADMIN_PASSWORD env var.
    # This hash is a placeholder; manage.py must be run post-deploy to set a real password.
    op.execute("""
        INSERT INTO users (email, password_hash, full_name, role, preferred_lang, is_active)
        VALUES ('admin@minadoor.com', '$2b$12$placeholder_run_manage_py', 'Admin User', 'admin', 'en', true)
        ON CONFLICT (email) DO NOTHING
    """)


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS trg_clients_updated_at ON clients")
    op.execute("DROP FUNCTION IF EXISTS update_updated_at")
    op.drop_table('audit_log')
    op.drop_index('idx_clients_travel_type', table_name='clients')
    op.drop_index('idx_clients_travel_date', table_name='clients')
    op.drop_index('idx_clients_status', table_name='clients')
    op.drop_index('idx_clients_passport', table_name='clients')
    op.drop_index('idx_clients_names', table_name='clients')
    op.drop_table('clients')
    op.drop_table('travel_types')
    op.drop_index('ix_users_email', table_name='users')
    op.drop_table('users')
```

## 7. Frontend
### index.html
```html
<!DOCTYPE html>
<html x-data="app()" x-init="initApp()" :dir="lang === 'ar' ? 'rtl' : 'ltr'" :lang="lang">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title x-text="t('app_name')">MinaDoor Travel DB</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <script defer src="https://cdn.jsdelivr.net/npm/alpinejs@3.13.3/dist/cdn.min.js"></script>
  <script src="https://unpkg.com/htmx.org@1.9.10"></script>
  <link rel="stylesheet" href="/css/app.css">
  <script>
    tailwind.config = {
      theme: {
        extend: {
          colors: {
            primary: '#1e40af',
            secondary: '#f59e0b',
            surface: '#ffffff',
            bg: '#f8fafc',
          }
        }
      }
    }
  </script>
<script src="https://cdn.jsdelivr.net/npm/dompurify@3.0.6/dist/purify.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/dompurify@3.0.6/dist/purify.min.js"></script>
</head>
<body class="min-h-screen bg-bg">
  <!-- Toast Container -->
  <div class="toast-container" x-show="toasts.length > 0" style="display:none;">
    <template x-for="toast in toasts" :key="toast.id">
      <div class="toast" :class="toast.type" x-text="toast.message"></div>
    </template>
  </div>

  <!-- LOGIN VIEW -->
  <div x-show="!isLoggedIn" class="min-h-screen flex items-center justify-center p-4" style="display:none;">
    <div class="w-full max-w-md">
      <div class="text-center mb-8">
        <img src="/assets/logo.png" alt="MinaDoor" class="logo-img mx-auto mb-4">
        <h1 class="text-2xl font-bold text-primary" x-text="t('app_name')"></h1>
      </div>
      <div class="bg-surface rounded-2xl shadow-lg p-8 border border-gray-100">
        <h2 class="text-xl font-semibold mb-6 text-center" x-text="t('login')"></h2>
        <form @submit.prevent="doLogin()">
          <div class="mb-4">
            <label class="block text-sm font-medium mb-1 text-gray-700" x-text="t('email')"></label>
            <input type="email" x-model="loginForm.email" class="form-input" required>
          </div>
          <div class="mb-6">
            <label class="block text-sm font-medium mb-1 text-gray-700" x-text="t('password')"></label>
            <input type="password" x-model="loginForm.password" class="form-input" required>
          </div>
          <button type="submit" class="btn btn-primary w-full justify-center py-2.5" :disabled="loading">
            <span x-show="!loading" x-text="t('sign_in')"></span>
            <span x-show="loading">...</span>
          </button>
        </form>
        <div x-show="loginError" class="mt-4 p-3 bg-red-50 text-red-600 rounded-lg text-sm" x-text="loginError"></div>
      </div>
      <div class="text-center mt-6">
        <div class="flex justify-center gap-2">
          <button @click="setLang('en')" class="lang-btn" :class="{'active': lang==='en'}">EN</button>
          <button @click="setLang('fr')" class="lang-btn" :class="{'active': lang==='fr'}">FR</button>
          <button @click="setLang('ar')" class="lang-btn" :class="{'active': lang==='ar'}">AR</button>
        </div>
      </div>
    </div>
  </div>

  <!-- MAIN APP -->
  <div x-show="isLoggedIn" class="flex min-h-screen" style="display:none;">
    <!-- Sidebar -->
    <aside class="w-64 bg-surface border-r border-gray-200 flex flex-col fixed h-full z-40 transition-transform"
           :class="mobileMenuOpen ? 'translate-x-0' : 'translate-x-0' : '-translate-x-full'"
           class="lg:translate-x-0 lg:static">
      <div class="p-6 border-b border-gray-100">
        <img src="/assets/logo.png" alt="MinaDoor" class="logo-img">
      </div>
      <nav class="flex-1 p-4 space-y-1">
        <a href="#dashboard" @click.prevent="navigate('dashboard')"
           class="flex items-center gap-3 px-4 py-2.5 rounded-lg text-sm font-medium transition-colors"
           :class="page==='dashboard' ? 'bg-primary/10 text-primary' : 'text-gray-600 hover:bg-gray-50'">
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z"/></svg>
          <span x-text="t('dashboard')"></span>
        </a>
        <a href="#clients" @click.prevent="navigate('clients')"
           class="flex items-center gap-3 px-4 py-2.5 rounded-lg text-sm font-medium transition-colors"
           :class="page==='clients' ? 'bg-primary/10 text-primary' : 'text-gray-600 hover:bg-gray-50'">
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z"/></svg>
          <span x-text="t('clients')"></span>
        </a>
        <a href="#travel-types" @click.prevent="navigate('travel-types')"
           x-show="user?.role === 'admin'"
           class="flex items-center gap-3 px-4 py-2.5 rounded-lg text-sm font-medium transition-colors"
           :class="page==='travel-types' ? 'bg-primary/10 text-primary' : 'text-gray-600 hover:bg-gray-50'">
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3.055 11H5a2 2 0 012 2v1a2 2 0 002 2 2 2 0 012 2v2.945M8 3.935V5.5A2.5 2.5 0 0010.5 8h.5a2 2 0 012 2 2 2 0 104 0 2 2 0 012-2h1.064M15 20.488V18a2 2 0 012-2h3.064"/></svg>
          <span x-text="t('travel_types')"></span>
        </a>
        <a href="#users" @click.prevent="navigate('users')"
           x-show="user?.role === 'admin'"
           class="flex items-center gap-3 px-4 py-2.5 rounded-lg text-sm font-medium transition-colors"
           :class="page==='users' ? 'bg-primary/10 text-primary' : 'text-gray-600 hover:bg-gray-50'">
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"/></svg>
          <span x-text="t('users')"></span>
        </a>
      </nav>
      <div class="p-4 border-t border-gray-100">
        <div class="flex items-center gap-3 px-4 py-2">
          <div class="w-8 h-8 rounded-full bg-primary text-white flex items-center justify-center text-sm font-bold"
               x-text="user?.full_name?.charAt(0) || 'U'"></div>
          <div class="flex-1 min-w-0">
            <p class="text-sm font-medium truncate" x-text="user?.full_name"></p>
            <p class="text-xs text-gray-500 truncate" x-text="user?.email"></p>
          </div>
        </div>
        <button @click="doLogout()" class="btn btn-ghost w-full mt-2 text-sm" x-text="t('logout')"></button>
      </div>
    </aside>

    <!-- Overlay for mobile -->
    <div x-show="mobileMenuOpen" @click="mobileMenuOpen = false" class="fixed inset-0 bg-black/20 z-30 lg:hidden"></div>

    <!-- Main Content -->
    <main class="flex-1 lg:ml-0 transition-all">
      <!-- Top Bar -->
      <header class="bg-surface border-b border-gray-200 px-6 py-3 flex items-center justify-between sticky top-0 z-20">
        <div class="flex items-center gap-3">
          <button @click="mobileMenuOpen = !mobileMenuOpen" class="lg:hidden p-2 rounded-lg hover:bg-gray-100">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16"/></svg>
          </button>
          <h2 class="text-lg font-semibold" x-text="pageTitle()"></h2>
        </div>
        <div class="flex items-center gap-3">
          <span class="text-xs text-gray-500" x-text="t('language') + ':'"></span>
          <button @click="setLang('en')" class="lang-btn" :class="{'active': lang==='en'}">EN</button>
          <button @click="setLang('fr')" class="lang-btn" :class="{'active': lang==='fr'}">FR</button>
          <button @click="setLang('ar')" class="lang-btn" :class="{'active': lang==='ar'}">AR</button>
        </div>
      </header>

      <div class="p-6 max-w-7xl mx-auto">
        <!-- DASHBOARD -->
        <div x-show="page === 'dashboard'" class="fade-in">
          <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
            <div class="stat-card">
              <p class="text-sm text-gray-500 mb-1" x-text="t('total_clients')"></p>
              <p class="text-3xl font-bold text-primary" x-text="stats.total || 0"></p>
            </div>
            <div class="stat-card">
              <p class="text-sm text-gray-500 mb-1" x-text="t('active_clients')"></p>
              <p class="text-3xl font-bold text-success" x-text="stats.active || 0"></p>
            </div>
            <div class="stat-card">
              <p class="text-sm text-gray-500 mb-1" x-text="t('by_travel_type')"></p>
              <div class="space-y-1 mt-2">
                <template x-for="item in stats.byType" :key="item.code">
                  <div class="flex justify-between text-sm">
                    <span x-text="item.name"></span>
                    <span class="font-semibold" x-text="item.count"></span>
                  </div>
                </template>
              </div>
            </div>
          </div>
        </div>

        <!-- CLIENTS LIST -->
        <div x-show="page === 'clients'" class="fade-in">
          <!-- Toolbar -->
          <div class="flex flex-wrap items-center gap-3 mb-6">
            <div class="flex-1 min-w-[200px]">
              <input type="text" x-model="clientFilters.search" @input.debounce.300="loadClients()"
                     class="form-input" :placeholder="t('search') + '...'">
            </div>
            <button @click="showFilters = !showFilters" class="btn btn-ghost border border-gray-200">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.293A1 1 0 013 6.586V4z"/></svg>
              <span x-text="t('filters')"></span>
            </button>
            <button @click="openImportModal()" class="btn btn-secondary">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12"/></svg>
              <span x-text="t('import')"></span>
            </button>
            <div class="relative" x-data="{open:false}">
              <button @click="open = !open" class="btn btn-primary">
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"/></svg>
                <span x-text="t('export')"></span>
              </button>
              <div x-show="open" @click.outside="open = false" class="absolute right-0 mt-2 w-40 bg-white rounded-lg shadow-lg border border-gray-200 py-1 z-10">
                <button @click="doExport('xlsx'); open=false" class="block w-full text-left px-4 py-2 text-sm hover:bg-gray-50" x-text="t('xlsx')"></button>
                <button @click="doExport('csv'); open=false" class="block w-full text-left px-4 py-2 text-sm hover:bg-gray-50" x-text="t('csv')"></button>
                <button @click="doExport('pdf'); open=false" class="block w-full text-left px-4 py-2 text-sm hover:bg-gray-50" x-text="t('pdf')"></button>
              </div>
            </div>
            <button @click="navigate('client-form')" class="btn btn-primary">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/></svg>
              <span x-text="t('add_client')"></span>
            </button>
          </div>

          <!-- Filters Panel -->
          <div x-show="showFilters" class="bg-white rounded-xl border border-gray-200 p-4 mb-4 fade-in">
            <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div>
                <label class="block text-xs font-medium text-gray-500 mb-1" x-text="t('travel_type')"></label>
                <select x-model="clientFilters.travel_type" class="form-input">
                  <option value="" x-text="t('all')"></option>
                  <template x-for="tt in travelTypes" :key="tt.id">
                    <option :value="tt.code" x-text="tt.name"></option>
                  </template>
                </select>
              </div>
              <div>
                <label class="block text-xs font-medium text-gray-500 mb-1" x-text="t('status')"></label>
                <select x-model="clientFilters.status" class="form-input">
                  <option value="" x-text="t('all')"></option>
                  <option value="active" x-text="t('active')"></option>
                  <option value="completed" x-text="t('completed')"></option>
                  <option value="cancelled" x-text="t('cancelled')"></option>
                </select>
              </div>
              <div>
                <label class="block text-xs font-medium text-gray-500 mb-1" x-text="t('gender')"></label>
                <select x-model="clientFilters.gender" class="form-input">
                  <option value="" x-text="t('all')"></option>
                  <option value="M" x-text="t('male')"></option>
                  <option value="F" x-text="t('female')"></option>
                </select>
              </div>
              <div class="flex items-end gap-2">
                <div class="flex-1">
                  <label class="block text-xs font-medium text-gray-500 mb-1" x-text="t('date_from')"></label>
                  <input type="date" x-model="clientFilters.travel_date_from" class="form-input">
                </div>
                <div class="flex-1">
                  <label class="block text-xs font-medium text-gray-500 mb-1" x-text="t('date_to')"></label>
                  <input type="date" x-model="clientFilters.travel_date_to" class="form-input">
                </div>
              </div>
            </div>
            <div class="flex justify-end gap-2 mt-4">
              <button @click="resetFilters()" class="btn btn-ghost text-sm" x-text="t('reset')"></button>
              <button @click="showFilters=false; loadClients()" class="btn btn-primary text-sm" x-text="t('apply')"></button>
            </div>
          </div>

          <!-- Table -->
          <div class="bg-white rounded-xl border border-gray-200 overflow-hidden">
            <div class="overflow-x-auto">
              <table class="data-table">
                <thead>
                  <tr>
                    <th x-text="t('surname')"></th>
                    <th x-text="t('given_name')"></th>
                    <th x-text="t('father_name')"></th>
                    <th x-text="t('passport_number')"></th>
                    <th x-text="t('travel_type')"></th>
                    <th x-text="t('travel_date')"></th>
                    <th x-text="t('status')"></th>
                    <th x-text="t('actions')"></th>
                  </tr>
                </thead>
                <tbody>
                  <template x-for="c in clients" :key="c.id">
                    <tr>
                      <td class="font-medium" x-text="c.surname"></td>
                      <td x-text="c.given_name"></td>
                      <td x-text="c.father_name"></td>
                      <td x-text="c.passport_number"></td>
                      <td>
                        <span class="inline-flex px-2 py-1 rounded-full text-xs font-medium bg-blue-50 text-blue-700"
                              x-text="c.travel_type?.name || c.travel_type_id"></span>
                      </td>
                      <td x-text="c.travel_date"></td>
                      <td>
                        <span class="inline-flex px-2 py-1 rounded-full text-xs font-medium"
                              :class="c.status==='active' ? 'bg-green-50 text-green-700' : (c.status==='completed' ? 'bg-gray-50 text-gray-700' : 'bg-red-50 text-red-700')"
                              x-text="t(c.status)"></span>
                      </td>
                      <td>
                        <div class="flex items-center gap-2">
                          <button @click="editClient(c)" class="p-1.5 rounded-lg hover:bg-gray-100 text-gray-500">
                            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"/></svg>
                          </button>
                          <button @click="deleteClient(c.id)" class="p-1.5 rounded-lg hover:bg-red-50 text-red-500">
                            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/></svg>
                          </button>
                        </div>
                      </td>
                    </tr>
                  </template>
                  <tr x-show="clients.length === 0">
                    <td colspan="8" class="text-center py-12 text-gray-400" x-text="t('no_results')"></td>
                  </tr>
                </tbody>
              </table>
            </div>
            <!-- Pagination -->
            <div class="flex items-center justify-between px-4 py-3 border-t border-gray-200" x-show="clientPagination.total > 0">
              <div class="text-sm text-gray-500">
                <span x-text="t('page') + ' ' + clientPagination.page + ' ' + t('of') + ' ' + Math.ceil(clientPagination.total/clientPagination.limit)"></span>
              </div>
              <div class="flex gap-2">
                <button @click="prevPage()" :disabled="clientPagination.page <= 1" class="btn btn-ghost text-sm" x-text="t('previous')"></button>
                <button @click="nextPage()" :disabled="clientPagination.page * clientPagination.limit >= clientPagination.total" class="btn btn-ghost text-sm" x-text="t('next')"></button>
              </div>
            </div>
          </div>
        </div>

        <!-- CLIENT FORM (Add/Edit) -->
        <div x-show="page === 'client-form'" class="fade-in">
          <div class="flex items-center gap-3 mb-6">
            <button @click="navigate('clients')" class="btn btn-ghost">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 19l-7-7m0 0l7-7m-7 7h18"/></svg>
            </button>
            <h3 class="text-lg font-semibold" x-text="editingClient ? t('edit') : t('add_client')"></h3>
          </div>
          <div class="space-y-6">
            <template x-for="(form, idx) in clientForms" :key="idx">
              <div class="bg-white rounded-xl border border-gray-200 p-6">
                <div class="flex items-center justify-between mb-4" x-show="clientForms.length > 1">
                  <span class="text-sm font-medium text-gray-500" x-text="'#' + (idx+1)"></span>
                  <button @click="removeClientForm(idx)" class="text-red-500 hover:text-red-700" x-show="clientForms.length > 1">
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/></svg>
                  </button>
                </div>
                <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div>
                    <label class="block text-xs font-medium text-gray-500 mb-1" x-text="t('surname') + ' *'"></label>
                    <input type="text" x-model="form.surname" class="form-input" required>
                  </div>
                  <div>
                    <label class="block text-xs font-medium text-gray-500 mb-1" x-text="t('given_name') + ' *'"></label>
                    <input type="text" x-model="form.given_name" class="form-input" required>
                  </div>
                  <div>
                    <label class="block text-xs font-medium text-gray-500 mb-1" x-text="t('father_name') + ' *'"></label>
                    <input type="text" x-model="form.father_name" class="form-input" required>
                  </div>
                  <div>
                    <label class="block text-xs font-medium text-gray-500 mb-1" x-text="t('mother_name')"></label>
                    <input type="text" x-model="form.mother_name" class="form-input">
                  </div>
                  <div>
                    <label class="block text-xs font-medium text-gray-500 mb-1" x-text="t('passport_number') + ' *'"></label>
                    <input type="text" x-model="form.passport_number" class="form-input" required>
                  </div>
                  <div>
                    <label class="block text-xs font-medium text-gray-500 mb-1" x-text="t('nationality') + ' *'"></label>
                    <input type="text" x-model="form.nationality" class="form-input" required>
                  </div>
                  <div>
                    <label class="block text-xs font-medium text-gray-500 mb-1" x-text="t('date_of_birth')"></label>
                    <input type="date" x-model="form.date_of_birth" class="form-input">
                  </div>
                  <div>
                    <label class="block text-xs font-medium text-gray-500 mb-1" x-text="t('passport_issue_date')"></label>
                    <input type="date" x-model="form.passport_issue_date" class="form-input">
                  </div>
                  <div>
                    <label class="block text-xs font-medium text-gray-500 mb-1" x-text="t('passport_expiry')"></label>
                    <input type="date" x-model="form.passport_expiry" class="form-input">
                  </div>
                  <div>
                    <label class="block text-xs font-medium text-gray-500 mb-1" x-text="t('gender')"></label>
                    <select x-model="form.gender" class="form-input">
                      <option value="" x-text="t('all')"></option>
                      <option value="M" x-text="t('male')"></option>
                      <option value="F" x-text="t('female')"></option>
                    </select>
                  </div>
                  <div>
                    <label class="block text-xs font-medium text-gray-500 mb-1" x-text="t('travel_type') + ' *'"></label>
                    <select x-model="form.travel_type_id" class="form-input" required>
                      <option value="" x-text="t('all')"></option>
                      <template x-for="tt in travelTypes" :key="tt.id">
                        <option :value="tt.id" x-text="tt.name"></option>
                      </template>
                    </select>
                  </div>
                  <div>
                    <label class="block text-xs font-medium text-gray-500 mb-1" x-text="t('payment_method')"></label>
                    <select x-model="form.payment_method" class="form-input">
                      <option value="cash" x-text="t('cash')"></option>
                      <option value="instalment" x-text="t('instalment')"></option>
                      <option value="bank_transfer" x-text="t('bank_transfer')"></option>
                    </select>
                  </div>
                  <div>
                    <label class="block text-xs font-medium text-gray-500 mb-1" x-text="t('travel_date') + ' *'"></label>
                    <input type="date" x-model="form.travel_date" class="form-input" required>
                  </div>
                  <div class="md:col-span-3">
                    <label class="block text-xs font-medium text-gray-500 mb-1" x-text="t('notes')"></label>
                    <textarea x-model="form.notes" class="form-input" rows="2"></textarea>
                  </div>
                </div>
              </div>
            </template>
            <div class="flex items-center gap-3">
              <button @click="addClientForm()" class="btn btn-ghost border border-dashed border-gray-300" x-show="!editingClient">
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/></svg>
                <span x-text="t('add_another')"></span>
              </button>
              <div class="flex-1"></div>
              <button @click="navigate('clients')" class="btn btn-ghost" x-text="t('cancel')"></button>
              <button @click="saveClients()" class="btn btn-primary" :disabled="loading">
                <span x-show="!loading" x-text="t('save')"></span>
                <span x-show="loading">...</span>
              </button>
            </div>
          </div>
        </div>

        <!-- TRAVEL TYPES -->
        <div x-show="page === 'travel-types'" class="fade-in">
          <div class="flex justify-between items-center mb-6">
            <h3 class="text-lg font-semibold" x-text="t('travel_types')"></h3>
            <button @click="openTravelTypeModal()" class="btn btn-primary">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/></svg>
              <span x-text="t('add')"></span>
            </button>
          </div>
          <div class="bg-white rounded-xl border border-gray-200 overflow-hidden">
            <table class="data-table">
              <thead>
                <tr>
                  <th x-text="t('code')"></th>
                  <th x-text="t('name_en')"></th>
                  <th x-text="t('name_fr')"></th>
                  <th x-text="t('name_ar')"></th>
                  <th x-text="t('is_active')"></th>
                  <th x-text="t('actions')"></th>
                </tr>
              </thead>
              <tbody>
                <template x-for="tt in travelTypes" :key="tt.id">
                  <tr>
                    <td class="font-mono text-sm" x-text="tt.code"></td>
                    <td x-text="tt.name_en"></td>
                    <td x-text="tt.name_fr"></td>
                    <td x-text="tt.name_ar"></td>
                    <td>
                      <span class="inline-flex px-2 py-1 rounded-full text-xs font-medium"
                            :class="tt.is_active ? 'bg-green-50 text-green-700' : 'bg-gray-50 text-gray-500'"
                            x-text="tt.is_active ? t('active') : t('cancelled')"></span>
                    </td>
                    <td>
                      <div class="flex items-center gap-2">
                        <button @click="openTravelTypeModal(tt)" class="p-1.5 rounded-lg hover:bg-gray-100 text-gray-500">
                          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"/></svg>
                        </button>
                        <button @click="deleteTravelType(tt.id)" class="p-1.5 rounded-lg hover:bg-red-50 text-red-500">
                          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/></svg>
                        </button>
                      </div>
                    </td>
                  </tr>
                </template>
              </tbody>
            </table>
          </div>
        </div>

        <!-- USERS -->
        <div x-show="page === 'users'" class="fade-in">
          <div class="flex justify-between items-center mb-6">
            <h3 class="text-lg font-semibold" x-text="t('users')"></h3>
            <button @click="openUserModal()" class="btn btn-primary">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/></svg>
              <span x-text="t('add')"></span>
            </button>
          </div>
          <div class="bg-white rounded-xl border border-gray-200 overflow-hidden">
            <table class="data-table">
              <thead>
                <tr>
                  <th x-text="t('full_name')"></th>
                  <th x-text="t('email')"></th>
                  <th x-text="t('role')"></th>
                  <th x-text="t('language')"></th>
                  <th x-text="t('is_active')"></th>
                  <th x-text="t('actions')"></th>
                </tr>
              </thead>
              <tbody>
                <template x-for="u in users" :key="u.id">
                  <tr>
                    <td class="font-medium" x-text="u.full_name"></td>
                    <td x-text="u.email"></td>
                    <td>
                      <span class="inline-flex px-2 py-1 rounded-full text-xs font-medium"
                            :class="u.role==='admin' ? 'bg-purple-50 text-purple-700' : 'bg-blue-50 text-blue-700'"
                            x-text="t(u.role)"></span>
                    </td>
                    <td class="uppercase" x-text="u.preferred_lang"></td>
                    <td>
                      <span class="inline-flex px-2 py-1 rounded-full text-xs font-medium"
                            :class="u.is_active ? 'bg-green-50 text-green-700' : 'bg-gray-50 text-gray-500'"
                            x-text="u.is_active ? t('active') : t('cancelled')"></span>
                    </td>
                    <td>
                      <div class="flex items-center gap-2">
                        <button @click="openUserModal(u)" class="p-1.5 rounded-lg hover:bg-gray-100 text-gray-500">
                          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"/></svg>
                        </button>
                        <button @click="deleteUser(u.id)" class="p-1.5 rounded-lg hover:bg-red-50 text-red-500">
                          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/></svg>
                        </button>
                      </div>
                    </td>
                  </tr>
                </template>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </main>
  </div>

  <!-- IMPORT MODAL -->
  <div x-show="importModalOpen" class="modal-backdrop" style="display:none;">
    <div class="modal-content">
      <div class="p-6 border-b border-gray-100 flex justify-between items-center">
        <h3 class="text-lg font-semibold" x-text="t('import')"></h3>
        <button @click="importModalOpen = false" class="p-1 rounded-lg hover:bg-gray-100">
          <svg class="w-5 h-5 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/></svg>
        </button>
      </div>
      <div class="p-6">
        <!-- Step 1: Upload -->
        <div x-show="importStep === 1">
          <div class="flex gap-2 mb-4">
            <a :href="`/api/v1/templates/${lang}`" class="text-xs text-primary hover:underline" x-text="t('template_en')" download></a>
            <a :href="`/api/v1/templates/fr`" class="text-xs text-primary hover:underline" x-text="t('template_fr')" download></a>
            <a :href="`/api/v1/templates/ar`" class="text-xs text-primary hover:underline" x-text="t('template_ar')" download></a>
          </div>
          <div class="drop-zone"
               @dragover.prevent="$el.classList.add('dragover')"
               @dragleave.prevent="$el.classList.remove('dragover')"
               @drop.prevent="handleFileDrop($event)"
               @click="$refs.fileInput.click()">
            <svg class="w-12 h-12 mx-auto mb-3 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"/></svg>
            <p class="text-sm text-gray-600 font-medium" x-text="t('drag_drop')"></p>
            <p class="text-xs text-gray-400 mt-1" x-text="t('or_click')"></p>
            <input type="file" x-ref="fileInput" @change="handleFileSelect($event)" accept=".xlsx,.csv" class="hidden">
          </div>
        </div>

        <!-- Step 2: Preview -->
        <div x-show="importStep === 2">
          <div class="mb-4 flex items-center gap-4 text-sm">
            <span class="text-green-600 font-medium" x-text="importPreview.valid_rows + ' ' + t('valid_rows')"></span>
            <span x-show="importPreview.errors.length > 0" class="text-red-600 font-medium" x-text="importPreview.errors.length + ' ' + t('errors')"></span>
          </div>
          <div class="overflow-x-auto max-h-64 border border-gray-200 rounded-lg mb-4">
            <table class="data-table">
              <thead class="sticky top-0">
                <tr>
                  <th class="bg-gray-50 text-gray-700">#</th>
                  <th class="bg-gray-50 text-gray-700" x-text="t('surname')"></th>
                  <th class="bg-gray-50 text-gray-700" x-text="t('given_name')"></th>
                  <th class="bg-gray-50 text-gray-700" x-text="t('passport_number')"></th>
                  <th class="bg-gray-50 text-gray-700" x-text="t('travel_type')"></th>
                  <th class="bg-gray-50 text-gray-700" x-text="t('travel_date')"></th>
                </tr>
              </thead>
              <tbody>
                <template x-for="(row, idx) in importPreview.preview_data" :key="idx">
                  <tr>
                    <td x-text="idx+1"></td>
                    <td x-text="row.surname"></td>
                    <td x-text="row.given_name"></td>
                    <td x-text="row.passport_number"></td>
                    <td x-text="row.travel_type"></td>
                    <td x-text="row.travel_date"></td>
                  </tr>
                </template>
              </tbody>
            </table>
          </div>
          <div class="flex justify-end gap-2">
            <button @click="importStep = 1" class="btn btn-ghost" x-text="t('retry')"></button>
            <button @click="confirmImport()" class="btn btn-primary" :disabled="importPreview.valid_rows === 0">
              <span x-text="t('confirm_import') + ' (' + importPreview.valid_rows + ')'"></span>
            </button>
          </div>
        </div>

        <!-- Step 3: Result -->
        <div x-show="importStep === 3">
          <div class="text-center py-8">
            <div class="w-16 h-16 bg-green-100 text-green-600 rounded-full flex items-center justify-center mx-auto mb-4">
              <svg class="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/></svg>
            </div>
            <p class="text-lg font-medium text-gray-800" x-text="importResult.imported_count + ' ' + t('import_success')"></p>
            <p x-show="importResult.duplicates_skipped > 0" class="text-sm text-gray-500 mt-1"
               x-text="importResult.duplicates_skipped + ' duplicates skipped'"></p>
            <button @click="importModalOpen = false; loadClients()" class="btn btn-primary mt-6" x-text="t('close')"></button>
          </div>
        </div>
      </div>
    </div>
  </div>

  <!-- TRAVEL TYPE MODAL -->
  <div x-show="travelTypeModalOpen" class="modal-backdrop" style="display:none;">
    <div class="modal-content max-w-lg">
      <div class="p-6 border-b border-gray-100 flex justify-between items-center">
        <h3 class="text-lg font-semibold" x-text="editingTravelType ? t('edit') : t('add')"></h3>
        <button @click="travelTypeModalOpen = false" class="p-1 rounded-lg hover:bg-gray-100">
          <svg class="w-5 h-5 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/></svg>
        </button>
      </div>
      <div class="p-6 space-y-4">
        <div>
          <label class="block text-xs font-medium text-gray-500 mb-1" x-text="t('code') + ' *'"></label>
          <input type="text" x-model="travelTypeForm.code" class="form-input" :disabled="editingTravelType">
        </div>
        <div>
          <label class="block text-xs font-medium text-gray-500 mb-1" x-text="t('name_en') + ' *'"></label>
          <input type="text" x-model="travelTypeForm.name_en" class="form-input">
        </div>
        <div>
          <label class="block text-xs font-medium text-gray-500 mb-1" x-text="t('name_fr') + ' *'"></label>
          <input type="text" x-model="travelTypeForm.name_fr" class="form-input">
        </div>
        <div>
          <label class="block text-xs font-medium text-gray-500 mb-1" x-text="t('name_ar') + ' *'"></label>
          <input type="text" x-model="travelTypeForm.name_ar" class="form-input" dir="rtl">
        </div>
        <div class="flex justify-end gap-2 pt-2">
          <button @click="travelTypeModalOpen = false" class="btn btn-ghost" x-text="t('cancel')"></button>
          <button @click="saveTravelType()" class="btn btn-primary" x-text="t('save')"></button>
        </div>
      </div>
    </div>
  </div>

  <!-- USER MODAL -->
  <div x-show="userModalOpen" class="modal-backdrop" style="display:none;">
    <div class="modal-content max-w-lg">
      <div class="p-6 border-b border-gray-100 flex justify-between items-center">
        <h3 class="text-lg font-semibold" x-text="editingUser ? t('edit') : t('add')"></h3>
        <button @click="userModalOpen = false" class="p-1 rounded-lg hover:bg-gray-100">
          <svg class="w-5 h-5 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/></svg>
        </button>
      </div>
      <div class="p-6 space-y-4">
        <div>
          <label class="block text-xs font-medium text-gray-500 mb-1" x-text="t('full_name') + ' *'"></label>
          <input type="text" x-model="userForm.full_name" class="form-input">
        </div>
        <div>
          <label class="block text-xs font-medium text-gray-500 mb-1" x-text="t('email') + ' *'"></label>
          <input type="email" x-model="userForm.email" class="form-input" :disabled="editingUser">
        </div>
        <div x-show="!editingUser">
          <label class="block text-xs font-medium text-gray-500 mb-1" x-text="t('password') + ' *'"></label>
          <input type="password" x-model="userForm.password" class="form-input">
        </div>
        <div>
          <label class="block text-xs font-medium text-gray-500 mb-1" x-text="t('role')"></label>
          <select x-model="userForm.role" class="form-input">
            <option value="agent" x-text="t('agent')"></option>
            <option value="admin" x-text="t('admin')"></option>
          </select>
        </div>
        <div>
          <label class="block text-xs font-medium text-gray-500 mb-1" x-text="t('language')"></label>
          <select x-model="userForm.preferred_lang" class="form-input">
            <option value="en" x-text="t('english')"></option>
            <option value="fr" x-text="t('french')"></option>
            <option value="ar" x-text="t('arabic')"></option>
          </select>
        </div>
        <div class="flex justify-end gap-2 pt-2">
          <button @click="userModalOpen = false" class="btn btn-ghost" x-text="t('cancel')"></button>
          <button @click="saveUser()" class="btn btn-primary" x-text="t('save')"></button>
        </div>
      </div>
    </div>
  </div>

  <script src="/js/app.js"></script>
</body>
</html>
```

### app.js
```javascript

function app() {
  return {
    // State
    lang: localStorage.getItem('lang') || 'en',
    isLoggedIn: false,
    loading: false,
    page: 'dashboard',
    mobileMenuOpen: false,
    user: null,
    toasts: [],
    locales: {},

    // Login
    loginForm: { email: '', password: '' },
    loginError: '',

    // Clients
    clients: [],
    clientPagination: { page: 1, limit: 50, total: 0 },
    clientFilters: {
      search: '',
      travel_type: '',
      status: '',
      gender: '',
      travel_date_from: '',
      travel_date_to: ''
    },
    showFilters: false,
    editingClient: null,
    clientForms: [],

    // Travel Types
    travelTypes: [],
    travelTypeModalOpen: false,
    editingTravelType: null,
    travelTypeForm: { code: '', name_en: '', name_fr: '', name_ar: '' },

    // Users
    users: [],
    userModalOpen: false,
    editingUser: null,
    userForm: { full_name: '', email: '', password: '', role: 'agent', preferred_lang: 'en' },

    // Import
    importModalOpen: false,
    importStep: 1,
    importPreview: { validation_id: '', total_rows: 0, valid_rows: 0, errors: [], preview_data: [] },
    importResult: { imported_count: 0, duplicates_skipped: 0 },

    // Export
    exportJobId: null,
    exportPolling: null,

    // Dashboard
    stats: { total: 0, active: 0, byType: [] },

    async initApp() {
      // Auth disabled – auto-login
      this.isLoggedIn = true;
      this.user = { id: 1, email: 'admin@minadoor.com', role: 'admin', full_name: 'Admin', preferred_lang: 'en' };
      await this.loadLocale();
      await this.loadTravelTypes();
      await this.loadClients();
    },

    async loadLocale() {
      try {
        const res = await fetch(`/locales/${this.lang}.json`);
        this.locales = await res.json();
      } catch (e) {
        this.locales = {};
      }
    },

    t(key) {
      return this.locales[key] || key;
    },

    setLang(l) {
      this.lang = l;
      localStorage.setItem('lang', l);
      this.loadLocale();
      document.documentElement.lang = l;
      document.documentElement.dir = l === 'ar' ? 'rtl' : 'ltr';
      if (this.isLoggedIn) {
        this.loadTravelTypes();
        if (this.page === 'clients') this.loadClients();
      }
    },

    pageTitle() {
      return this.t(this.page === 'client-form' ? 'clients' : this.page);
    },

    navigate(p) {
      this.page = p;
      this.mobileMenuOpen = false;
      if (p === 'clients') this.loadClients();
      if (p === 'travel-types') this.loadTravelTypes();
      if (p === 'users') this.loadUsers();
      if (p === 'dashboard') this.loadStats();
      if (p === 'client-form') {
        this.editingClient = null;
        this.clientForms = [this.emptyClientForm()];
      }
    },

    emptyClientForm() {
      return {
        surname: '', given_name: '', father_name: '', mother_name: '',
        passport_number: '', nationality: '', date_of_birth: '',
        passport_issue_date: '', passport_expiry: '', gender: '',
        travel_type_id: '', payment_method: 'cash', travel_date: '', notes: ''
      };
    },

    addClientForm() {
      this.clientForms.push(this.emptyClientForm());
    },

    removeClientForm(idx) {
      this.clientForms.splice(idx, 1);
    },

    async doLogin() {
      this.loading = true;
      this.loginError = '';
      try {
        const res = await fetch('/api/api/v1/auth/login', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(this.loginForm)
        });
        const data = await res.json();
        if (res.ok) {
          localStorage.setItem('access_token', data.access_token);
          localStorage.setItem('refresh_token', data.refresh_token);
          this.isLoggedIn = true;
          await this.initApp();
          this.navigate('dashboard');
        } else {
          this.loginError = data.detail || this.t('auth_failed');
        }
      } catch (e) {
        this.loginError = this.t('error_occurred');
      }
      this.loading = false;
    },

    doLogout() {
      const rt = localStorage.getItem('refresh_token');
      if (rt) {
        fetch('/api/api/v1/auth/logout', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ refresh_token: rt })
        }).catch(() => {});
      }
      this.logout();
    },

    logout() {
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      this.isLoggedIn = false;
      this.user = null;
      this.page = 'dashboard';
    },

    api(path, opts = {}) {
      const token = localStorage.getItem('access_token');
      const headers = {
        'Accept-Language': this.lang,
        ...(opts.body && !(opts.body instanceof FormData) ? { 'Content-Type': 'application/json' } : {}),
        ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
        ...opts.headers
      };
      return fetch('/api/v1' + path, { ...opts, headers });
    },

    async loadClients() {
      this.loading = true;
      const params = new URLSearchParams();
      params.set('page', this.clientPagination.page);
      params.set('limit', this.clientPagination.limit);
      if (this.clientFilters.search) params.set('search', this.clientFilters.search);
      if (this.clientFilters.travel_type) params.set('travel_type', this.clientFilters.travel_type);
      if (this.clientFilters.status) params.set('status', this.clientFilters.status);
      if (this.clientFilters.gender) params.set('gender', this.clientFilters.gender);
      if (this.clientFilters.travel_date_from) params.set('travel_date_from', this.clientFilters.travel_date_from);
      if (this.clientFilters.travel_date_to) params.set('travel_date_to', this.clientFilters.travel_date_to);

      try {
        const res = await this.api(`/clients?${params}`);
        if (res.ok) {
          const data = await res.json();
          this.clients = data.items;
          this.clientPagination.total = data.total;
        }
      } catch (e) {}
      this.loading = false;
    },

    prevPage() {
      if (this.clientPagination.page > 1) {
        this.clientPagination.page--;
        this.loadClients();
      }
    },

    nextPage() {
      if (this.clientPagination.page * this.clientPagination.limit < this.clientPagination.total) {
        this.clientPagination.page++;
        this.loadClients();
      }
    },

    resetFilters() {
      this.clientFilters = { search: '', travel_type: '', status: '', gender: '', travel_date_from: '', travel_date_to: '' };
      this.clientPagination.page = 1;
      this.loadClients();
    },

    async loadTravelTypes() {
      try {
        const res = await this.api(`/travel-types?lang=${this.lang}`);
        if (res.ok) this.travelTypes = await res.json();
      } catch (e) {}
    },

    async loadUsers() {
      try {
        const res = await this.api('/users');
        if (res.ok) this.users = await res.json();
      } catch (e) {}
    },

    async loadStats() {
      try {
        // Total
        let res = await this.api('/clients?limit=1');
        if (res.ok) {
          const data = await res.json();
          this.stats.total = data.total;
        }
        // Active
        res = await this.api('/clients?status=active&limit=1');
        if (res.ok) {
          const data = await res.json();
          this.stats.active = data.total;
        }
        // By type
        this.stats.byType = [];
        for (const tt of this.travelTypes) {
          res = await this.api(`/clients?travel_type=${tt.code}&limit=1`);
          if (res.ok) {
            const data = await res.json();
            this.stats.byType.push({ code: tt.code, name: tt.name, count: data.total });
          }
        }
      } catch (e) {}
    },

    editClient(c) {
      this.editingClient = c;
      this.clientForms = [{
        surname: c.surname, given_name: c.given_name, father_name: c.father_name,
        mother_name: c.mother_name || '', passport_number: c.passport_number,
        nationality: c.nationality, date_of_birth: c.date_of_birth || '',
        passport_issue_date: c.passport_issue_date || '', passport_expiry: c.passport_expiry || '',
        gender: c.gender || '', travel_type_id: c.travel_type_id,
        payment_method: c.payment_method, travel_date: c.travel_date, notes: c.notes || ''
      }];
      this.navigate('client-form');
    },

    async deleteClient(id) {
      if (!confirm(this.t('confirm_delete'))) return;
      try {
        const res = await this.api(`/clients/${id}`, { method: 'DELETE' });
        if (res.ok) {
          this.showToast(this.t('delete') + ' OK', 'success');
          this.loadClients();
        }
      } catch (e) {}
    },

    async saveClients() {
      this.loading = true;
      try {
        if (this.editingClient) {
          const form = this.clientForms[0];
          const res = await this.api(`/clients/${this.editingClient.id}`, {
            method: 'PATCH',
            body: JSON.stringify(form)
          });
          if (res.ok) {
            this.showToast(this.t('save') + ' OK', 'success');
            this.navigate('clients');
          } else {
            const err = await res.json();
            this.showToast(err.detail || this.t('error_occurred'), 'error');
          }
        } else {
          // Batch create
          let ok = 0;
          for (const form of this.clientForms) {
            const res = await this.api('/clients', {
              method: 'POST',
              body: JSON.stringify(form)
            });
            if (res.ok) ok++;
          }
          this.showToast(`${ok}/${this.clientForms.length} ${this.t('save')} OK`, 'success');
          this.navigate('clients');
        }
      } catch (e) {
        this.showToast(this.t('error_occurred'), 'error');
      }
      this.loading = false;
    },

    // Import
    openImportModal() {
      this.importModalOpen = true;
      this.importStep = 1;
      this.importPreview = { validation_id: '', total_rows: 0, valid_rows: 0, errors: [], preview_data: [] };
    },

    handleFileDrop(e) {
      e.preventDefault();
      const files = e.dataTransfer.files;
      if (files.length) this.uploadImportFile(files[0]);
    },

    handleFileSelect(e) {
      const files = e.target.files;
      if (files.length) this.uploadImportFile(files[0]);
    },

    async uploadImportFile(file) {
      this.loading = true;
      const formData = new FormData();
      formData.append('file', file);
      try {
        const res = await this.api('/clients/import', { method: 'POST', body: formData });
        if (res.ok) {
          this.importPreview = await res.json();
          this.importStep = 2;
        } else {
          const err = await res.json();
          this.showToast(err.detail || this.t('import_failed'), 'error');
        }
      } catch (e) {
        this.showToast(this.t('error_occurred'), 'error');
      }
      this.loading = false;
    },

    async confirmImport() {
      this.loading = true;
      try {
        // Build corrected rows from preview_data (user may have edited inline in a real app)
        // Here we just send the valid preview rows
        const rows = this.importPreview.preview_data;
        // In a real app, user edits rows inline; here we send preview
        const res = await this.api('/clients/import/confirm', {
          method: 'POST',
          body: JSON.stringify({ rows })
        });
        if (res.ok) {
          this.importResult = await res.json();
          this.importStep = 3;
        }
      } catch (e) {
        this.showToast(this.t('error_occurred'), 'error');
      }
      this.loading = false;
    },

    // Export
    async doExport(format) {
      this.loading = true;
      try {
        const body = {
          format,
          search: this.clientFilters.search || undefined,
          travel_type: this.clientFilters.travel_type || undefined,
          status: this.clientFilters.status || undefined,
          gender: this.clientFilters.gender || undefined,
          travel_date_from: this.clientFilters.travel_date_from || undefined,
          travel_date_to: this.clientFilters.travel_date_to || undefined,
          header_lang: this.lang
        };
        const res = await this.api('/clients/export', {
          method: 'POST',
          body: JSON.stringify(body)
        });
        if (res.ok) {
          const data = await res.json();
          this.exportJobId = data.job_id;
          this.showToast(this.t('processing') + '...', 'success');
          this.pollExportStatus();
        }
      } catch (e) {}
      this.loading = false;
    },

    pollExportStatus() {
      if (this.exportPolling) clearInterval(this.exportPolling);
      this.exportPolling = setInterval(async () => {
        try {
          const res = await this.api(`/exports/${this.exportJobId}/status`);
          if (res.ok) {
            const data = await res.json();
            if (data.status === 'completed') {
              clearInterval(this.exportPolling);
              this.showToast(this.t('export_ready'), 'success');
              window.open(`/api/api/v1/exports/${this.exportJobId}/download`, '_blank');
            } else if (data.status === 'failed') {
              clearInterval(this.exportPolling);
              this.showToast(this.t('export_failed'), 'error');
            }
          }
        } catch (e) {}
      }, 3000);
    },

    // Travel Types
    openTravelTypeModal(tt = null) {
      this.editingTravelType = tt;
      if (tt) {
        this.travelTypeForm = { code: tt.code, name_en: tt.name_en, name_fr: tt.name_fr, name_ar: tt.name_ar };
      } else {
        this.travelTypeForm = { code: '', name_en: '', name_fr: '', name_ar: '' };
      }
      this.travelTypeModalOpen = true;
    },

    async saveTravelType() {
      try {
        const method = this.editingTravelType ? 'PATCH' : 'POST';
        const path = this.editingTravelType ? `/travel-types/${this.editingTravelType.id}` : '/travel-types';
        const res = await this.api(path, {
          method,
          body: JSON.stringify(this.travelTypeForm)
        });
        if (res.ok) {
          this.travelTypeModalOpen = false;
          this.loadTravelTypes();
          this.showToast(this.t('save') + ' OK', 'success');
        }
      } catch (e) {}
    },

    async deleteTravelType(id) {
      if (!confirm(this.t('confirm_delete'))) return;
      try {
        const res = await this.api(`/travel-types/${id}`, { method: 'DELETE' });
        if (res.ok) {
          this.loadTravelTypes();
          this.showToast(this.t('delete') + ' OK', 'success');
        }
      } catch (e) {}
    },

    // Users
    openUserModal(u = null) {
      this.editingUser = u;
      if (u) {
        this.userForm = { full_name: u.full_name, email: u.email, password: '', role: u.role, preferred_lang: u.preferred_lang };
      } else {
        this.userForm = { full_name: '', email: '', password: '', role: 'agent', preferred_lang: 'en' };
      }
      this.userModalOpen = true;
    },

    async saveUser() {
      try {
        const method = this.editingUser ? 'PATCH' : 'POST';
        const path = this.editingUser ? `/users/${this.editingUser.id}` : '/users';
        const body = { ...this.userForm };
        if (this.editingUser) delete body.password;
        const res = await this.api(path, { method, body: JSON.stringify(body) });
        if (res.ok) {
          this.userModalOpen = false;
          this.loadUsers();
          this.showToast(this.t('save') + ' OK', 'success');
        }
      } catch (e) {}
    },

    async deleteUser(id) {
      if (!confirm(this.t('confirm_delete'))) return;
      try {
        const res = await this.api(`/users/${id}`, { method: 'DELETE' });
        if (res.ok) {
          this.loadUsers();
          this.showToast(this.t('delete') + ' OK', 'success');
        }
      } catch (e) {}
    },

    showToast(message, type = 'success') {
      const id = Date.now();
      this.toasts.push({ id, message, type });
      setTimeout(() => {
        this.toasts = this.toasts.filter(t => t.id !== id);
      }, 4000);
    }
  };
}
// Global sanitizer
function sanitize(dirty) {
    return window.DOMPurify ? DOMPurify.sanitize(dirty) : dirty;
}
```

### app.css
```css

@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Noto+Naskh+Arabic:wght@400;500;600;700&display=swap');

:root {
  --primary: #1e40af;
  --primary-light: #3b82f6;
  --secondary: #f59e0b;
  --bg: #f8fafc;
  --surface: #ffffff;
  --text: #1e293b;
  --text-muted: #64748b;
  --border: #e2e8f0;
  --danger: #ef4444;
  --success: #10b981;
}

* { box-sizing: border-box; }

body {
  font-family: 'Inter', sans-serif;
  background: var(--bg);
  color: var(--text);
  margin: 0;
}

[dir="rtl"] body {
  font-family: 'Noto Naskh Arabic', 'Inter', sans-serif;
}

/* Custom scrollbar */
::-webkit-scrollbar { width: 8px; height: 8px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: #cbd5e1; border-radius: 4px; }
::-webkit-scrollbar-thumb:hover { background: #94a3b8; }

/* Logo styling */
.logo-img { max-height: 48px; width: auto; }

/* Drop zone */
.drop-zone {
  border: 2px dashed var(--border);
  border-radius: 12px;
  padding: 2rem;
  text-align: center;
  transition: all 0.2s;
  cursor: pointer;
}
.drop-zone:hover, .drop-zone.dragover {
  border-color: var(--primary);
  background: rgba(30,64,175,0.04);
}

/* Table */
.data-table { width: 100%; border-collapse: separate; border-spacing: 0; }
.data-table th {
  background: var(--primary);
  color: white;
  font-weight: 600;
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  padding: 0.75rem 1rem;
  text-align: left;
}
[dir="rtl"] .data-table th { text-align: right; }
.data-table td {
  padding: 0.875rem 1rem;
  border-bottom: 1px solid var(--border);
  font-size: 0.875rem;
}
.data-table tr:hover td { background: rgba(30,64,175,0.02); }

/* Cards */
.stat-card {
  background: var(--surface);
  border-radius: 12px;
  padding: 1.5rem;
  box-shadow: 0 1px 3px rgba(0,0,0,0.04);
  border: 1px solid var(--border);
}

/* Modal */
.modal-backdrop {
  position: fixed; inset: 0; background: rgba(0,0,0,0.5);
  display: flex; align-items: center; justify-content: center;
  z-index: 50; padding: 1rem;
}
.modal-content {
  background: var(--surface);
  border-radius: 16px;
  max-width: 900px; width: 100%;
  max-height: 90vh; overflow-y: auto;
  box-shadow: 0 20px 25px -5px rgba(0,0,0,0.1);
}

/* Form */
.form-input {
  width: 100%;
  padding: 0.5rem 0.75rem;
  border: 1px solid var(--border);
  border-radius: 8px;
  font-size: 0.875rem;
  transition: border-color 0.15s;
}
.form-input:focus {
  outline: none;
  border-color: var(--primary-light);
  box-shadow: 0 0 0 3px rgba(59,130,246,0.1);
}

/* Buttons */
.btn {
  display: inline-flex; align-items: center; gap: 0.5rem;
  padding: 0.5rem 1rem; border-radius: 8px;
  font-size: 0.875rem; font-weight: 500;
  transition: all 0.15s; cursor: pointer; border: none;
}
.btn-primary { background: var(--primary); color: white; }
.btn-primary:hover { background: #1e3a8a; }
.btn-secondary { background: var(--secondary); color: white; }
.btn-secondary:hover { background: #d97706; }
.btn-danger { background: var(--danger); color: white; }
.btn-ghost { background: transparent; color: var(--text-muted); }
.btn-ghost:hover { background: var(--bg); }

/* Language switcher */
.lang-btn {
  padding: 0.25rem 0.5rem;
  border-radius: 6px;
  font-size: 0.75rem;
  font-weight: 600;
  cursor: pointer;
  border: 1px solid var(--border);
  background: white;
}
.lang-btn.active {
  background: var(--primary);
  color: white;
  border-color: var(--primary);
}

/* Animations */
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: translateY(0); }
}
.fade-in { animation: fadeIn 0.25s ease-out; }

/* Toast */
.toast-container {
  position: fixed;
  top: 1rem;
  right: 1rem;
  z-index: 100;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}
[dir="rtl"] .toast-container { right: auto; left: 1rem; }
.toast {
  padding: 0.75rem 1rem;
  border-radius: 8px;
  color: white;
  font-size: 0.875rem;
  box-shadow: 0 4px 6px rgba(0,0,0,0.1);
  animation: fadeIn 0.2s ease-out;
}
.toast.success { background: var(--success); }
.toast.error { background: var(--danger); }
```

### Locales
#### ar.json
```json
{
  "app_name": "قاعدة بيانات مينا دور للسفر",
  "login": "تسجيل الدخول",
  "logout": "تسجيل الخروج",
  "email": "البريد الإلكتروني",
  "password": "كلمة المرور",
  "sign_in": "دخول",
  "dashboard": "لوحة التحكم",
  "clients": "العملاء",
  "travel_types": "أنواع السفر",
  "users": "المستخدمون",
  "settings": "الإعدادات",
  "search": "بحث",
  "add_client": "إضافة عميل",
  "add_another": "+ إضافة آخر",
  "save": "حفظ",
  "cancel": "إلغاء",
  "edit": "تعديل",
  "delete": "حذف",
  "confirm_delete": "هل أنت متأكد؟",
  "surname": "اللقب",
  "given_name": "الاسم",
  "father_name": "اسم الأب",
  "mother_name": "اسم الأم",
  "passport_number": "رقم جواز السفر",
  "nationality": "الجنسية",
  "date_of_birth": "تاريخ الميلاد",
  "passport_issue_date": "تاريخ الإصدار",
  "passport_expiry": "تاريخ الانتهاء",
  "gender": "الجنس",
  "male": "ذكر",
  "female": "أنثى",
  "travel_type": "نوع السفر",
  "payment_method": "طريقة الدفع",
  "travel_date": "تاريخ السفر",
  "status": "الحالة",
  "notes": "ملاحظات",
  "active": "نشط",
  "completed": "مكتمل",
  "cancelled": "ملغى",
  "cash": "نقدًا",
  "instalment": "بالتقسيط",
  "bank_transfer": "تحويل بنكي",
  "total_clients": "إجمالي العملاء",
  "active_clients": "العملاء النشطون",
  "by_travel_type": "حسب نوع السفر",
  "import": "استيراد",
  "export": "تصدير",
  "drag_drop": "اسحب الملف وأفلته هنا",
  "or_click": "أو انقر للاستعراض",
  "template_en": "قالب (EN)",
  "template_fr": "قالب (FR)",
  "template_ar": "قالب (AR)",
  "preview": "معاينة",
  "confirm_import": "تأكيد الاستيراد",
  "valid_rows": "الصفوف الصالحة",
  "errors": "أخطاء",
  "processing": "جاري المعالجة",
  "download": "تحميل",
  "xlsx": "إكسل",
  "csv": "CSV",
  "pdf": "PDF",
  "page": "صفحة",
  "of": "من",
  "previous": "السابق",
  "next": "التالي",
  "no_results": "لا توجد نتائج",
  "language": "اللغة",
  "english": "English",
  "french": "Français",
  "arabic": "العربية",
  "admin": "مدير",
  "agent": "وكيل",
  "role": "الدور",
  "full_name": "الاسم الكامل",
  "created_at": "تاريخ الإنشاء",
  "actions": "إجراءات",
  "code": "الرمز",
  "name": "الاسم",
  "is_active": "نشط",
  "close": "إغلاق",
  "retry": "إعادة المحاولة",
  "import_success": "اكتمل الاستيراد بنجاح",
  "export_ready": "جاهز للتحميل",
  "error_occurred": "حدث خطأ",
  "required_field": "هذا الحقل مطلوب",
  "duplicate_passport": "رقم جواز السفر موجود مسبقاً",
  "filters": "عوامل التصفية",
  "apply": "تطبيق",
  "reset": "إعادة تعيين",
  "date_from": "من",
  "date_to": "إلى",
  "all": "الكل"
}```

#### en.json
```json
{
  "app_name": "MinaDoor Travel DB",
  "login": "Login",
  "logout": "Logout",
  "email": "Email",
  "password": "Password",
  "sign_in": "Sign In",
  "dashboard": "Dashboard",
  "clients": "Clients",
  "travel_types": "Travel Types",
  "users": "Users",
  "settings": "Settings",
  "search": "Search",
  "add_client": "Add Client",
  "add_another": "+ Add another",
  "save": "Save",
  "cancel": "Cancel",
  "edit": "Edit",
  "delete": "Delete",
  "confirm_delete": "Are you sure?",
  "surname": "Surname",
  "given_name": "Given Name",
  "father_name": "Father Name",
  "mother_name": "Mother Name",
  "passport_number": "Passport Number",
  "nationality": "Nationality",
  "date_of_birth": "Date of Birth",
  "passport_issue_date": "Passport Issue Date",
  "passport_expiry": "Passport Expiry",
  "gender": "Gender",
  "male": "Male",
  "female": "Female",
  "travel_type": "Travel Type",
  "payment_method": "Payment Method",
  "travel_date": "Travel Date",
  "status": "Status",
  "notes": "Notes",
  "active": "Active",
  "completed": "Completed",
  "cancelled": "Cancelled",
  "cash": "Cash",
  "instalment": "Instalment",
  "bank_transfer": "Bank Transfer",
  "total_clients": "Total Clients",
  "active_clients": "Active Clients",
  "by_travel_type": "By Travel Type",
  "import": "Import",
  "export": "Export",
  "drag_drop": "Drag & drop file here",
  "or_click": "or click to browse",
  "template_en": "Template (EN)",
  "template_fr": "Template (FR)",
  "template_ar": "Template (AR)",
  "preview": "Preview",
  "confirm_import": "Confirm Import",
  "valid_rows": "Valid rows",
  "errors": "Errors",
  "processing": "Processing",
  "download": "Download",
  "xlsx": "Excel",
  "csv": "CSV",
  "pdf": "PDF",
  "page": "Page",
  "of": "of",
  "previous": "Previous",
  "next": "Next",
  "no_results": "No results found",
  "language": "Language",
  "english": "English",
  "french": "Français",
  "arabic": "العربية",
  "admin": "Admin",
  "agent": "Agent",
  "role": "Role",
  "full_name": "Full Name",
  "created_at": "Created At",
  "actions": "Actions",
  "code": "Code",
  "name": "Name",
  "is_active": "Active",
  "close": "Close",
  "retry": "Retry",
  "import_success": "Import completed successfully",
  "export_ready": "Export ready for download",
  "error_occurred": "An error occurred",
  "required_field": "This field is required",
  "duplicate_passport": "Passport number already exists",
  "filters": "Filters",
  "apply": "Apply",
  "reset": "Reset",
  "date_from": "From",
  "date_to": "To",
  "all": "All"
}```

#### fr.json
```json
{
  "app_name": "MinaDoor Travel DB",
  "login": "Connexion",
  "logout": "Déconnexion",
  "email": "Email",
  "password": "Mot de passe",
  "sign_in": "Se connecter",
  "dashboard": "Tableau de bord",
  "clients": "Clients",
  "travel_types": "Types de voyage",
  "users": "Utilisateurs",
  "settings": "Paramètres",
  "search": "Rechercher",
  "add_client": "Ajouter un client",
  "add_another": "+ Ajouter un autre",
  "save": "Enregistrer",
  "cancel": "Annuler",
  "edit": "Modifier",
  "delete": "Supprimer",
  "confirm_delete": "Êtes-vous sûr ?",
  "surname": "Nom",
  "given_name": "Prénom",
  "father_name": "Nom du père",
  "mother_name": "Nom de la mère",
  "passport_number": "N° Passeport",
  "nationality": "Nationalité",
  "date_of_birth": "Date de naissance",
  "passport_issue_date": "Date d'émission",
  "passport_expiry": "Date d'expiration",
  "gender": "Genre",
  "male": "Homme",
  "female": "Femme",
  "travel_type": "Type de voyage",
  "payment_method": "Mode de paiement",
  "travel_date": "Date de voyage",
  "status": "Statut",
  "notes": "Remarques",
  "active": "Actif",
  "completed": "Terminé",
  "cancelled": "Annulé",
  "cash": "Comptant",
  "instalment": "À tempérament",
  "bank_transfer": "Virement bancaire",
  "total_clients": "Total clients",
  "active_clients": "Clients actifs",
  "by_travel_type": "Par type de voyage",
  "import": "Importer",
  "export": "Exporter",
  "drag_drop": "Glisser-déposer le fichier ici",
  "or_click": "ou cliquer pour parcourir",
  "template_en": "Modèle (EN)",
  "template_fr": "Modèle (FR)",
  "template_ar": "Modèle (AR)",
  "preview": "Aperçu",
  "confirm_import": "Confirmer l'import",
  "valid_rows": "Lignes valides",
  "errors": "Erreurs",
  "processing": "Traitement",
  "download": "Télécharger",
  "xlsx": "Excel",
  "csv": "CSV",
  "pdf": "PDF",
  "page": "Page",
  "of": "sur",
  "previous": "Précédent",
  "next": "Suivant",
  "no_results": "Aucun résultat",
  "language": "Langue",
  "english": "English",
  "french": "Français",
  "arabic": "العربية",
  "admin": "Administrateur",
  "agent": "Agent",
  "role": "Rôle",
  "full_name": "Nom complet",
  "created_at": "Créé le",
  "actions": "Actions",
  "code": "Code",
  "name": "Nom",
  "is_active": "Actif",
  "close": "Fermer",
  "retry": "Réessayer",
  "import_success": "Import terminé avec succès",
  "export_ready": "Export prêt au téléchargement",
  "error_occurred": "Une erreur est survenue",
  "required_field": "Ce champ est obligatoire",
  "duplicate_passport": "Ce numéro de passeport existe déjà",
  "filters": "Filtres",
  "apply": "Appliquer",
  "reset": "Réinitialiser",
  "date_from": "Du",
  "date_to": "Au",
  "all": "Tous"
}```

## 8. Docker & Deployment
### Dockerfile (backend)
```dockerfile
# ── Stage 1: builder ─────────────────────────────────────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev libffi-dev libssl-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir --prefix=/install -r requirements.txt

# ── Stage 2: runtime ─────────────────────────────────────────────────────────
FROM python:3.11-slim AS runtime

# System libraries for weasyprint, magic
RUN apt-get update && apt-get install -y --no-install-recommends \
    libcairo2 libpango-1.0-0 libpangocairo-1.0-0 \
    libgdk-pixbuf-2.0-0 libmagic1 shared-mime-info wget \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy installed Python packages from builder
COPY --from=builder /install /usr/local

# Copy application code
COPY . .

# Non-root user for security
RUN addgroup --system appgroup && adduser --system --ingroup appgroup appuser
RUN mkdir -p /app/uploads /app/exports /tmp/exports && \
    chown -R appuser:appgroup /app /tmp/exports

USER appuser

# Entrypoint runs migrations then starts Gunicorn
ENTRYPOINT ["sh", "entrypoint.sh"]
```

### entrypoint.sh
```bash
#!/bin/sh
set -e

echo "[entrypoint] Running Alembic migrations..."
alembic upgrade head

echo "[entrypoint] Starting server..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## 9. Live System State
### Running Containers
```
NAMES                   STATUS                     PORTS
minadoordb_api_1        Exited (1) 2 minutes ago   
minadoordb_frontend_1   Up 24 minutes              0.0.0.0:80->80/tcp, [::]:80->80/tcp
minadoordb_db_1         Up 24 minutes (healthy)    5432/tcp
minadoordb_redis_1      Up 24 minutes (healthy)    6379/tcp
```

### API Container Logs (last 30 lines)
```
```

### Frontend Container Logs (last 10 lines)
```
172.19.0.1 - - [17/May/2026:13:19:25 +0000] "GET /api/v1/travel-types?lang=ar HTTP/1.1" 504 569 "http://localhost/" "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36" "-"
172.19.0.1 - - [17/May/2026:13:19:30 +0000] "GET /api/v1/clients?page=1&limit=50 HTTP/1.1" 504 569 "http://localhost/" "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36" "-"
172.19.0.1 - - [17/May/2026:13:19:33 +0000] "GET /api/v1/users HTTP/1.1" 504 569 "http://localhost/" "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36" "-"
172.19.0.1 - - [17/May/2026:13:19:40 +0000] "GET /api/v1/clients?page=1&limit=50 HTTP/1.1" 502 559 "http://localhost/" "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36" "-"
172.19.0.1 - - [17/May/2026:13:19:51 +0000] "GET /api/v1/travel-types?lang=ar HTTP/1.1" 504 569 "http://localhost/" "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36" "-"
```

## 10. API Quick Test
```
API unreachable

Travel types endpoint unreachable
```

## 11. Known Issues
5. Import/export backend not yet implemented; endpoints are stubs.

## 12. Enhancement Requests
- Provide clear instructions to replace the current frontend folder with the new build.
