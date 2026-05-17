from pydantic import BaseModel, field_validator, EmailStr, model_config
from typing import Optional, List
from datetime import date, datetime
import re


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    role: str = "agent"

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        errors = []
        if len(v) < 8:
            errors.append("at least 8 characters")
        if not re.search(r"[A-Z]", v):
            errors.append("one uppercase letter")
        if not re.search(r"[a-z]", v):
            errors.append("one lowercase letter")
        if not re.search(r"\d", v):
            errors.append("one digit")
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            errors.append("one special character")
        if errors:
            raise ValueError("Password requires: " + ", ".join(errors))
        return v

    @field_validator("role")
    @classmethod
    def valid_role(cls, v: str) -> str:
        if v not in ("admin", "agent"):
            raise ValueError("Role must be 'admin' or 'agent'")
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
        if v is not None and v.upper() not in ("M", "F"):
            raise ValueError("Gender must be M or F")
        return v.upper() if v else v

    @field_validator("passport_expiry")
    @classmethod
    def expiry_after_issue(cls, v: Optional[date], info) -> Optional[date]:
        issue = info.data.get("passport_issue_date")
        if v and issue and v < issue:
            raise ValueError("Expiry must be after issue date")
        return v

    @field_validator("payment_method")
    @classmethod
    def valid_payment(cls, v: str) -> str:
        allowed = {"cash", "card", "transfer", "instalment"}
        if v not in allowed:
            raise ValueError(f"payment_method must be one of {allowed}")
        return v


class ClientCreate(ClientBase):
    # travel_date validated at creation only
    @field_validator("travel_date")
    @classmethod
    def travel_not_past(cls, v: date) -> date:
        if v < date.today():
            raise ValueError("Travel date cannot be in the past")
        return v


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
    travel_date: Optional[date] = None  # No past-date check on update
    status: Optional[str] = None
    notes: Optional[str] = None

    @field_validator("gender")
    @classmethod
    def validate_gender(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v.upper() not in ("M", "F"):
            raise ValueError("Gender must be M or F")
        return v.upper() if v else v

    @field_validator("status")
    @classmethod
    def valid_status(cls, v: Optional[str]) -> Optional[str]:
        allowed = {"active", "completed", "cancelled", "pending"}
        if v and v not in allowed:
            raise ValueError(f"status must be one of {allowed}")
        return v


class ClientResponse(ClientBase):
    model_config = model_config = {"from_attributes": True}

    id: int
    created_at: datetime
    updated_at: datetime
    created_by: Optional[int] = None
    archived: bool
    status: str


class TravelTypeCreate(BaseModel):
    code: str
    name_en: str
    name_fr: str
    name_ar: str


class TravelTypeResponse(TravelTypeCreate):
    id: int
    is_active: bool

    model_config = {"from_attributes": True}


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

    model_config = {"from_attributes": True}


class ImportPreview(BaseModel):
    validation_id: str
    total_rows: int
    valid_rows: int
    errors: List[dict]


class ExportRequest(BaseModel):
    format: str = "xlsx"
    header_lang: str = "en"
    search: Optional[str] = None
    travel_type: Optional[str] = None
    status: Optional[str] = None
    gender: Optional[str] = None
    travel_date_from: Optional[str] = None
    travel_date_to: Optional[str] = None

    @field_validator("format")
    @classmethod
    def valid_format(cls, v: str) -> str:
        if v not in ("xlsx", "csv", "pdf"):
            raise ValueError("format must be xlsx, csv, or pdf")
        return v

    @field_validator("header_lang")
    @classmethod
    def valid_lang(cls, v: str) -> str:
        if v not in ("en", "fr", "ar"):
            raise ValueError("header_lang must be en, fr, or ar")
        return v


class ExportStatus(BaseModel):
    job_id: str
    status: str
    download_url: Optional[str] = None
    error: Optional[str] = None


class PaginatedClients(BaseModel):
    total: int
    page: int
    limit: int
    pages: int
    items: List[ClientResponse]
