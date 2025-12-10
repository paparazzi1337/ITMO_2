from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from database.config import get_settings
from typing import Generator

# Убедитесь, что используете правильный URL:
SQLALCHEMY_DATABASE_URL = "postgresql+psycopg2://user:password@database:5432/mydb"

engine = create_engine(
    url=SQLALCHEMY_DATABASE_URL,
    echo=True,         # Логирование SQL-запросов
    pool_size=5,       # Размер пула соединений
    max_overflow=10    # Максимальное количество соединений сверх pool_size
)

Base = declarative_base()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_session():
    """
    Генератор сессий для использования в зависимостях FastAPI
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_db() -> Generator[Session, None, None]:
    """
    Основной генератор сессий для зависимостей FastAPI
    (Типизированная версия с правильными аннотациями)
    """
    return get_session()

def init_db(drop_all: bool = False):
    """
    Инициализация базы данных - создание всех таблиц.
    
    Args:
        drop_all (bool): Если True, удаляет все таблицы перед созданием.
                         Используйте с осторожностью в production!
    """
    if drop_all:
        Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)