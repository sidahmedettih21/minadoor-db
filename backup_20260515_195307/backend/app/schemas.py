from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List, Dict, Any
from datetime import date, datetime
import re

# Auth
class Token(BaseModel):
    access_token: str
    refresh_token: str
    expires_in: int
    token_type: str = "bearer"

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class RefreshRequest(BaseModel):
    refresh_token: str

class UserOut(BaseModel):
    id: int
    email: str
    full_name: str
    role: str
    preferred_lang: str
    is_active: bool
    class Config:
        from_attributes = True

class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6)
    full_name: str = Field(..., min_length=2, max_length=100)
    role: str = "agent"
    preferred_lang: str = "en"

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    role: Optional[str] = None
    preferred_lang: Optional[str] = None
    is_active: Optional[bool] = None

# Travel Types
class TravelTypeOut(BaseModel):
    id: int
    code: str
    name: str  # localized
    name_en: str
    name_fr: str
    name_ar: str
    is_active: bool
    class Config:
        from_attributes = True

class TravelTypeCreate(BaseModel):
    code: str = Field(..., max_length=30)
    name_en: str = Field(..., max_length=100)
    name_fr: str = Field(..., max_length=100)
    name_ar: str = Field(..., max_length=100)

class TravelTypeUpdate(BaseModel):
    name_en: Optional[str] = None
    name_fr: Optional[str] = None
    name_ar: Optional[str] = None
    is_active: Optional[bool] = None

# Clients
class ClientBase(BaseModel):
    surname: str = Field(..., max_length=100)
    given_name: str = Field(..., max_length=100)
    father_name: str = Field(..., max_length=100)
    mother_name: Optional[str] = Field(None, max_length=100)
    passport_number: str = Field(..., max_length=30)
    nationality: str = Field(..., max_length=50)
    date_of_birth: Optional[date] = None
    passport_issue_date: Optional[date] = None
    passport_expiry: Optional[date] = None
    gender: Optional[str] = Field(None)
    travel_type_id: int
    payment_method: str = "cash"
    travel_date: date
    status: str = "active"
    notes: Optional[str] = None

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

class ClientOut(ClientBase):
    id: int
    created_by: Optional[int]
    created_at: datetime
    updated_at: datetime
    archived: bool
    travel_type: Optional[TravelTypeOut] = None
    class Config:
        from_attributes = True

class ClientListResponse(BaseModel):
    items: List[ClientOut]
    total: int
    page: int
    limit: int

# Import
class ImportError(BaseModel):
    row: int
    field: str
    error: str

class ImportPreview(BaseModel):
    validation_id: str
    total_rows: int
    valid_rows: int
    errors: List[ImportError]
    preview_data: List[Dict[str, Any]]

class ImportConfirm(BaseModel):
    rows: List[Dict[str, Any]]

class ImportResult(BaseModel):
    imported_count: int
    duplicates_skipped: int

# Export
class ExportRequest(BaseModel):
    format: str = Field(..., pattern=r"^(xlsx|csv|pdf)$")
    search: Optional[str] = None
    travel_type: Optional[str] = None
    status: Optional[str] = None
    travel_date_from: Optional[date] = None
    travel_date_to: Optional[date] = None
    gender: Optional[str] = None
    header_lang: str = "en"

class ExportStatus(BaseModel):
    job_id: str
    status: str  # processing, completed, failed
    download_url: Optional[str] = None

# Health
class HealthCheck(BaseModel):
    status: str
    db: str
    redis: str
