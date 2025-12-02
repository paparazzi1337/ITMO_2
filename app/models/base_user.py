from datetime import datetime
from enum import Enum
from sqlalchemy import Column, String, Boolean, DateTime, Enum as SQLEnum
from sqlalchemy.orm import relationship
from database.database import Base

class UserRole(str, Enum):
    ADMIN = "admin"
    REGULAR = "regular"
    MODEL_OWNER = "model_owner"

class BaseUser(Base):
    __tablename__ = "users"

    user_id = Column("user_id", String, primary_key=True)
    username = Column("username", String, unique=True, nullable=False)
    email = Column("email", String, unique=True, nullable=False)
    password = Column("password", String, nullable=False)
    password_hash = Column("password_hash", String, nullable=False)
    role = Column("role", SQLEnum(UserRole), nullable=False)
    created_at = Column("created_at", DateTime, default=datetime.now)
    is_active = Column("is_active", Boolean, default=True)

    balance = relationship("Balance", back_populates="user", uselist=False, cascade="all, delete-orphan")
    transactions = relationship("Transaction", back_populates="user", cascade="all, delete-orphan")
    predictions = relationship("PredictionTask", back_populates="user", cascade="all, delete-orphan")
    models = relationship("BaseMLModel", back_populates="owner", cascade="all, delete-orphan")