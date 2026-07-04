"""Scene Composition and Timeline REST APIs."""
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from apps.api.dependencies import (
    CurrentUser, get_composition_service, get_timeline_service,
)
from packages.core.exceptions import NotFoundError
from packages.schemas.compositions import (
    CompositionCreate, CompositionResponse, CompositionUpdate,
    TimelineCreate, TimelineResponse, TimelineUpdate,
)
from services.animation_service import SceneCompositionService, TimelineService

router = APIRouter(tags=["compositions"])
CompSvcDep = Annotated[SceneCompositionService, Depends(get_composition_service)]
TlSvcDep = Annotated[TimelineService, Depends(get_timeline_service)]


def _comp_response(c) -> CompositionResponse:
    return CompositionResponse(
        id=str(c.id), scene_id=str(c.scene_id),
        background_id=str(c.background_id) if c.background_id else None,
        background_override=c.background_override, camera=c.camera, lighting=c.lighting,
        layers=c.layers, characters=c.characters, props=c.props,
        canvas_width=c.canvas_width, canvas_height=c.canvas_height,
        status=c.status, version=c.version,
        created_at=c.created_at.isoformat(), updated_at=c.updated_at.isoformat(),
    )


def _tl_response(t) -> TimelineResponse:
    return TimelineResponse(
        id=str(t.id), composition_id=str(t.composition_id),
        fps=t.fps, total_frames=t.total_frames, duration_seconds=t.duration_seconds,
        keyframes=t.keyframes, clips=t.clips, transitions=t.transitions,
        camera_events=t.camera_events, audio_events=t.audio_events,
        subtitle_events=t.subtitle_events, playhead_frame=t.playhead_frame,
        created_at=t.created_at.isoformat(), updated_at=t.updated_at.isoformat(),
    )


# ---------------------------------------------------------- Compositions
@router.post("/compositions", response_model=CompositionResponse, status_code=status.HTTP_201_CREATED)
async def create_composition(body: CompositionCreate, current_user: CurrentUser, svc: CompSvcDep) -> CompositionResponse:
    try:
        comp = await svc.get_or_create(body.scene_id)
        if body.model_dump(exclude_none=True, exclude={"scene_id"}):
            comp = await svc.update(comp.id, body.model_dump(exclude_none=True, exclude={"scene_id"}))
        return _comp_response(comp)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/scenes/{scene_id}/composition", response_model=CompositionResponse)
async def get_scene_composition(scene_id: UUID, current_user: CurrentUser, svc: CompSvcDep) -> CompositionResponse:
    try:
        return _comp_response(await svc.get_or_create(scene_id))
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)


@router.get("/compositions/{composition_id}", response_model=CompositionResponse)
async def get_composition(composition_id: UUID, current_user: CurrentUser, svc: CompSvcDep) -> CompositionResponse:
    try:
        return _comp_response(await svc.get_by_id(composition_id))
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)


@router.patch("/compositions/{composition_id}", response_model=CompositionResponse)
async def update_composition(
    composition_id: UUID, body: CompositionUpdate, current_user: CurrentUser, svc: CompSvcDep,
) -> CompositionResponse:
    try:
        return _comp_response(await svc.update(composition_id, body.model_dump(exclude_none=True)))
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)


@router.post("/compositions/{composition_id}/characters", response_model=CompositionResponse)
async def add_character_to_composition(
    composition_id: UUID, body: dict, current_user: CurrentUser, svc: CompSvcDep,
) -> CompositionResponse:
    try:
        return _comp_response(await svc.add_character(composition_id, body))
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)


@router.delete("/compositions/{composition_id}/characters/{ref_id}", response_model=CompositionResponse)
async def remove_character_from_composition(
    composition_id: UUID, ref_id: str, current_user: CurrentUser, svc: CompSvcDep,
) -> CompositionResponse:
    try:
        return _comp_response(await svc.remove_character(composition_id, ref_id))
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)


@router.post("/compositions/{composition_id}/props", response_model=CompositionResponse)
async def add_prop_to_composition(
    composition_id: UUID, body: dict, current_user: CurrentUser, svc: CompSvcDep,
) -> CompositionResponse:
    try:
        return _comp_response(await svc.add_prop(composition_id, body))
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)


@router.delete("/compositions/{composition_id}/props/{ref_id}", response_model=CompositionResponse)
async def remove_prop_from_composition(
    composition_id: UUID, ref_id: str, current_user: CurrentUser, svc: CompSvcDep,
) -> CompositionResponse:
    try:
        return _comp_response(await svc.remove_prop(composition_id, ref_id))
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)


@router.delete("/compositions/{composition_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_composition(composition_id: UUID, current_user: CurrentUser, svc: CompSvcDep) -> None:
    try:
        await svc.delete(composition_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)


# ---------------------------------------------------------- Timelines
@router.get("/compositions/{composition_id}/timeline", response_model=TimelineResponse)
async def get_timeline(composition_id: UUID, current_user: CurrentUser, svc: TlSvcDep) -> TimelineResponse:
    tl = await svc.get_or_create(composition_id)
    return _tl_response(tl)


@router.patch("/timelines/{timeline_id}", response_model=TimelineResponse)
async def update_timeline(
    timeline_id: UUID, body: TimelineUpdate, current_user: CurrentUser, svc: TlSvcDep,
) -> TimelineResponse:
    try:
        return _tl_response(await svc.update(timeline_id, body.model_dump(exclude_none=True)))
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)


@router.post("/timelines/{timeline_id}/keyframes", response_model=TimelineResponse)
async def add_keyframe(timeline_id: UUID, body: dict, current_user: CurrentUser, svc: TlSvcDep) -> TimelineResponse:
    try:
        return _tl_response(await svc.add_keyframe(timeline_id, body))
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)


@router.post("/timelines/{timeline_id}/clips", response_model=TimelineResponse)
async def add_clip(timeline_id: UUID, body: dict, current_user: CurrentUser, svc: TlSvcDep) -> TimelineResponse:
    try:
        return _tl_response(await svc.add_clip(timeline_id, body))
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)


@router.delete("/timelines/{timeline_id}/clips/{clip_id}", response_model=TimelineResponse)
async def remove_clip(
    timeline_id: UUID, clip_id: str, current_user: CurrentUser, svc: TlSvcDep,
) -> TimelineResponse:
    try:
        return _tl_response(await svc.remove_clip(timeline_id, clip_id))
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)


@router.patch("/timelines/{timeline_id}/playhead/{frame}", response_model=TimelineResponse)
async def set_playhead(
    timeline_id: UUID, frame: int, current_user: CurrentUser, svc: TlSvcDep,
) -> TimelineResponse:
    try:
        return _tl_response(await svc.set_playhead(timeline_id, frame))
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)
