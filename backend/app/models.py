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

    clients = relationship("Client", back_populates="travel_type")

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
    travel_type = relationship("TravelType", back_populates="clients")

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
