import uuid
import re
import bcrypt
from datetime import datetime
from typing import Optional, Dict
from models.base_user import BaseUser, UserRole
from pydantic import EmailStr, ValidationError
from sqlalchemy.exc import SQLAlchemyError

class UserService:
    def __init__(self, db_session):
        self.db = db_session
    
    @staticmethod
    def _hash_password(password: str) -> str:
        """Генерация безопасного хэша пароля с солью"""
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """Валидация email через регулярное выражение"""
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
            raise ValueError("Invalid email format")
        return True
    
    def create_user(self, user_data: Dict) -> BaseUser:
        """
        Создание нового пользователя с проверкой уникальности
        
        Args:
            user_data: {
                'username': str,
                'email': str,
                'password': str,
                'role?': str (default: 'regular')
            }
        
        Returns:
            BaseUser: созданный пользователь
        
        Raises:
            ValueError: при ошибках валидации, существующем пользователе или сохранения
        """
        try:
            # Валидация email
            self.validate_email(user_data['email'])
            
            # Проверка существующего пользователя
            existing_user = self.db.query(BaseUser).filter(
                (BaseUser.username == user_data['username']) | 
                (BaseUser.email == user_data['email'])
            ).first()
            
            if existing_user:
                error_fields = []
                if existing_user.username == user_data['username']:
                    error_fields.append(f"username '{user_data['username']}'")
                if existing_user.email == user_data['email']:
                    error_fields.append(f"email '{user_data['email']}'")
                raise ValueError(f"User with {' and '.join(error_fields)} already exists")

            # Валидация и нормализация роли
            role_str = user_data.get('role', 'regular').lower()
            try:
                role = UserRole(role_str)
            except ValueError:
                valid_roles = [e.value for e in UserRole]
                raise ValueError(f"Invalid role '{role_str}'. Valid roles: {valid_roles}")
            
            # Создание пользователя
            user = BaseUser(
                user_id=str(uuid.uuid4()),
                username=user_data['username'],
                email=user_data['email'],
                password_hash=self._hash_password(user_data['password']),
                role=role,
                created_at=datetime.utcnow(),
                is_active=True
            )
            
            self.db.add(user)
            self.db.commit()
            return user
            
        except SQLAlchemyError as e:
            self.db.rollback()
            raise ValueError(f"Database error: {str(e)}")
        except Exception as e:
            self.db.rollback()
            raise ValueError(f"User creation failed: {str(e)}")
    
    def create_admin(self, username: str, email: str, password: str) -> BaseUser:
        """Создание пользователя с ролью ADMIN"""
        return self.create_user({
            'username': username,
            'email': email,
            'password': password,
            'role': UserRole.ADMIN.value
        })
    
    def get_by_username(self, username: str) -> BaseUser | None:
        return self.db.query(BaseUser).filter(BaseUser.username == username).first()

    def get_by_email(self, email: str) -> BaseUser | None:
        return self.db.query(BaseUser).filter(BaseUser.email == email).first()
    
    def verify_user(self, username_or_email: str, password: str) -> Optional[BaseUser]:
        """
        Проверка учетных данных пользователя
        Returns:
            BaseUser: если аутентификация успешна
            None: если пользователь не найден или пароль неверный
        """
        try:
            user = self.db.query(BaseUser).filter(
                (BaseUser.email == username_or_email) | 
                (BaseUser.username == username_or_email)
            ).first()
            
            if user and self._check_password(password, user.password_hash):
                self.db.commit()
                return user
            return None
        except Exception:
            self.db.rollback()
            raise
    
    @staticmethod
    def _check_password(password: str, hashed: str) -> bool:
        """Безопасное сравнение пароля с хэшем"""
        try:
            return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
        except (ValueError, TypeError):
            return False

class UserPermissionsService:
    """Сервис для проверки прав пользователя"""
    
    PERMISSIONS = {
        UserRole.ADMIN: ["*"],
        UserRole.MODEL_OWNER: [
            "make_prediction", 
            "view_history",
            "upload_model",
            "manage_model"
        ],
        UserRole.REGULAR: [
            "make_prediction",
            "view_history"
        ]
    }
    
    @classmethod
    def can_perform_action(cls, user: BaseUser, action: str) -> bool:
        """Проверка наличия прав у пользователя"""
        if not user or not user.is_active:
            return False
            
        permissions = cls.PERMISSIONS.get(user.role, [])
        return "*" in permissions or action in permissions