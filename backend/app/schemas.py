from pydantic import BaseModel, field_validator, EmailStr, ConfigDict, ValidationInfo
from typing import Optional, List
from datetime import date
import re

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    role: str = "agent"

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
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

    @field_validator("gender")
    @classmethod
    def validate_gender(cls, v: Optional[str]) -> Optional[str]:
        if v and v.upper() not in ("M", "F"):
            raise ValueError("Gender must be M or F")
        return v.upper() if v else v

    @field_validator("passport_expiry")
    @classmethod
    def expiry_after_issue(cls, v: Optional[date], info: ValidationInfo) -> Optional[date]:
        if v and info.data.get("passport_issue_date") and v < info.data["passport_issue_date"]:
            raise ValueError("Expiry must be after issue date")
        return v

    @field_validator("travel_date")
    @classmethod
    def travel_not_past(cls, v: date) -> date:
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

    model_config = ConfigDict(from_attributes=True)

class TravelTypeCreate(BaseModel):
    code: str
    name_en: str
    name_fr: str
    name_ar: str

class TravelTypeResponse(TravelTypeCreate):
    id: int
    is_active: bool

    model_config = ConfigDict(from_attributes=True)

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

    model_config = ConfigDict(from_attributes=True)

class PaginatedClients(BaseModel):
    total: int
    page: int
    limit: int
    pages: int
    items: list[ClientResponse]

class ExportStatus(BaseModel):
    job_id: str
    status: str
    error: Optional[str] = None
    download_url: Optional[str] = None

class ExportRequest(BaseModel):
    format: str
    search: Optional[str] = None
    travel_type: Optional[str] = None
    status: Optional[str] = None
    gender: Optional[str] = None
    travel_date_from: Optional[date] = None
    travel_date_to: Optional[date] = None
    header_lang: str = "en"

class ImportPreview(BaseModel):
    validation_id: str
    total_rows: int
    valid_rows: int
    errors: List[dict]
    preview_data: List[dict] = []

class ImportConfirmRequest(BaseModel):
    rows: list[ClientCreate]
    validation_id: str | None = None
