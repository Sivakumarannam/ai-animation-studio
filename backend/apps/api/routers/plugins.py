from typing import Any

from fastapi import APIRouter, HTTPException, status

from apps.api.dependencies import CurrentUser
from packages.core.exceptions import PluginError
from plugins.registry import get_registry

router = APIRouter(prefix="/plugins", tags=["plugins"])


@router.get("", response_model=list[dict[str, Any]])
async def list_plugins(current_user: CurrentUser) -> list[dict[str, Any]]:
    registry = get_registry()
    return registry.list_plugins()


@router.get("/{plugin_id}", response_model=dict[str, Any])
async def get_plugin(plugin_id: str, current_user: CurrentUser) -> dict[str, Any]:
    registry = get_registry()
    try:
        plugin = registry.get(plugin_id)
    except PluginError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)
    return {
        **{k: v for k, v in plugin.metadata.__dict__.items()},
        "character_archetypes": plugin.get_character_archetypes(),
        "story_templates": plugin.get_story_templates(),
        "default_settings": plugin.get_default_settings(),
    }
