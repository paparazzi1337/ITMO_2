from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from fastapi.responses import RedirectResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import jwt, JWTError
from sqlalchemy.orm import Session
from datetime import timedelta

from database.database import get_session
from database.config import settings
from models.base_user import BaseUser
from ..schemas import Token
from services.auth_services import AuthService
from services.base_user_services import UserService
from core.templates import templates

router = APIRouter(
    prefix="/auth",
    tags=["auth"]
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login", scheme_name="BearerAuth")

@router.post("/login", response_model=Token)
async def login_for_access_token(
    response: Response,
    request: Request,
    db: Session = Depends(get_session)
):
    form_data = await request.form()
    username = form_data.get("username")
    password = form_data.get("password")
    
    user_service = UserService(db)
    user = user_service.verify_user(username, password)
    
    if not user:
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "Неверное имя пользователя или пароль"},
            status_code=400
        )
    
    access_token = AuthService.create_access_token(
        data={"sub": user.username, "user_id": str(user.user_id)}
    )
    
    # Устанавливаем куку для веб-интерфейса
    response = RedirectResponse(url="/", status_code=303)
    response.set_cookie(
        key="access_token",
        value=f"Bearer {access_token}",
        httponly=True,
        max_age=1800,  # 30 минут
        secure=False,  # True в production (HTTPS)
        samesite="lax",
        path="/",
    )
    
    return response

@router.post("/logout")
async def logout(request: Request):
    response = RedirectResponse(url="/", status_code=303)
    response.delete_cookie(
        key="access_token",
        path="/",
    )
    return response

async def get_current_user(
    request: Request,
    db: Session = Depends(get_session)
) -> BaseUser:
    """Получение текущего пользователя из куки"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Не удалось подтвердить учетные данные",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    token = request.cookies.get("access_token")
    if not token:
        raise credentials_exception
    
    try:
        # Удаляем префикс "Bearer "
        token = token.replace("Bearer ", "")
        payload = AuthService.verify_token(token)
        if payload is None:
            raise credentials_exception
            
        username: str = payload.get("sub")
        user_id: str = payload.get("user_id")
        if username is None or user_id is None:
            raise credentials_exception
            
    except (JWTError, AttributeError):
        raise credentials_exception
    
    user = UserService(db).get_by_username(username)
    if user is None or str(user.user_id) != user_id:
        raise credentials_exception
        
    return user