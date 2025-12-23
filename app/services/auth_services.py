from jose import jwt
from datetime import datetime, timedelta
from database.config import settings
from typing import Dict, Any, Optional

class AuthService:
    @staticmethod
    def create_access_token(data: Dict[str, Any]) -> str:
        """
        Создает JWT токен
        Args:
            data: Данные для включения в токен (обычно {"sub": username})
        Returns:
            str: Закодированный JWT токен
        """
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode.update({"exp": expire})
        return jwt.encode(
            to_encode,
            settings.SECRET_KEY,
            algorithm=settings.ALGORITHM
        )

    @staticmethod
    def verify_token(token: str) -> Optional[Dict[str, Any]]:
        """
        Верифицирует JWT токен
        Args:
            token: JWT токен для проверки
        Returns:
            Dict: Декодированные данные токена или None если невалидный
        """
        try:
            return jwt.decode(
                token,
                settings.SECRET_KEY,
                algorithms=[settings.ALGORITHM]
            )
        except jwt.JWTError:
            return None