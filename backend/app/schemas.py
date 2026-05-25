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
    preview_data: List[dict] = []

class ImportConfirmRequest(BaseModel):
    rows: list[ClientCreate]
    validation_id: str | None = None
