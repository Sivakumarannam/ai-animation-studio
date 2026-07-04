from enum import Enum


class UserPlan(str, Enum):
    FREE = "free"
    PRO = "pro"
    ENTERPRISE = "enterprise"


class ProjectStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    ARCHIVED = "archived"


class StoryStatus(str, Enum):
    DRAFT = "draft"
    GENERATING = "generating"
    READY = "ready"
    FAILED = "failed"


class SceneStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    READY = "ready"
    FAILED = "failed"


class AssetType(str, Enum):
    IMAGE = "image"
    VOICE = "voice"
    SUBTITLE = "subtitle"
    ANIMATION = "animation"
    BACKGROUND = "background"
    PROP = "prop"
    THUMBNAIL = "thumbnail"
    VIDEO = "video"


class AssetStatus(str, Enum):
    PENDING = "pending"
    GENERATING = "generating"
    READY = "ready"
    FAILED = "failed"


class PipelineStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"
    CANCELLED = "cancelled"


class PipelineStep(str, Enum):
    STORY = "story"
    SCRIPT = "script"
    SCENE_BREAKDOWN = "scene_breakdown"
    STORYBOARD = "storyboard"
    ASSET_SELECTION = "asset_selection"
    IMAGE_GENERATION = "image_generation"
    VOICE_GENERATION = "voice_generation"
    SUBTITLE_GENERATION = "subtitle_generation"
    ANIMATION = "animation"
    RENDERING = "rendering"
    THUMBNAIL = "thumbnail"
    SEO = "seo"
    PUBLISH = "publish"


class AnimationStyle(str, Enum):
    CARTOON_2D = "cartoon_2d"
    ANIME = "anime"
    FLAT = "flat"
    PIXEL = "pixel"
    SKETCH = "sketch"


class ContentRating(str, Enum):
    GENERAL = "general"
    KIDS = "kids"
    TEEN = "teen"
    ADULT = "adult"


class CharacterRole(str, Enum):
    LEAD = "lead"
    SUPPORTING = "supporting"
    BACKGROUND = "background"
    NARRATOR = "narrator"


class PublishStatus(str, Enum):
    DRAFT = "draft"
    PUBLIC = "public"
    UNLISTED = "unlisted"
    PRIVATE = "private"
    SCHEDULED = "scheduled"
