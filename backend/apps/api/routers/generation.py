"""
Generation API router — story generation, pipeline management, and status endpoints.
All AI calls go through the StoryGenerationService which uses the LLMProvider interface.
"""
from __future__ import annotations

from typing import Any

import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from services.story_generation_service import StoryGenerationService, get_story_generation_service

logger = structlog.get_logger()

router = APIRouter(prefix="/generation", tags=["generation"])


# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------

class GenerateOutlineRequest(BaseModel):
    story_prompt: str
    plugin_id: str = "telugu_family_comedy"
    language: str = "Telugu"
    scene_count: int = 5
    episode_title: str = ""


class StartPipelineRequest(BaseModel):
    story_id: str
    project_id: str
    plugin_id: str = "telugu_family_comedy"
    settings: dict[str, Any] = {}


class SuggestVariationsRequest(BaseModel):
    original_prompt: str
    plugin_id: str = "telugu_family_comedy"
    count: int = 3


class RefineDialogueRequest(BaseModel):
    scene_description: str
    characters: list[str]
    language: str = "Telugu"
    tone_notes: str = ""


class ThumbnailPromptRequest(BaseModel):
    story_title: str
    synopsis: str
    style_hint: str = "cartoon animation"


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/outline", summary="Generate a story outline immediately (no Celery)")
async def generate_outline(
    req: GenerateOutlineRequest,
    svc: StoryGenerationService = Depends(get_story_generation_service),
) -> dict[str, Any]:
    """
    Quick story outline generation — synchronous, returns immediately.
    Use for previews and testing. For full pipeline use /pipeline/start.
    """
    try:
        outline = await svc.generate_story_outline(
            story_prompt=req.story_prompt,
            plugin_id=req.plugin_id,
            language=req.language,
            scene_count=req.scene_count,
            episode_title=req.episode_title,
        )
        return {"success": True, "outline": outline}
    except Exception as exc:
        logger.error("outline_generation_failed", error=str(exc))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))


@router.post("/pipeline/start", summary="Dispatch full generation pipeline (Celery)")
async def start_pipeline(
    req: StartPipelineRequest,
    svc: StoryGenerationService = Depends(get_story_generation_service),
) -> dict[str, Any]:
    """
    Start the full AI generation pipeline asynchronously.
    Returns run_id and WebSocket URL for progress streaming.
    """
    # Celery import checked lazily inside the service
    try:
        result = svc.start_full_pipeline(
            story_id=req.story_id,
            project_id=req.project_id,
            user_id="api",  # TODO: replace with auth user_id from token
            plugin_id=req.plugin_id,
            settings=req.settings,
        )
        return result
    except Exception as exc:
        logger.error("pipeline_start_failed", error=str(exc))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))


@router.post("/pipeline/{run_id}/resume", summary="Resume a failed or paused pipeline")
async def resume_pipeline(
    run_id: str,
    svc: StoryGenerationService = Depends(get_story_generation_service),
) -> dict[str, Any]:
    try:
        return svc.resume_pipeline(run_id)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))


@router.get("/pipeline/{run_id}/status", summary="Get pipeline status and step results")
async def get_pipeline_status(
    run_id: str,
    svc: StoryGenerationService = Depends(get_story_generation_service),
) -> dict[str, Any]:
    status_data = await svc.get_pipeline_status(run_id)
    if status_data is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"No pipeline found for run_id={run_id}")
    return status_data


@router.post("/variations", summary="Suggest alternative story ideas")
async def suggest_variations(
    req: SuggestVariationsRequest,
    svc: StoryGenerationService = Depends(get_story_generation_service),
) -> dict[str, Any]:
    try:
        variations = await svc.suggest_story_variations(
            original_prompt=req.original_prompt,
            plugin_id=req.plugin_id,
            count=req.count,
        )
        return {"variations": variations}
    except Exception as exc:
        logger.error("variations_failed", error=str(exc))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))


@router.post("/refine-dialogue", summary="Refine dialogue for a scene")
async def refine_dialogue(
    req: RefineDialogueRequest,
    svc: StoryGenerationService = Depends(get_story_generation_service),
) -> dict[str, Any]:
    try:
        dialogue = await svc.refine_scene_dialogue(
            scene_description=req.scene_description,
            characters=req.characters,
            language=req.language,
            tone_notes=req.tone_notes,
        )
        return {"dialogue": dialogue}
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))


@router.post("/thumbnail-prompt", summary="Generate an image prompt for episode thumbnail")
async def thumbnail_prompt(
    req: ThumbnailPromptRequest,
    svc: StoryGenerationService = Depends(get_story_generation_service),
) -> dict[str, Any]:
    try:
        prompt = await svc.generate_episode_thumbnail_prompt(
            story_title=req.story_title,
            synopsis=req.synopsis,
            style_hint=req.style_hint,
        )
        return {"prompt": prompt}
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))


@router.get("/providers/health", summary="Check health of all registered AI providers")
async def providers_health() -> dict[str, Any]:
    from agents.registry import get_provider_registry
    registry = get_provider_registry()
    health = await registry.health_check()
    providers = registry.list_registered()
    return {
        "providers": providers,
        "health": health,
        "all_healthy": all(health.values()),
    }
