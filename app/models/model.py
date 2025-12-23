from datetime import datetime
from enum import Enum
from typing import Optional, TYPE_CHECKING
import uuid
from pydantic import BaseModel
from sqlalchemy import Column, String, Integer, DateTime, Enum as SQLEnum, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database.database import Base

if TYPE_CHECKING:
    from models.base_user import BaseUser

class TaskStatus(str, Enum):
    """Статусы выполнения ML задачи"""
    NEW = "new"
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

# SQLAlchemy ORM модели
class MLTaskBase(Base):
    __abstract__ = True
    status = Column(SQLEnum(TaskStatus), default=TaskStatus.NEW)
    result = Column(String, nullable=True)
    question = Column(String, nullable=True)
    
class MLTask(MLTaskBase):
    __tablename__ = "ml_tasks"  # Изменил имя таблицы на более конкретное

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey('users.user_id'))
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    owner = relationship("BaseUser", back_populates="ml_tasks")

    def to_queue_message(self) -> dict:
        return {
            "task_id": self.id,
            "question": self.question,
        }

# Pydantic DTO модели (отдельно от ORM)
class MLTaskCreate(BaseModel):
    question: str
    user_id: str
    status: TaskStatus = TaskStatus.NEW  # Значение по умолчанию

class MLTaskUpdate(BaseModel):
    status: Optional[TaskStatus] = None
    result: Optional[str] = None