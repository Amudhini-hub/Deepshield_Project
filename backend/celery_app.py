from celery import Celery

from backend.config.config import get_config

_config = get_config()
_broker = _config.get_celery_broker_url()

celery_app = Celery(
    "deepshield",
    broker=_broker,
    backend=_broker,
    include=["backend.tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    result_expires=3600,
)
