from pydantic import BaseModel, Field


class SceneCreate(BaseModel):
    scene_number: int = Field(ge=1)
    title: str = ""
    description: str = ""
    dialogue: str = ""
    action_notes: str = ""
    duration_seconds: float = Field(default=0.0, ge=0.0)
    background_id: str | None = None
    ordering: int = 0


class SceneUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    dialogue: str | None = None
    action_notes: str | None = None
    duration_seconds: float | None = None
    background_id: str | None = None
    status: str | None = None
    ordering: int | None = None


class SceneReorderRequest(BaseModel):
    scene_ids: list[str]


class SceneResponse(BaseModel):
    id: str
    story_id: str
    scene_number: int
    title: str
    description: str
    dialogue: str
    action_notes: str
    duration_seconds: float
    background_id: str | None
    status: str
    ordering: int
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}
