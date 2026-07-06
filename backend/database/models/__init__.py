# Ensures all models are registered with SQLAlchemy metadata.
# Import order does not matter — all tables are declared on the same Base.
from database.models.user import User, RefreshToken  # noqa: F401
from database.models.project import Project  # noqa: F401
from database.models.story import Story  # noqa: F401
from database.models.scene import Scene  # noqa: F401
from database.models.character import Character  # noqa: F401
from database.models.asset import (  # noqa: F401
    Background, Prop, AnimationPreset, Audio, Music, SoundEffect
)
from database.models.animation import (  # noqa: F401
    Expression, Pose, CharacterTemplate,
    SceneComposition, Timeline, AssetVersion,
)
from database.models.intelligence import (  # noqa: F401
    World, Season, Episode, StoryScene, StoryIdea,
    StoryMemory, StoryEvaluation, GenerationJob,
    GenerationLog, RetryQueue, StoryVersion,
)
from database.models.knowledge import (  # noqa: F401
    KnowledgeCollection, KnowledgeDocument, KnowledgeChunk,
    EmbeddingJob, KnowledgeMemory, RetrievalHistory, KnowledgeVersion,
)
