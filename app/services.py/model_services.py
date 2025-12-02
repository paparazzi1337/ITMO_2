import pika
import json
from datetime import datetime
from models.model import BaseMLModel, MLModelStatus
from models.base_user import BaseUser
from typing import Dict

class ModelService:
    def __init__(self, db_session):
        self.db = db_session
        self.rabbit_connection = self._init_rabbitmq()
    
    def _init_rabbitmq(self):
        """Инициализация подключения к RabbitMQ"""
        connection = pika.BlockingConnection(
            pika.ConnectionParameters('rabbitmq'))
        channel = connection.channel()
        channel.queue_declare(queue='model_predictions', durable=True)
        return connection
    
    def create_model(self, model_data: Dict) -> BaseMLModel:
        model = BaseMLModel(
            model_id=model_data['model_id'],
            name=model_data['name'],
            owner_id=model_data['owner_id'],
            model_type=model_data.get('model_type', 'base'),
            model_path=model_data.get('model_path')
        )
        self.db.add(model)
        self.db.commit()
        return model
    
    def publish_prediction_task(self, model_id: str, input_data: Dict) -> str:
        """Публикация задачи на предсказание в RabbitMQ"""
        channel = self.rabbit_connection.channel()
        task_id = str(uuid.uuid4())
        
        channel.basic_publish(
            exchange='',
            routing_key='model_predictions',
            body=json.dumps({
                'task_id': task_id,
                'model_id': model_id,
                'input_data': input_data,
                'timestamp': datetime.utcnow().isoformat()
            }),
            properties=pika.BasicProperties(
                delivery_mode=2  # Сохранять сообщения при перезапуске
            )
        )
        return task_id
    
    def change_status(self, model: BaseMLModel, status: MLModelStatus) -> None:
        model.status = status
        self.db.commit()

class TensorFlowModelService:
    def __init__(self, model_path: str):
        self.model_path = model_path
        self._model = self._load_model()
    
    def _load_model(self):
        """Загрузка TensorFlow модели"""
        # Реальная реализация
        print(f"Loading TensorFlow model from {self.model_path}")
        return None
    
    def predict(self, input_data: Dict) -> Dict:
        """Выполнение предсказания"""
        return {"prediction": "sample_result"}