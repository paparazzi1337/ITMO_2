from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from ..schemas import UserCreate, UserResponse
from services.base_user_services import UserService
from database.database import get_session
from uuid import uuid4

router = APIRouter(prefix="/users")

@router.post("/", response_model=UserResponse)
async def create_user(
    request: Request,
    db: Session = Depends(get_session)
):
    form_data = await request.form()
    try:
        user_data = {
            'username': form_data.get('username'),
            'email': form_data.get('email'),
            'password': form_data.get('password'),
            'password_confirm': form_data.get('password_confirm')
        }
        
        # Валидация паролей
        if user_data['password'] != user_data['password_confirm']:
            raise HTTPException(status_code=400, detail="Пароли не совпадают")
        
        user_service = UserService(db)
        db_user = user_service.create_user({
            'username': user_data['username'],
            'email': user_data['email'],
            'password': user_data['password']
        })
        
        # Перенаправление после успешной регистрации
        return RedirectResponse(url="/login", status_code=303)
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))