from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from database.database import get_session
from models.base_user import BaseUser
from services.base_user_services import UserService
from services.auth_services import AuthService

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

async def get_current_user(
    request: Request,
    db: Session = Depends(get_session)
) -> BaseUser:
    """Альтернатива для API-запросов с заголовком Authorization"""
    token = None
    
    # Проверяем куки (для веб-интерфейса)
    if not token:
        token = request.cookies.get("access_token")
    
    # Проверяем заголовок Authorization (для API)
    if not token and request.headers.get("Authorization"):
        try:
            token = request.headers["Authorization"].split(" ")[1]
        except IndexError:
            pass
    
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Требуется аутентификация",
        )
    
    # Удаляем "Bearer " если есть
    token = token.replace("Bearer ", "")
    
    payload = AuthService.verify_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Недействительный токен",
        )
    
    username = payload.get("sub")
    user_id = payload.get("user_id")
    if not username or not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Недействительные данные токена",
        )
    
    user = UserService(db).get_by_username(username)
    if not user or str(user.user_id) != user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Пользователь не найден",
        )
    
    return user