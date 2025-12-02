from typing import Dict, List
from sqlalchemy.orm import Session
from models.prediction_history import PredictionTask, PredictionStatus
from models.base_user import BaseUser
from models.model import BaseMLModel

class PredictionService:
    def __init__(self, db: Session):
        self.db = db

    def create_task(self, task_data: Dict) -> PredictionTask:
        task = PredictionTask(
            task_id=task_data['task_id'],
            user_id=task_data['user_id'],
            model_id=task_data['model_id'],
            input_data=task_data['input_data']
        )
        self.db.add(task)
        self.db.commit()
        return task

    def complete_task(self, task_id: str, result: Dict) -> None:
        task = self.db.query(PredictionTask).filter(PredictionTask.task_id == task_id).first()
        if task:
            task.status = PredictionStatus.COMPLETED
            task.result = result
            self.db.commit()

    def fail_task(self, task_id: str, error: str) -> None:
        task = self.db.query(PredictionTask).filter(PredictionTask.task_id == task_id).first()
        if task:
            task.status = PredictionStatus.FAILED
            task.error = error
            self.db.commit()

    def get_user_history(self, user: BaseUser) -> List[PredictionTask]:
        return self.db.query(PredictionTask)\
            .filter(PredictionTask.user_id == user.user_id)\
            .order_by(PredictionTask.created_at.desc())\
            .all()

    def get_model_history(self, model: BaseMLModel) -> List[PredictionTask]:
        return self.db.query(PredictionTask)\
            .filter(PredictionTask.model_id == model.model_id)\
            .order_by(PredictionTask.created_at.desc())\
            .all()