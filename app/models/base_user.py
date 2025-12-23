from datetime import datetime
from enum import Enum
from sqlalchemy import UUID, Column, Integer, String, Boolean, DateTime, Enum as SQLEnum
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
    password = Column('password', String(255))
    role = Column("role", SQLEnum(UserRole), nullable=False)
    created_at = Column("created_at", DateTime, default=datetime.now)
    is_active = Column("is_active", Boolean, default=True)

    balance = relationship("Balance", back_populates="user", uselist=False, cascade="all, delete-orphan")
    transactions = relationship("Transaction", back_populates="user", cascade="all, delete-orphan")
    predictions = relationship("PredictionTask", back_populates="user", cascade="all, delete-orphan")
    ml_tasks = relationship("MLTask", back_populates="owner", cascade="all, delete-orphan")

    @property
    def password_hash(self):
        return self.password
        
    @password_hash.setter
    def password_hash(self, value):
        self.password = value