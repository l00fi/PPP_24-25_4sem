from app.celery.celery_app import celery
from app.core.config import Settings
from redis import Redis

import time
import json


redis_client = Redis(host=Settings.REDIS_HOST, port=Settings.REDIS_PORT)

@celery.task(bind=True)
def long_running_task(self, user_id: int):
    # Отправка уведомления о старте
    redis_client.publish(
        f"task_{self.request.id}",
        json.dumps({
            "status": "STARTED",
            "task_id": self.request.id,
            "message": "Задача началась"
        })
    )
    
    # Имитация прогресса
    for i in range(1, 3):
        time.sleep(0.5)
        redis_client.publish(
            f"task_{self.request.id}",
            json.dumps({
                "status": "PROGRESS",
                "task_id": self.request.id,
                "progress": i
            })
        )
    
    # Уведомление о завершении
    redis_client.publish(
        f"task_{self.request.id}",
        json.dumps({
            "status": "COMPLETED",
            "task_id": self.request.id,
            "result": "success"
        })
    )