from sqlalchemy import Column, BigInteger, String, Boolean, Date, DateTime, Text, ForeignKey, CHAR, SmallInteger, JSON, CheckConstraint, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(100), nullable=False)
    role = Column(String(20), default="agent")
    preferred_lang = Column(String(5), default="en")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class TravelType(Base):
    __tablename__ = "travel_types"
    id = Column(SmallInteger, primary_key=True, autoincrement=True)
    code = Column(String(30), unique=True, nullable=False)
    name_en = Column(String(100), nullable=False)
    name_fr = Column(String(100), nullable=False)
    name_ar = Column(String(100), nullable=False)
    is_active = Column(Boolean, default=True)

class Client(Base):
    __tablename__ = "clients"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    created_by = Column(BigInteger, ForeignKey("users.id"))
    surname = Column(String(100), nullable=False)
    given_name = Column(String(100), nullable=False)
    father_name = Column(String(100), nullable=False)
    mother_name = Column(String(100))
    passport_number = Column(String(30), nullable=False)
    nationality = Column(String(50), nullable=False)
    date_of_birth = Column(Date)
    passport_issue_date = Column(Date)
    passport_expiry = Column(Date)
    gender = Column(CHAR(1))
    travel_type_id = Column(SmallInteger, ForeignKey("travel_types.id"), nullable=False)
    payment_method = Column(String(30), default="cash")
    travel_date = Column(Date, nullable=False)
    status = Column(String(20), default="active")
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    archived = Column(Boolean, default=False)

    travel_type = relationship("TravelType")

    __table_args__ = (
        CheckConstraint("gender IN ('M','F')", name="check_gender"),
        Index("idx_clients_passport", "passport_number", postgresql_where=archived.is_(False)),
        Index("idx_clients_names", "surname", "given_name", "father_name", postgresql_using="gin", postgresql_ops={"surname": "gin_trgm_ops", "given_name": "gin_trgm_ops", "father_name": "gin_trgm_ops"}),
        Index("idx_clients_travel_type", "travel_type_id", postgresql_where=archived.is_(False)),
        Index("idx_clients_status", "status", postgresql_where=archived.is_(False)),
        Index("idx_clients_travel_date", "travel_date", postgresql_where=archived.is_(False)),
    )

class AuditLog(Base):
    __tablename__ = "audit_log"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger)
    action = Column(String(20))
    table_name = Column(String(50))
    record_id = Column(BigInteger)
    old_data = Column(JSON)
    new_data = Column(JSON)
    changed_at = Column(DateTime(timezone=True), server_default=func.now())
