"""
Pipeline task stubs. Full AI generation steps will be implemented in Phase 4+.
These tasks define the Celery task signatures so the workflow engine can schedule them.
"""
from celery.utils.log import get_task_logger

from apps.worker.main import celery_app

logger = get_task_logger(__name__)


@celery_app.task(bind=True, name="pipeline.run_full_pipeline", max_retries=2)
def run_full_pipeline(self, story_id: str, plugin_id: str, settings: dict) -> dict:
    """Orchestrates the full AI generation pipeline for a story."""
    logger.info(f"Starting full pipeline for story {story_id}")
    return {"story_id": story_id, "status": "queued", "task_id": self.request.id}


@celery_app.task(bind=True, name="pipeline.generate_story", max_retries=3)
def generate_story(self, story_id: str, plugin_id: str) -> dict:
    """Step 1: Generate story script using LLM."""
    logger.info(f"Generating story for {story_id}")
    return {"story_id": story_id, "step": "story", "status": "pending_implementation"}


@celery_app.task(bind=True, name="pipeline.generate_image", max_retries=3)
def generate_scene_image(self, scene_id: str, prompt: str) -> dict:
    """Step 6: Generate scene image using image provider."""
    logger.info(f"Generating image for scene {scene_id}")
    return {"scene_id": scene_id, "step": "image", "status": "pending_implementation"}


@celery_app.task(bind=True, name="pipeline.generate_voice", max_retries=3)
def generate_voice(self, scene_id: str, dialogue: str, language: str) -> dict:
    """Step 7: Generate voice audio using TTS provider."""
    logger.info(f"Generating voice for scene {scene_id}")
    return {"scene_id": scene_id, "step": "voice", "status": "pending_implementation"}


@celery_app.task(bind=True, name="pipeline.render_video", max_retries=2)
def render_video(self, story_id: str) -> dict:
    """Step 10: Render final video using renderer provider."""
    logger.info(f"Rendering video for story {story_id}")
    return {"story_id": story_id, "step": "render", "status": "pending_implementation"}
