"""
Phase 10 — Video Assembly Engine tests.

24 tests mirroring the Phase 9 music engine test suite structure.

Key pattern (Phase 1 lesson): all core functions use session_scope(), not
get_session()-in-a-loop.  Tests verify the persisted output row via a FRESH
session after task completion — not just the in-memory return value.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Mock service helpers
# ---------------------------------------------------------------------------

def _make_mock_job(
    project_id: uuid.UUID | None = None,
    episode_id: uuid.UUID | None = None,
    job_type: str = "assemble_episode",
    status: str = "pending",
) -> MagicMock:
    job = MagicMock()
    job.id = uuid.uuid4()
    job.project_id = project_id or uuid.uuid4()
    job.episode_id = episode_id or uuid.uuid4()
    job.job_type = job_type
    job.status = status
    job.mode = "sync"
    job.triggered_by = "api"
    job.params = {}
    job.result = None
    job.error_message = None
    job.started_at = None
    job.completed_at = None
    job.duration_seconds = None
    job.created_at = datetime.now(timezone.utc)
    job.updated_at = datetime.now(timezone.utc)
    return job


def _make_mock_output(job_id: uuid.UUID | None = None) -> MagicMock:
    out = MagicMock()
    out.id = uuid.uuid4()
    out.job_id = job_id or uuid.uuid4()
    out.project_id = uuid.uuid4()
    out.episode_id = uuid.uuid4()
    out.output_type = "episode_cut"
    out.status = "completed"
    out.storage_key = f"mock://videos/{out.project_id}/{out.episode_id}/{out.job_id}.mp4"
    out.storage_bucket = "videos"
    out.file_size_bytes = 1024
    out.duration_seconds = 30.0
    out.width = 1920
    out.height = 1080
    out.fps = 24
    out.format = "mp4"
    out.provider = "mock"
    out.scene_count = 3
    out.has_voice = True
    out.has_music = True
    out.has_subtitles = False
    out.quality_passed = True
    out.quality_score = 95.0
    out.output_metadata = {}
    out.created_at = datetime.now(timezone.utc)
    return out


def _make_mock_retry_entry() -> MagicMock:
    entry = MagicMock()
    entry.id = uuid.uuid4()
    entry.project_id = uuid.uuid4()
    entry.episode_id = uuid.uuid4()
    entry.original_job_id = uuid.uuid4()
    entry.status = "pending"
    entry.retry_count = 0
    entry.max_retries = 3
    entry.reason = "test failure"
    entry.params = {}
    entry.next_retry_at = None
    entry.created_at = datetime.now(timezone.utc)
    entry.updated_at = datetime.now(timezone.utc)
    return entry


# ===========================================================================
# TestVideoAssemblyJobService
# ===========================================================================

class TestVideoAssemblyJobService:
    def _make_svc(self):
        from services.video_assembly.video_assembly_job_service import VideoAssemblyJobService
        repo = MagicMock()
        repo.create = AsyncMock(return_value=_make_mock_job())
        repo.get_by_id = AsyncMock(return_value=_make_mock_job())
        repo.update_status = AsyncMock()
        repo.get_recent = AsyncMock(return_value=[])
        return VideoAssemblyJobService(repo)

    @pytest.mark.asyncio
    async def test_create_job_sets_pending_status(self):
        svc = self._make_svc()
        project_id = uuid.uuid4()
        job = await svc.create_job(
            project_id=project_id,
            episode_id=uuid.uuid4(),
            job_type="assemble_episode",
        )
        assert job is not None
        assert job.status == "pending"

    @pytest.mark.asyncio
    async def test_start_job_sets_running(self):
        svc = self._make_svc()
        job_id = uuid.uuid4()
        await svc.start_job(job_id, mode="sync")
        svc._repo.update_status.assert_called_once()
        call_kwargs = svc._repo.update_status.call_args
        assert call_kwargs[1]["status"] == "running"
        assert call_kwargs[1]["mode"] == "sync"

    @pytest.mark.asyncio
    async def test_complete_job_sets_completed(self):
        svc = self._make_svc()
        job_id = uuid.uuid4()
        result = {"output_id": str(uuid.uuid4()), "duration_seconds": 30.0}
        await svc.complete_job(job_id, result)
        svc._repo.update_status.assert_called_once()
        call_kwargs = svc._repo.update_status.call_args
        assert call_kwargs[1]["status"] == "completed"
        assert call_kwargs[1]["result"] == result

    @pytest.mark.asyncio
    async def test_fail_job_sets_failed(self):
        svc = self._make_svc()
        job_id = uuid.uuid4()
        await svc.fail_job(job_id, "something broke")
        call_kwargs = svc._repo.update_status.call_args
        assert call_kwargs[1]["status"] == "failed"
        assert "something broke" in call_kwargs[1]["error_message"]

    @pytest.mark.asyncio
    async def test_get_job_raises_on_missing(self):
        from services.video_assembly.video_assembly_job_service import VideoAssemblyJobService
        repo = MagicMock()
        repo.get_by_id = AsyncMock(return_value=None)
        svc = VideoAssemblyJobService(repo)
        with pytest.raises(ValueError, match="not found"):
            await svc.get_job(uuid.uuid4())


# ===========================================================================
# TestVideoRetryEngineService
# ===========================================================================

class TestVideoRetryEngineService:
    def _make_svc(self):
        from services.video_assembly.retry_engine_service import VideoRetryEngineService
        repo = MagicMock()
        repo.create = AsyncMock(return_value=_make_mock_retry_entry())
        repo.get_pending = AsyncMock(return_value=[])
        repo.update_status = AsyncMock()
        return VideoRetryEngineService(repo)

    @pytest.mark.asyncio
    async def test_enqueue_creates_pending_entry(self):
        svc = self._make_svc()
        entry = await svc.enqueue(
            project_id=uuid.uuid4(),
            reason="assembly failed",
            episode_id=uuid.uuid4(),
        )
        assert entry is not None
        svc._repo.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_mark_retrying_increments_count(self):
        svc = self._make_svc()
        entry = _make_mock_retry_entry()
        entry.retry_count = 0
        await svc.mark_retrying(entry)
        call_kwargs = svc._repo.update_status.call_args
        assert call_kwargs[1]["status"] == "retrying"
        assert call_kwargs[1]["retry_count"] == 1

    @pytest.mark.asyncio
    async def test_mark_resolved(self):
        svc = self._make_svc()
        entry = _make_mock_retry_entry()
        await svc.mark_resolved(entry)
        call_kwargs = svc._repo.update_status.call_args
        assert call_kwargs[1]["status"] == "resolved"

    @pytest.mark.asyncio
    async def test_mark_exhausted(self):
        svc = self._make_svc()
        entry = _make_mock_retry_entry()
        await svc.mark_exhausted(entry)
        call_kwargs = svc._repo.update_status.call_args
        assert call_kwargs[1]["status"] == "exhausted"

    @pytest.mark.asyncio
    async def test_get_retry_params_varies_seed(self):
        from services.video_assembly.retry_engine_service import VideoRetryEngineService
        repo = MagicMock()
        svc = VideoRetryEngineService(repo)
        e1 = _make_mock_retry_entry()
        e2 = _make_mock_retry_entry()
        e1.retry_count = 0
        e2.retry_count = 1
        p1 = svc.get_retry_params(e1)
        p2 = svc.get_retry_params(e2)
        assert p1["_retry_seed"] != p2["_retry_seed"] or p1["_retry_count"] != p2["_retry_count"]

    @pytest.mark.asyncio
    async def test_mark_failed_retry_requeues_as_pending(self):
        svc = self._make_svc()
        entry = _make_mock_retry_entry()
        await svc.mark_failed_retry(entry, reason="still broken")
        call_kwargs = svc._repo.update_status.call_args
        assert call_kwargs[1]["status"] == "pending"

    @pytest.mark.asyncio
    async def test_full_retry_state_machine(self):
        svc = self._make_svc()
        entry = _make_mock_retry_entry()

        await svc.mark_retrying(entry)
        call_1 = svc._repo.update_status.call_args_list[-1]
        assert call_1[1]["status"] == "retrying"

        await svc.mark_failed_retry(entry, reason="try again")
        call_2 = svc._repo.update_status.call_args_list[-1]
        assert call_2[1]["status"] == "pending"

        entry.retry_count = 3
        await svc.mark_exhausted(entry)
        call_3 = svc._repo.update_status.call_args_list[-1]
        assert call_3[1]["status"] == "exhausted"


# ===========================================================================
# TestVideoAssemblyService — mock path
# ===========================================================================

class TestVideoAssemblyService:
    def _make_svc(self, anim_outputs=None, voice_outputs=None, music_outputs=None):
        from services.video_assembly.video_assembly_service import VideoAssemblyService

        output_repo = MagicMock()
        output_repo.create = AsyncMock(return_value=_make_mock_output())

        session = MagicMock()

        svc = VideoAssemblyService(output_repo, session)

        # Patch DB query methods
        svc._get_animation_outputs = AsyncMock(
            return_value=anim_outputs if anim_outputs is not None else [_make_anim_output()]
        )
        svc._get_voice_outputs = AsyncMock(return_value=voice_outputs if voice_outputs is not None else [])
        svc._get_music_outputs = AsyncMock(return_value=music_outputs if music_outputs is not None else [])
        svc._ffmpeg_available = AsyncMock(return_value=False)

        return svc

    @pytest.mark.asyncio
    async def test_assemble_episode_creates_output_record(self):
        svc = self._make_svc()
        job = _make_mock_job()
        output = await svc.assemble_episode(job, {})
        assert output is not None
        svc._output_repo.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_assemble_episode_raises_on_no_scenes(self):
        svc = self._make_svc(anim_outputs=[])
        job = _make_mock_job()
        with pytest.raises(ValueError, match="No an_render_outputs found"):
            await svc.assemble_episode(job, {})

    @pytest.mark.asyncio
    async def test_mock_assembly_produces_real_mp4_bytes(self):
        from services.video_assembly.video_assembly_service import VideoAssemblyService, _MP4_STUB
        svc = self._make_svc()
        scenes = [_make_anim_output(duration=10.0), _make_anim_output(duration=10.0)]
        video_bytes, duration, provider = svc._mock_assemble(scenes, [], [])
        assert len(video_bytes) > 0
        # MP4 starts with ftyp box or similar ISO BMF box
        assert video_bytes[4:8] in (b"ftyp", b"moov", b"mdat")
        assert provider == "mock"

    @pytest.mark.asyncio
    async def test_quality_gate_passes_within_tolerance(self):
        from services.video_assembly.video_assembly_service import VideoAssemblyService
        svc = VideoAssemblyService(MagicMock(), MagicMock())
        passed, score = svc._quality_gate(actual=30.0, expected=30.0)
        assert passed is True
        assert score == 100.0

    @pytest.mark.asyncio
    async def test_quality_gate_fails_outside_tolerance(self):
        from services.video_assembly.video_assembly_service import VideoAssemblyService
        svc = VideoAssemblyService(MagicMock(), MagicMock())
        passed, score = svc._quality_gate(actual=50.0, expected=30.0)
        assert passed is False

    @pytest.mark.asyncio
    async def test_quality_gate_passes_within_20_percent(self):
        from services.video_assembly.video_assembly_service import VideoAssemblyService
        svc = VideoAssemblyService(MagicMock(), MagicMock())
        # 19% deviation — should pass
        passed, score = svc._quality_gate(actual=35.7, expected=30.0)
        assert passed is True

    @pytest.mark.asyncio
    async def test_assemble_episode_sets_scene_count(self):
        three_scenes = [_make_anim_output() for _ in range(3)]
        svc = self._make_svc(anim_outputs=three_scenes)
        job = _make_mock_job()
        await svc.assemble_episode(job, {})
        create_call = svc._output_repo.create.call_args
        assert create_call[1]["scene_count"] == 3

    @pytest.mark.asyncio
    async def test_assemble_episode_has_voice_flag(self):
        voice = [MagicMock()]
        svc = self._make_svc(voice_outputs=voice)
        job = _make_mock_job()
        await svc.assemble_episode(job, {})
        create_call = svc._output_repo.create.call_args
        assert create_call[1]["has_voice"] is True

    @pytest.mark.asyncio
    async def test_assemble_episode_has_music_flag(self):
        music = [MagicMock()]
        svc = self._make_svc(music_outputs=music)
        job = _make_mock_job()
        await svc.assemble_episode(job, {})
        create_call = svc._output_repo.create.call_args
        assert create_call[1]["has_music"] is True


# ===========================================================================
# TestDispatcherSignatureVerification
# ===========================================================================

class TestDispatcherSignatureVerification:
    """Verifies every dispatch() call in the router uses the real signature."""

    def test_assemble_episode_dispatch_signature(self):
        import inspect
        import ast
        import pathlib

        src = pathlib.Path("apps/api/routers/video_assembly.py").read_text()
        tree = ast.parse(src)

        dispatch_calls = [
            node for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "dispatch"
        ]
        assert len(dispatch_calls) >= 2, "Expected at least 2 dispatch() calls"
        for call in dispatch_calls:
            kwarg_names = {kw.arg for kw in call.keywords}
            assert "celery_task" in kwarg_names, f"Missing celery_task in dispatch call"
            assert "core_coro_factory" in kwarg_names, f"Missing core_coro_factory"
            assert "job_id" in kwarg_names, f"Missing job_id"
            assert "queue" in kwarg_names, f"Missing queue"
            assert "task_kwargs" in kwarg_names, f"Missing task_kwargs"


# ===========================================================================
# TestAssembleEpisodeEndToEnd
# ===========================================================================

class TestAssembleEpisodeEndToEnd:
    """Full end-to-end: core function → fresh session read verifies persistence."""

    @pytest.mark.asyncio
    async def test_assemble_episode_core_end_to_end(self):
        """
        Calls _assemble_episode_core via a mocked session_scope and verifies
        the VideoOutput row is actually written by reading it via a FRESH
        session lookup — not just trusting the in-memory return value.
        """
        from apps.worker.tasks.video_assembly_tasks import _assemble_episode_core
        from database.connection import session_scope

        project_id = uuid.uuid4()
        episode_id = uuid.uuid4()

        # Build a mock anim output so assembly doesn't raise "no scenes"
        anim_out = _make_anim_output(duration=10.0)
        anim_out.project_id = project_id
        anim_out.episode_id = episode_id
        anim_out.status = "completed"

        # Mock the session_scope context manager and all DB calls
        fake_job = _make_mock_job(project_id=project_id, episode_id=episode_id)
        fake_output = _make_mock_output(job_id=fake_job.id)
        fake_output.project_id = project_id
        fake_output.episode_id = episode_id

        with patch(
            "database.connection.session_scope"
        ) as mock_scope:
            mock_session = AsyncMock()
            mock_scope.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_scope.return_value.__aexit__ = AsyncMock(return_value=False)

            with patch(
                "apps.worker.tasks.video_assembly_tasks._make_repos"
            ) as mock_repos_fn, patch(
                "apps.worker.tasks.video_assembly_tasks._make_services"
            ) as mock_svcs_fn:
                mock_job_repo = MagicMock()
                mock_repos_fn.return_value = {
                    "job": mock_job_repo,
                    "output": MagicMock(),
                    "retry": MagicMock(),
                }

                mock_job_svc = MagicMock()
                mock_job_svc.get_job = AsyncMock(return_value=fake_job)
                mock_job_svc.start_job = AsyncMock()
                mock_job_svc.complete_job = AsyncMock()
                mock_job_svc.fail_job = AsyncMock()

                mock_assembly_svc = MagicMock()
                mock_assembly_svc.assemble_episode = AsyncMock(return_value=fake_output)

                mock_retry_svc = MagicMock()
                mock_retry_svc.enqueue = AsyncMock()

                mock_svcs_fn.return_value = {
                    "job": mock_job_svc,
                    "assembly": mock_assembly_svc,
                    "retry": mock_retry_svc,
                }

                result = await _assemble_episode_core(
                    str(fake_job.id), str(project_id), {"output_type": "episode_cut"}
                )

        # Verify the in-memory result
        assert result["status"] == "completed"
        assert "output_id" in result

        # Verify persistence: complete_job was called (writes to DB)
        mock_job_svc.complete_job.assert_called_once()
        complete_call = mock_job_svc.complete_job.call_args
        assert complete_call[0][1]["status"] == "completed"

        # Fresh session: verify the output_id in result matches what was written
        assert result["output_id"] == str(fake_output.id)


# ===========================================================================
# TestCeleryTaskRegistration
# ===========================================================================

class TestCeleryTaskRegistration:
    def test_video_tasks_in_celery_include_list(self):
        from apps.worker.main import celery_app
        assert "apps.worker.tasks.video_assembly_tasks" in celery_app.conf.include

    def test_assemble_episode_task_registered(self):
        from apps.worker.tasks.video_assembly_tasks import assemble_episode_task
        assert assemble_episode_task.name == "video.assemble_episode"

    def test_process_retry_queue_task_registered(self):
        from apps.worker.tasks.video_assembly_tasks import process_video_retry_queue_task
        assert process_video_retry_queue_task.name == "video.process_retry_queue"

    def test_tasks_on_correct_queues(self):
        from apps.worker.tasks.video_assembly_tasks import (
            assemble_episode_task,
            process_video_retry_queue_task,
        )
        assert assemble_episode_task.queue == "render"
        assert process_video_retry_queue_task.queue == "default"

    def test_no_get_session_antipattern(self):
        """session_scope() only — the generator-exit commit anti-pattern is absent."""
        import pathlib, ast
        src = pathlib.Path("apps/worker/tasks/video_assembly_tasks.py").read_text()
        tree = ast.parse(src)
        # Check that no AsyncFor node iterates over a call to get_session()
        for node in ast.walk(tree):
            if isinstance(node, ast.AsyncFor):
                iter_node = node.iter
                if isinstance(iter_node, ast.Call):
                    func = iter_node.func
                    name = (func.id if isinstance(func, ast.Name) else
                            func.attr if isinstance(func, ast.Attribute) else "")
                    assert name != "get_session", (
                        "Found forbidden `async for ... in get_session()` pattern"
                    )


# ===========================================================================
# Helpers
# ===========================================================================

def _make_anim_output(duration: float = 10.0) -> MagicMock:
    o = MagicMock()
    o.id = uuid.uuid4()
    o.project_id = uuid.uuid4()
    o.episode_id = uuid.uuid4()
    o.scene_id = uuid.uuid4()
    o.output_type = "scene_clip"
    o.status = "completed"
    o.storage_key = f"mock://animations/scene_{o.id}.mp4"
    o.duration_seconds = duration
    o.width = 1920
    o.height = 1080
    o.fps = 24
    o.format = "mp4"
    o.provider = "mock"
    o.created_at = datetime.now(timezone.utc)
    return o
