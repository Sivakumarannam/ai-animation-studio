from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class PluginMetadata:
    id: str
    name: str
    version: str
    description: str
    language: str
    animation_style: str
    content_rating: str = "general"
    tags: list[str] = field(default_factory=list)
    author: str = ""


class ContentPlugin(ABC):
    """
    Base class for all content studio plugins.

    Each plugin is a self-contained content factory that defines:
    - Character archetypes
    - Story templates
    - Default settings
    - Language/locale configuration

    The core platform never contains plugin-specific business logic.
    New plugins can be added without modifying core code (Open/Closed Principle).
    """

    @property
    @abstractmethod
    def metadata(self) -> PluginMetadata:
        """Return plugin metadata (id, name, language, etc.)."""
        ...

    @abstractmethod
    def get_character_archetypes(self) -> list[dict[str, Any]]:
        """Return default character archetypes for this plugin."""
        ...

    @abstractmethod
    def get_story_templates(self) -> list[dict[str, Any]]:
        """Return story prompt templates for this plugin."""
        ...

    @abstractmethod
    def get_default_settings(self) -> dict[str, Any]:
        """Return default generation settings."""
        ...

    def get_prompt_context(self) -> dict[str, Any]:
        """Return extra context injected into all prompts for this plugin."""
        return {}
