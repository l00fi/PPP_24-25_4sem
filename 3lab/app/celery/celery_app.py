from app.core.config import Settings
from celery import Celery

# Эта канал для уведомлений 
REDIS_BROKER = f"redis://{Settings.REDIS_HOST}:{Settings.REDIS_PORT}/0"
# Это канал где выполняются тяжелые процессы
REDIS_BACKEND = f"redis://{Settings.REDIS_HOST}:{Settings.REDIS_PORT}/1"

celery_app = Celery(
    "lab3",
    broker=REDIS_BROKER,
    backend=REDIS_BACKEND,
)

# Определяю то, в каком формате отправлять и принимать запросы
celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    result_expires=3600,
)

# Передаю все "тяжелые" процессы которые выполняются на celery + redis
celery_app.autodiscover_tasks(['app.celery.tasks'])