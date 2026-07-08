"""
Celery application — multi-queue setup with dead-letter handling.

Queues
------
default   — lightweight CRUD-adjacent tasks
ai        — LLM / image / TTS generation (heavy, slow)
render    — FFmpeg video rendering (CPU-intensive)
publish   — upload to storage / YouTube / external
dlq       — dead-letter queue for failed tasks after all retries
"""
from __future__ import annotations

import os

from celery import Celery
from celery.signals import task_failure, task_retry, task_success, worker_process_init
from celery.utils.log import get_task_logger

CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/1")
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/1")

celery_app = Celery(
    "ai_animation_studio",
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND,
    include=[
        "apps.worker.tasks.workflow_tasks",
        "apps.worker.tasks.dead_letter",
        "apps.worker.tasks.intelligence_tasks",
        "apps.worker.tasks.knowledge_tasks",
        "apps.worker.tasks.research_tasks",
    ],
)

celery_app.conf.update(
    # Serialisation
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,

    # Reliability
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,  # one task at a time per worker thread
    task_reject_on_worker_lost=True,

    # Result TTL
    result_expires=86400 * 7,  # 7 days

    # Queue routing
    task_routes={
        "workflow.run_pipeline": {"queue": "ai"},
        "workflow.resume_pipeline": {"queue": "ai"},
        "workflow.run_step": {"queue": "ai"},
        "intelligence.*": {"queue": "ai"},
        "knowledge.*": {"queue": "ai"},
        "research.*": {"queue": "ai"},
        "render.*": {"queue": "render"},
        "publish.*": {"queue": "publish"},
        "dlq.*": {"queue": "dlq"},
    },

    # Default queue for anything not matched above
    task_default_queue="default",

    # Per-queue configuration
    task_queues={
        "default": {"exchange": "default", "routing_key": "default"},
        "ai": {"exchange": "ai", "routing_key": "ai"},
        "render": {"exchange": "render", "routing_key": "render"},
        "publish": {"exchange": "publish", "routing_key": "publish"},
        "dlq": {"exchange": "dlq", "routing_key": "dlq"},
    },
)

logger = get_task_logger(__name__)


# ---------------------------------------------------------------------------
# Worker process bootstrap — each forked worker process needs its own DB
# engine/session factory, mirroring the FastAPI lifespan startup.
# ---------------------------------------------------------------------------

@worker_process_init.connect
def _init_worker_db(**kwargs):
    from database.connection import init_db
    from apps.api.config import get_settings

    settings = get_settings()
    init_db(
        settings.DATABASE_URL,
        pool_size=settings.DATABASE_POOL_SIZE,
        max_overflow=settings.DATABASE_MAX_OVERFLOW,
    )

    from agents.registry import get_provider_registry
    from agents.provider_factory import setup_providers
    setup_providers(settings, get_provider_registry())

    logger.info("worker_process_db_initialized")


# ---------------------------------------------------------------------------
# Signal handlers — observability hooks
# ---------------------------------------------------------------------------

@task_success.connect
def on_task_success(sender=None, result=None, **kwargs):
    logger.info(f"task_success task={sender.name} result_keys={list(result.keys()) if isinstance(result, dict) else type(result).__name__}")


@task_failure.connect
def on_task_failure(sender=None, task_id=None, exception=None, traceback=None, **kwargs):
    logger.error(f"task_failure task={sender.name} task_id={task_id} error={exception}")


@task_retry.connect
def on_task_retry(sender=None, reason=None, **kwargs):
    logger.warning(f"task_retry task={sender.name} reason={reason}")
