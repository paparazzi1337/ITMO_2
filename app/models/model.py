from abc import ABC
from datetime import datetime
from enum import Enum
from typing import Dict
from sqlalchemy import Column, String, JSON, DateTime, Enum as SQLEnum, ForeignKey
from sqlalchemy.orm import relationship
from database.database import Base

class MLModelStatus(Enum):
    TRAINING = "training"
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"

class BaseMLModel(Base):
    __tablename__ = "models"

    model_id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    owner_id = Column(String, ForeignKey("users.user_id"), nullable=False)
    status = Column(SQLEnum(MLModelStatus), default=MLModelStatus.INACTIVE)
    created_at = Column(DateTime, default=datetime.utcnow)
    model_metadata = Column(JSON, default={})
    model_type = Column(String, nullable=False)
    model_path = Column(String)

    owner = relationship("BaseUser", back_populates="models")
    predictions = relationship("PredictionTask", back_populates="model", cascade="all, delete-orphan")