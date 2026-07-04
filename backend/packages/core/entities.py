from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID, uuid4
from typing import Any


@dataclass
class Entity:
    id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class UserEntity(Entity):
    email: str = ""
    full_name: str = ""
    is_active: bool = True
    is_superuser: bool = False
    plan: str = "free"
    language: str = "en"


@dataclass
class ProjectEntity(Entity):
    user_id: UUID = field(default_factory=uuid4)
    title: str = ""
    description: str = ""
    status: str = "draft"
    plugin_id: str = ""
    animation_style: str = "cartoon_2d"
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class StoryEntity(Entity):
    project_id: UUID = field(default_factory=uuid4)
    title: str = ""
    premise: str = ""
    full_script: str = ""
    genre: str = ""
    tone: str = ""
    duration_target: int = 0
    language: str = "en"
    status: str = "draft"
    ai_metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class SceneEntity(Entity):
    story_id: UUID = field(default_factory=uuid4)
    scene_number: int = 0
    title: str = ""
    description: str = ""
    dialogue: str = ""
    action_notes: str = ""
    duration_seconds: float = 0.0
    background_id: UUID | None = None
    status: str = "pending"
    ordering: int = 0


@dataclass
class CharacterEntity(Entity):
    project_id: UUID = field(default_factory=uuid4)
    name: str = ""
    description: str = ""
    personality: str = ""
    voice_profile: str = ""
    age_range: str = ""
    gender: str = ""
    is_library: bool = False
    thumbnail_url: str = ""
    asset_data: dict[str, Any] = field(default_factory=dict)
