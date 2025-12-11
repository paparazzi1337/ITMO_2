from contextlib import asynccontextmanager
from datetime import datetime
from fastapi import Depends, FastAPI, APIRouter, Form, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
import logging
from typing import AsyncGenerator, Optional

# Импорт моделей и сервисов
from services.model_services import MLTaskService
from services.base_user_services import UserService
from models.base_user import BaseUser
from services.balance_services import BalanceService
from database.database import get_session, init_db
from api.routers.auth import router as auth_router
from api.routers.users import router as users_router
from api.routers.balance import router as balance_router
from api.routers.models import ml_route as models_router, send_task_rpc
from api.routers.predictions import router as predictions_router
from api.dependencies import get_current_user
from core.templates import templates

# Настройка логгера
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Управление жизненным циклом приложения"""
    try:
        init_db(drop_all=True)  # Инициализация БД
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Database initialization failed: {str(e)}")
        raise
    yield
    logger.info("Application shutdown")

def create_app() -> FastAPI:
    app = FastAPI(
        title="ML Prediction Service",
        version="1.0.0",
        description="API для управления ML-моделями и балансом пользователей",
        lifespan=lifespan
    )

    # Настройка middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Подключение статических файлов
    app.mount("/static", StaticFiles(directory="/app/static"), name="static")

    # Подключение API роутеров
    api_router = APIRouter()
    api_router.include_router(auth_router)
    api_router.include_router(users_router, tags=["users"])
    api_router.include_router(balance_router)
    api_router.include_router(models_router)
    api_router.include_router(predictions_router)
    app.include_router(api_router, prefix="/api")

    return app

app = create_app()

async def get_current_user_from_request(request: Request) -> Optional[BaseUser]:
    """Получение текущего пользователя для шаблонов"""
    try:
        db = next(get_session())
        return await get_current_user(request, db)
    except Exception:
        return None

# HTML роуты
@app.get("/", response_class=HTMLResponse)
async def home(request: Request, db: Session = Depends(get_session)):
    try:
        current_user = await get_current_user(request, db)
        return templates.TemplateResponse(
            "index.html",
            {"request": request, "current_user": current_user}
        )
    except HTTPException:
        return templates.TemplateResponse(
            "index.html",
            {"request": request, "current_user": None}
        )

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request, error: str = None):
    return templates.TemplateResponse(
        "login.html",
        {"request": request, "error": error}
    )

@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request, error: str = None):
    return templates.TemplateResponse(
        "register.html",
        {"request": request, "error": error}
    )

@app.post("/register")
async def handle_register(
    request: Request,
    db: Session = Depends(get_session)
):
    try:
        form_data = await request.form()
        user_data = {
            'username': form_data.get('username'),
            'email': form_data.get('email'),
            'password': form_data.get('password'),
            'password_confirm': form_data.get('password_confirm')
        }
        
        # Проверка паролей
        if user_data['password'] != user_data['password_confirm']:
            return templates.TemplateResponse(
                "register.html",
                {"request": request, "error": "Пароли не совпадают"},
                status_code=400
            )
        
        user_service = UserService(db)
        user_service.create_user(user_data)
        
        return RedirectResponse("/login", status_code=303)
        
    except ValueError as e:
        return templates.TemplateResponse(
            "register.html",
            {"request": request, "error": str(e)},
            status_code=400
        )

@app.get("/balance", response_class=HTMLResponse)
async def balance_page(
    request: Request,
    current_user: BaseUser = Depends(get_current_user),
    db: Session = Depends(get_session)
):
    balance_service = BalanceService(db)
    
    return templates.TemplateResponse(
        "balance.html",
        {
            "request": request,
            "current_user": current_user,
            "transactions": balance_service.get_transaction_history(current_user.user_id),
            "now": datetime.now  # Добавляем функцию now в контекст шаблона
        }
    )

@app.post("/login")
async def handle_login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_session)
):
    try:
        # Здесь должна быть ваша логика аутентификации
        # Например:
        user_service = UserService(db)
        user = user_service.verify_user(username, password)
        if not user:
            raise ValueError("Invalid credentials")
        
        response = RedirectResponse("/", status_code=303)
        # Установка кук и т.д.
        return response
    except Exception as e:
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": str(e)},
            status_code=400
        )
    
@app.get("/chat", response_class=HTMLResponse)
async def chat_page(
    request: Request,
    current_user: BaseUser = Depends(get_current_user),
    db: Session = Depends(get_session)
):
    if not current_user:
        return RedirectResponse("/login", status_code=303)
    
    mltask_service = MLTaskService(db)
    tasks = mltask_service.get_chat_history(current_user.user_id)
    
    responses = []
    for task in tasks:
        responses.append({
            "original": task.question,
            "processed": task.result,
            "timestamp": task.created_at.strftime('%d.%m.%Y %H:%M')  # Используем время из задачи
        })
    
    return templates.TemplateResponse(
        "chat.html",
        {
            "request": request,
            "current_user": current_user,
            "responses": responses,
            "now": datetime.now  # Добавляем функцию now в контекст
        }
    )

@app.post("/chat", response_class=HTMLResponse)
async def handle_chat(
    request: Request,
    message: str = Form(...),
    user_id: str = Form(...),
    current_user: BaseUser = Depends(get_current_user),
    db: Session = Depends(get_session)
):
    if not current_user:
        return RedirectResponse("/login", status_code=303)

    # Проверяем баланс
    balance_service = BalanceService(db)
    if current_user.balance.amount < 10:
        mltask_service = MLTaskService(db)
        tasks = mltask_service.get_chat_history(current_user.user_id)
        responses = [
            {
                "original": task.question,
                "processed": task.result,
                "timestamp": task.created_at.strftime('%d.%m.%Y %H:%M')
            } for task in tasks
        ]
        
        return templates.TemplateResponse(
            "chat.html",
            {
                "request": request,
                "current_user": current_user,
                "responses": responses,
                "error": "Недостаточно средств на балансе"
            },
            status_code=400
        )

    try:
        # Списываем средства
        balance_service.withdraw(current_user.user_id, 10, "Оплата запроса к модели")

        # Отправляем запрос к модели
        mltask_service = MLTaskService(db)
        response = await send_task_rpc(
            message=message,
            user_id=user_id,
            mltask_service=mltask_service
        )

        # Перенаправляем на GET /chat чтобы обновить историю
        return RedirectResponse("/chat", status_code=303)

    except HTTPException as e:
        # Возвращаем средства при ошибке
        balance_service.deposit(current_user.user_id, 10, "Возврат средств за невыполненный запрос")
        
        # Получаем текущую историю
        tasks = mltask_service.get_chat_history(current_user.user_id)
        responses = [
            {
                "original": task.question,
                "processed": task.result,
                "timestamp": task.created_at.strftime('%d.%m.%Y %H:%M')
            } for task in tasks
        ]
        
        return templates.TemplateResponse(
            "chat.html",
            {
                "request": request,
                "current_user": current_user,
                "responses": responses,
                "error": str(e.detail)
            },
            status_code=400
        )

@app.get("/health")
async def health_check():
    return {"status": "OK"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api_main:app", host="0.0.0.0", port=8000, reload=True)