from datetime import datetime
from typing import List, Optional

from sqlalchemy import select
from models.model import MLTask, MLTaskCreate, MLTaskUpdate, TaskStatus

class MLTaskService:
    def __init__(self, db_session):
        self.db = db_session  # Используем db как session

    def create(self, task_create: MLTaskCreate) -> MLTask:
        """Создает новую ML задачу"""
        task = MLTask(
            status=task_create.status,
            question=task_create.question,
            user_id=task_create.user_id
        )
        self.db.add(task)
        self.db.commit()
        self.db.refresh(task)
        return task

    def get(self, task_id: int):
        return self.db.query(MLTask).filter(MLTask.id == task_id).first()
    
    def get_user_tasks(self, user_id: str) -> List[MLTask]:
        """Получить все задачи пользователя"""
        return self.db.query(MLTask).filter(MLTask.user_id == user_id).order_by(MLTask.created_at).all()
    
    def get_chat_history(self, user_id: str):
        """Получить историю чата пользователя"""
        return self.db.query(MLTask).filter(
            MLTask.user_id == user_id
        ).order_by(MLTask.created_at).all()

    def get_all(self):
        return self.db.query(MLTask).all()

    def update(self, task_id: int, task_update: MLTaskUpdate) -> Optional[MLTask]:
        """Обновляет существующую задачу"""
        task = self.get(task_id)
        if not task:
            return None
        
        update_data = task_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(task, field, value)
        
        task.updated_at = datetime.utcnow()
        self.db.add(task)
        self.db.commit()
        self.db.refresh(task)
        return task

    def delete(self, task_id: int) -> bool:
        """Удаляет задачу по ID"""
        task = self.get(task_id)
        if not task:
            return False
        
        self.db.delete(task)
        self.db.commit()
        return True

    def set_status(self, task_id: int, status: TaskStatus) -> Optional[MLTask]:
        """Обновляет статус задачи"""
        return self.update(task_id, MLTaskUpdate(status=status))

    def set_result(self, task_id: int, result: str) -> Optional[MLTask]:
        """Устанавливает результат выполнения задачи"""
        return self.update(
            task_id, 
            MLTaskUpdate(
                status=TaskStatus.COMPLETED,
                result=result
            )
        )