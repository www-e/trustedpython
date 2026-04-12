"""
Celery Application Configuration

Configures Celery for background task processing with Redis as broker.
All async tasks should be defined as separate modules in this directory.
"""

from celery import Celery

from app.core.config import settings

# Create Celery instance
celery_app = Celery(
    "game_marketplace",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=[
        # Task modules will be added here as they are created
        # "app.tasks.email_tasks",
        # "app.tasks.payment_tasks",
    ],
)

# Celery configuration
celery_app.conf.update(
    # Task settings
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    # Task routing (will be expanded)
    task_routes={
        # "app.tasks.email_tasks.*": {"queue": "email"},
    },
    # Task result settings
    result_expires=3600,
    # Worker settings
    worker_prefetch_multiplier=4,
    worker_concurrency=4,
    worker_max_tasks_per_child=1000,
    # Task execution settings
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    # Error handling
    task_send_sent_event=True,
    task_send_failed_event=True,
    # Beat scheduler settings (for periodic tasks)
    beat_scheduler_filename="celerybeat-schedule",
)

# Periodic task schedule
from celery.schedules import crontab

celery_app.conf.beat_schedule = {
    # Example periodic tasks (will be expanded)
    # "cleanup-expired-tokens": {
    #     "task": "app.tasks.cleanup_tasks.cleanup_expired_tokens",
    #     "schedule": crontab(hour=0, minute=0),
    # },
}
