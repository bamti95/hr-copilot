from celery import Celery

from core.config import settings


celery_app = Celery(
    "hr_copilot",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "tasks.question_generation_tasks",
    ],
)

celery_app.conf.update(
    task_default_queue=settings.CELERY_TASK_DEFAULT_QUEUE,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    worker_prefetch_multiplier=1,
    task_track_started=True,
    task_time_limit=60 * 30,
    task_soft_time_limit=60 * 25,
    broker_transport_options={"visibility_timeout": 60 * 60},
    result_backend_transport_options={"visibility_timeout": 60 * 60},
)
