from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from apps.api.config import Settings, get_settings
from database.connection import get_session
from database.models.user import User
from packages.utils.security import decode_token
from repositories.animation_repository import (
    AssetVersionRepository,
    CharacterTemplateRepository,
    ExpressionRepository,
    PoseRepository,
    SceneCompositionRepository,
    TimelineRepository,
)
from repositories.asset_repository import (
    AssetRepository, BackgroundRepository, PropRepository,
    AnimationPresetRepository, AudioRepository, MusicRepository, SoundEffectRepository
)
from repositories.character_repository import CharacterRepository
from repositories.project_repository import ProjectRepository
from repositories.scene_repository import SceneRepository
from repositories.story_repository import StoryRepository
from repositories.user_repository import RefreshTokenRepository, UserRepository
from services.animation_service import (
    AssetManagerService,
    CharacterTemplateService,
    ExpressionService,
    PoseService,
    SceneCompositionService,
    TimelineService,
)
from services.auth_service import AuthService
from services.character_service import CharacterService
from services.library_service import (
    BackgroundLibraryService, PropLibraryService,
    AnimationPresetLibraryService, AudioLibraryService, MusicLibraryService, SoundEffectLibraryService
)
from services.project_service import ProjectService
from services.scene_service import SceneService
from services.story_service import StoryService
from plugins.storage.minio_storage import MinIOStorage
from sqlalchemy.ext.asyncio import AsyncSession

bearer_scheme = HTTPBearer(auto_error=False)

SettingsDep = Annotated[Settings, Depends(get_settings)]
SessionDep = Annotated[AsyncSession, Depends(get_session)]


# ---------------------------------------------------------------------------
# Repositories
# ---------------------------------------------------------------------------

def get_user_repo(session: SessionDep) -> UserRepository:
    return UserRepository(session)


def get_refresh_token_repo(session: SessionDep) -> RefreshTokenRepository:
    return RefreshTokenRepository(session)


def get_project_repo(session: SessionDep) -> ProjectRepository:
    return ProjectRepository(session)


def get_story_repo(session: SessionDep) -> StoryRepository:
    return StoryRepository(session)


def get_scene_repo(session: SessionDep) -> SceneRepository:
    return SceneRepository(session)


def get_character_repo(session: SessionDep) -> CharacterRepository:
    return CharacterRepository(session)


def get_asset_repo(session: SessionDep) -> AssetRepository:
    return AssetRepository(session)


def get_background_repo(session: SessionDep) -> BackgroundRepository:
    return BackgroundRepository(session)


def get_prop_repo(session: SessionDep) -> PropRepository:
    return PropRepository(session)


def get_animation_preset_repo(session: SessionDep) -> AnimationPresetRepository:
    return AnimationPresetRepository(session)


def get_audio_repo(session: SessionDep) -> AudioRepository:
    return AudioRepository(session)


def get_music_repo(session: SessionDep) -> MusicRepository:
    return MusicRepository(session)


def get_sound_effect_repo(session: SessionDep) -> SoundEffectRepository:
    return SoundEffectRepository(session)


# Module 2 — Animation Engine repos
def get_expression_repo(session: SessionDep) -> ExpressionRepository:
    return ExpressionRepository(session)


def get_pose_repo(session: SessionDep) -> PoseRepository:
    return PoseRepository(session)


def get_character_template_repo(session: SessionDep) -> CharacterTemplateRepository:
    return CharacterTemplateRepository(session)


def get_composition_repo(session: SessionDep) -> SceneCompositionRepository:
    return SceneCompositionRepository(session)


def get_timeline_repo(session: SessionDep) -> TimelineRepository:
    return TimelineRepository(session)


def get_asset_version_repo(session: SessionDep) -> AssetVersionRepository:
    return AssetVersionRepository(session)


# ---------------------------------------------------------------------------
# Services (existing)
# ---------------------------------------------------------------------------

def get_auth_service(
    user_repo: Annotated[UserRepository, Depends(get_user_repo)],
    token_repo: Annotated[RefreshTokenRepository, Depends(get_refresh_token_repo)],
    settings: SettingsDep,
) -> AuthService:
    return AuthService(user_repo, token_repo, settings)


def get_project_service(
    repo: Annotated[ProjectRepository, Depends(get_project_repo)],
) -> ProjectService:
    return ProjectService(repo)


def get_story_service(
    repo: Annotated[StoryRepository, Depends(get_story_repo)],
) -> StoryService:
    return StoryService(repo)


def get_scene_service(
    repo: Annotated[SceneRepository, Depends(get_scene_repo)],
) -> SceneService:
    return SceneService(repo)


def get_character_service(
    repo: Annotated[CharacterRepository, Depends(get_character_repo)],
) -> CharacterService:
    return CharacterService(repo)


# ---------------------------------------------------------------------------
# Services (Module 2 — Animation Engine)
# ---------------------------------------------------------------------------

def get_expression_service(
    repo: Annotated[ExpressionRepository, Depends(get_expression_repo)],
) -> ExpressionService:
    return ExpressionService(repo)


def get_pose_service(
    repo: Annotated[PoseRepository, Depends(get_pose_repo)],
) -> PoseService:
    return PoseService(repo)


def get_character_template_service(
    repo: Annotated[CharacterTemplateRepository, Depends(get_character_template_repo)],
) -> CharacterTemplateService:
    return CharacterTemplateService(repo)


def get_composition_service(
    repo: Annotated[SceneCompositionRepository, Depends(get_composition_repo)],
) -> SceneCompositionService:
    return SceneCompositionService(repo)


def get_timeline_service(
    repo: Annotated[TimelineRepository, Depends(get_timeline_repo)],
) -> TimelineService:
    return TimelineService(repo)


def get_background_library_service(
    repo: Annotated[BackgroundRepository, Depends(get_background_repo)],
) -> BackgroundLibraryService:
    return BackgroundLibraryService(repo)


def get_prop_library_service(
    repo: Annotated[PropRepository, Depends(get_prop_repo)],
) -> PropLibraryService:
    return PropLibraryService(repo)


def get_animation_preset_service(
    repo: Annotated[AnimationPresetRepository, Depends(get_animation_preset_repo)],
) -> AnimationPresetLibraryService:
    return AnimationPresetLibraryService(repo)


def get_audio_service(
    repo: Annotated[AudioRepository, Depends(get_audio_repo)],
) -> AudioLibraryService:
    return AudioLibraryService(repo)


def get_music_service(
    repo: Annotated[MusicRepository, Depends(get_music_repo)],
) -> MusicLibraryService:
    return MusicLibraryService(repo)


def get_sound_effect_service(
    repo: Annotated[SoundEffectRepository, Depends(get_sound_effect_repo)],
) -> SoundEffectLibraryService:
    return SoundEffectLibraryService(repo)


def get_storage(settings: SettingsDep) -> MinIOStorage:
    storage = MinIOStorage(
        endpoint=settings.MINIO_ENDPOINT,
        access_key=settings.MINIO_ACCESS_KEY,
        secret_key=settings.MINIO_SECRET_KEY,
        secure=settings.MINIO_SECURE,
    )
    storage.ensure_bucket(settings.MINIO_BUCKET_ASSETS)
    return storage


def get_asset_manager_service(
    version_repo: Annotated[AssetVersionRepository, Depends(get_asset_version_repo)],
    expr_repo: Annotated[ExpressionRepository, Depends(get_expression_repo)],
    pose_repo: Annotated[PoseRepository, Depends(get_pose_repo)],
    tmpl_repo: Annotated[CharacterTemplateRepository, Depends(get_character_template_repo)],
    bg_repo: Annotated[BackgroundRepository, Depends(get_background_repo)],
    prop_repo: Annotated[PropRepository, Depends(get_prop_repo)],
    preset_repo: Annotated[AnimationPresetRepository, Depends(get_animation_preset_repo)],
    audio_repo: Annotated[AudioRepository, Depends(get_audio_repo)],
    music_repo: Annotated[MusicRepository, Depends(get_music_repo)],
    sfx_repo: Annotated[SoundEffectRepository, Depends(get_sound_effect_repo)],
) -> AssetManagerService:
    return AssetManagerService(
        version_repo, expr_repo, pose_repo, tmpl_repo,
        bg_repo, prop_repo, preset_repo, audio_repo, music_repo, sfx_repo
    )


# ---------------------------------------------------------------------------
# Auth middleware
# ---------------------------------------------------------------------------

async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    user_repo: Annotated[UserRepository, Depends(get_user_repo)],
    settings: SettingsDep,
) -> User:
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    try:
        payload = decode_token(credentials.credentials, settings.SECRET_KEY, settings.JWT_ALGORITHM)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")

    if payload.get("type") != "access":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Wrong token type")

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Malformed token")

    user = await user_repo.get_by_id(UUID(user_id))
    if user is None or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive")
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]
