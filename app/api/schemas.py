from pydantic import BaseModel, EmailStr, ConfigDict, SecretStr
from datetime import datetime
from enum import Enum
from typing import Optional
from decimal import Decimal

# Auth schemas
class Token(BaseModel):
    access_token: str
    token_type: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

# User schemas
class UserRole(str, Enum):
    ADMIN = "admin"
    REGULAR = "regular"
    MODEL_OWNER = "model_owner"

class UserBase(BaseModel):
    email: EmailStr
    username: str

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    user_id: str
    role: UserRole
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

# Balance schemas
class TransactionType(str, Enum):
    DEPOSIT = "deposit"
    WITHDRAWAL = "withdrawal"
    PAYMENT = "payment"
    REFUND = "refund"

class TransactionCreate(BaseModel):
    amount: Decimal
    description: Optional[str] = None

class TransactionResponse(TransactionCreate):
    id: str
    user_id: str
    type: TransactionType
    status: str
    timestamp: datetime

    class Config:
        from_attributes = True

class BalanceResponse(BaseModel):
    amount: Decimal
    updated_at: datetime

    class Config:
        from_attributes = True

# Model schemas
class TaskStatus(str, Enum):
    """Дублируем enum для статусов, если он нужен в схемах"""
    NEW = "new"
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class MLTaskCreate(BaseModel):
    """DTO для создания ML задачи"""
    question: str
    user_id: str
    status: TaskStatus = TaskStatus.NEW

class MLTaskUpdate(BaseModel):
    """DTO для обновления ML задачи"""
    status: Optional[TaskStatus] = None
    result: Optional[str] = None

class MLTaskResponse(BaseModel):
    """Схема для ответа с данными задачи"""
    id: str
    question: str
    status: TaskStatus
    result: Optional[str] = None
    user_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
        

# Prediction schemas
class PredictionStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"

class PredictionCreate(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    model_id: str
    input_data: dict

class PredictionResponse(PredictionCreate):
    task_id: str
    user_id: str
    status: PredictionStatus
    created_at: datetime
    result: Optional[dict] = None
    error: Optional[str] = None

    class Config:
        from_attributes = True