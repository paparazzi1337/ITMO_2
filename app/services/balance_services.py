from decimal import Decimal
from typing import List, Dict
import threading
from sqlalchemy.orm import Session
from models.balance import Transaction, Balance, TransactionType, TransactionStatus
from models.base_user import BaseUser

class InsufficientFundsError(Exception):
    pass

class TransactionNotFoundError(Exception):
    pass

class BalanceService:
    def __init__(self, db: Session):
        self.db = db
        self._lock = threading.Lock()

    def get_balance(self, user: BaseUser) -> Decimal:
        balance = self.db.query(Balance).filter(Balance.user_id == user.user_id).first()
        return balance.amount if balance else Decimal('0')

    def deposit(self, user: BaseUser, amount: Decimal, description: str = "") -> str:
        if amount <= Decimal('0'):
            raise ValueError("Amount must be positive")

        with self._lock:
            transaction = Transaction(
                user_id=user.user_id,
                amount=amount,
                type=TransactionType.DEPOSIT,
                status=TransactionStatus.PENDING,
                description=description
            )
            self.db.add(transaction)

            balance = self.db.query(Balance).filter(Balance.user_id == user.user_id).first()
            if not balance:
                balance = Balance(user_id=user.user_id, amount=Decimal('0'))
                self.db.add(balance)

            balance.amount += amount
            transaction.status = TransactionStatus.COMPLETED
            self.db.commit()
            return transaction.id

    def withdraw(self, user_id: str, amount: Decimal, description: str = "") -> str:
        if amount <= Decimal('0'):
            raise ValueError("Amount must be positive")

        with self._lock:
            balance = self.db.query(Balance).filter(Balance.user_id == user_id).first()
            if not balance or balance.amount < amount:
                raise InsufficientFundsError("Insufficient funds")

            transaction = Transaction(
                user_id=user_id,
                amount=amount,
                type=TransactionType.WITHDRAWAL,
                status=TransactionStatus.PENDING,
                description=description
            )
            self.db.add(transaction)

            balance.amount -= amount
            transaction.status = TransactionStatus.COMPLETED
            self.db.commit()
            return transaction.id

    def make_payment(self, user_id: str, amount: Decimal, service_name: str, reference_id: str = None) -> str:
        description = f"Payment for {service_name}"
        if reference_id:
            description += f" (ref: {reference_id})"
        
        return self.withdraw(
            user_id=user_id,
            amount=amount,
            description=description
        )

    def get_transaction_history(self, user_id: str) -> List[Dict]:
        transactions = self.db.query(Transaction)\
            .filter(Transaction.user_id == user_id)\
            .order_by(Transaction.timestamp.desc())\
            .all()
        
        return [{
            'id': tx.id,
            'user_id': tx.user_id,
            'amount': tx.amount,
            'type': tx.type,
            'description': tx.description,
            'status': tx.status,
            'timestamp': tx.timestamp.strftime('%d.%m.%Y %H:%M')
        } for tx in transactions]

    def get_transaction(self, transaction_id: str) -> Dict:
        transaction = self.db.query(Transaction)\
            .filter(Transaction.id == transaction_id)\
            .first()
        
        if not transaction:
            raise TransactionNotFoundError(f"Transaction {transaction_id} not found")
        
        return {
            'id': transaction.id,
            'user_id': transaction.user_id,
            'amount': transaction.amount,
            'type': transaction.type,
            'status': transaction.status,
            'description': transaction.description,
            'timestamp': transaction.timestamp.isoformat()
        }