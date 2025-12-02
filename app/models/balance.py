from decimal import Decimal
from enum import Enum
from uuid import uuid4
from datetime import datetime
from sqlalchemy import Column, String, Numeric, Enum as SQLEnum, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from database.database import Base

class TransactionType(str, Enum):
    DEPOSIT = "deposit"
    WITHDRAWAL = "withdrawal"
    PAYMENT = "payment"
    REFUND = "refund"

class TransactionStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REVERSED = "reversed"

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(String, primary_key=True, default=lambda: f"tx_{uuid4().hex}")
    user_id = Column(String, ForeignKey("users.user_id"), nullable=False)
    amount = Column(Numeric(precision=20, scale=2), nullable=False)
    type = Column(SQLEnum(TransactionType), nullable=False)
    status = Column(SQLEnum(TransactionStatus), nullable=False)
    description = Column(String)
    error = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)

    user = relationship("BaseUser", back_populates="transactions")

class Balance(Base):
    __tablename__ = "balances"

    user_id = Column(String, ForeignKey("users.user_id"), primary_key=True)
    amount = Column(Numeric(precision=20, scale=2), default=Decimal('0'), nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("BaseUser", back_populates="balance")