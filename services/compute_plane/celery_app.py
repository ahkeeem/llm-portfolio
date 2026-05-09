from celery import Celery
import os

# Read from environment, default to local redis for development
REDIS_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/1")

app = Celery(
    "ear_compute_plane",
    broker=REDIS_URL,
    backend=RESULT_BACKEND,
    include=["services.compute_plane.tasks"]
)

app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600, # 1 hour max for heavy extraction tasks
)
