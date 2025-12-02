import bcrypt
import re
from datetime import datetime
from models.base_user import BaseUser, UserRole
from typing import Optional

class UserService:
    def __init__(self, db_session):
        self.db = db_session
    
    @staticmethod
    def _hash_password(password: str) -> str:
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    @staticmethod
    def validate_email(email: str) -> bool:
        pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
        if not pattern.match(email):
            raise ValueError("Invalid email format")
        return True
    
    def create_user(self, user_data: dict) -> BaseUser:
        self.validate_email(user_data['email'])
        
        user = BaseUser(
            user_id=user_data['user_id'],
            username=user_data['username'],
            email=user_data['email'],
            password_hash=self._hash_password(user_data['password']),
            role=UserRole(user_data.get('role', 'regular'))
        )
        
        self.db.add(user)
        self.db.commit()
        return user
    
    def create_admin(self, username: str, email: str, password: str, **kwargs) -> BaseUser:
        return self.create_user({
            'username': username,
            'email': email,
            'password': password,
            'role': UserRole.ADMIN,
            **kwargs
    })
    
    def verify_user(self, username_or_email: str, password: str) -> Optional[BaseUser]:
        # Позволяем аутентификацию по email или username
        user = self.db.query(BaseUser).filter(
            (BaseUser.email == username_or_email) | 
            (BaseUser.username == username_or_email)
        ).first()
        
        if user and bcrypt.checkpw(password.encode('utf-8'), user.password_hash.encode('utf-8')):
            return user
        return None

class UserPermissionsService:
    @staticmethod
    def can_perform_action(user: BaseUser, action: str) -> bool:
        if user.role == UserRole.ADMIN:
            return True
        elif user.role == UserRole.MODEL_OWNER:
            return action in ["make_prediction", "view_history", "upload_model", "manage_model"]
        else:  # REGULAR
            return action in ["make_prediction", "view_history"]