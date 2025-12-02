from datetime import datetime
from enum import Enum
from sqlalchemy import Column, String, JSON, DateTime, Enum as SQLEnum, ForeignKey
from sqlalchemy.orm import relationship
from database.database import Base


class PredictionStatus(Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"

class PredictionTask(Base):
    __tablename__ = "predictions"

    task_id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.user_id"))
    model_id = Column(String, ForeignKey("models.model_id"))
    input_data = Column(JSON)
    status = Column(SQLEnum(PredictionStatus), default=PredictionStatus.PENDING)
    created_at = Column(DateTime, default=datetime.utcnow)
    result = Column(JSON)
    error = Column(String)
    
    user = relationship("BaseUser", back_populates="predictions")
    model = relationship("BaseMLModel", back_populates="predictions")