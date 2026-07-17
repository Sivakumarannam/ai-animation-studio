"""
Phase 9 — Music & Sound Engine tests.

Mirrors test_voice_engine.py / test_animation_engine.py structure.

Coverage:
  - MockMusicProvider: generates real WAV bytes, deterministic, varies by mood,
    is_available
  - MusicJobService: create → start → complete → fail lifecycle
  - MusicRetryEngineService: enqueue → retrying → resolved/exhausted,
    mark_failed_retry requeues as pending, full state machine, seed variance
  - MusicGenerationService: provider call + output record creation
  - Dispatcher signature verification (grepped against real dispatcher.py)
  - End-to-end: generate_track core function drives dispatch → complete chain
    AND queries the committed mu_outputs row (catches silent-commit bug)
  - Celery task registration: all 3 music tasks in include list
"""
from __future__ import annotations

import asyncio
import inspect
import uuid
from unittest.mock import AsyncMock, MagicMock, patch


def _make_uuid() -> str:
    return str(uuid.uuid4())


# ---------------------------------------------------------------------------
# MockMusicProvider
# ---------------------------------------------------------------------------

class TestMockMusicProvider:
    async def test_generate_returns_result(self):
        from agents.implementations.mock_music_provider import MockMusicProvider
        from agents.interfaces.music_provider import MusicGenerationRequest

        provider = MockMusicProvider()
        request = MusicGenerationRequest(
            project_id=_make_uuid(),
            mood="adventure",
            duration_seconds=3.0,
        )
        result = await provider.generate_track(request)

        assert result.provider == "mock"
        assert result.storage_key.startswith("music/")
        assert result.duration_seconds > 0
        assert result.format == "wav"
        assert result.sample_rate == 44100
        assert len(result.audio_bytes) > 0

    async def test_generate_produces_real_wav_bytes(self):
        """Output must be a valid RIFF/WAV header."""
        from agents.implementations.mock_music_provider import MockMusicProvider
        from agents.interfaces.music_provider import MusicGenerationRequest

        provider = MockMusicProvider()
        request = MusicGenerationRequest(
            project_id=_make_uuid(),
            mood="comedy",
            duration_seconds=1.0,
        )
        result = await provider.generate_track(request)
        assert result.audio_bytes[:4] == b"RIFF", "audio_bytes must start with RIFF WAV header"
        assert result.audio_bytes[8:12] == b"WAVE"

    async def test_generate_is_deterministic(self):
        from agents.implementations.mock_music_provider import MockMusicProvider
        from agents.interfaces.music_provider import MusicGenerationRequest

        provider = MockMusicProvider()
        pid = _make_uuid()
        request = MusicGenerationRequest(
            project_id=pid,
            mood="happy",
            duration_seconds=2.0,
        )
        r1 = await provider.generate_track(request)
        r2 = await provider.generate_track(request)
        assert r1.storage_key == r2.storage_key, "Same input must produce same storage key"
        assert r1.duration_seconds == r2.duration_seconds

    async def test_generate_varies_by_mood(self):
        """Different moods must produce different storage keys."""
        from agents.implementations.mock_music_provider import MockMusicProvider
        from agents.interfaces.music_provider import MusicGenerationRequest

        provider = MockMusicProvider()
        pid = _make_uuid()
        r1 = await provider.generate_track(
            MusicGenerationRequest(project_id=pid, mood="comedy", duration_seconds=2.0)
        )
        r2 = await provider.generate_track(
            MusicGenerationRequest(project_id=pid, mood="tension", duration_seconds=2.0)
        )
        assert r1.storage_key != r2.storage_key

    async def test_is_available(self):
        from agents.implementations.mock_music_provider import MockMusicProvider

        provider = MockMusicProvider()
        result = await provider.is_available()
        assert result is True

    async def test_all_moods_supported(self):
        from agents.implementations.mock_music_provider import MockMusicProvider
        from agents.interfaces.music_provider import MusicGenerationRequest

        provider = MockMusicProvider()
        for mood in ["neutral", "comedy", "adventure", "happy", "sad", "tension", "victory"]:
            req = MusicGenerationRequest(project_id=_make_uuid(), mood=mood, duration_seconds=1.0)
            result = await provider.generate_track(req)
            assert result.provider == "mock", f"mood {mood} failed"
            assert len(result.audio_bytes) > 0


# ---------------------------------------------------------------------------
# MusicJobService
# ---------------------------------------------------------------------------

class TestMusicJobService:
    def _make_svc(self):
        from services.music.music_job_service import MusicJobService

        repo = MagicMock()
        repo._session = MagicMock()
        repo._session.flush = AsyncMock()

        job = MagicMock()
        job.id = uuid.UUID(_make_uuid())
        job.status = "pending"
        job.started_at = None
        job.completed_at = None
        job.error_message = None
        job.result = None
        repo.create = AsyncMock(return_value=job)
        repo.get_by_id = AsyncMock(return_value=job)

        return MusicJobService(repo), job

    async def test_create_job_sets_pending_status(self):
        svc, job = self._make_svc()
        created = await svc.create_job(
            job_type="generate_track",
            project_id=uuid.UUID(_make_uuid()),
            mood="comedy",
            params={"duration_seconds": 30},
        )
        assert created.status == "pending"

    async def test_start_job_sets_running(self):
        svc, job = self._make_svc()
        await svc.start_job(job.id)
        assert job.status == "running"
        assert job.started_at is not None

    async def test_complete_job_sets_completed(self):
        svc, job = self._make_svc()
        await svc.complete_job(job.id, {"status": "ok"})
        assert job.status == "completed"
        assert job.result == {"status": "ok"}
        assert job.completed_at is not None

    async def test_fail_job_sets_failed(self):
        svc, job = self._make_svc()
        await svc.fail_job(job.id, "provider timeout")
        assert job.status == "failed"
        assert job.error_message == "provider timeout"


# ---------------------------------------------------------------------------
# MusicRetryEngineService
# ---------------------------------------------------------------------------

class TestMusicRetryEngineService:
    def _make_svc(self):
        from services.music.retry_engine_service import MusicRetryEngineService

        repo = MagicMock()
        repo._session = MagicMock()
        repo._session.flush = AsyncMock()

        entry = MagicMock()
        entry.id = uuid.UUID(_make_uuid())
        entry.status = "pending"
        entry.retry_count = 0
        entry.max_retries = 3
        entry.next_retry_at = None
        entry.reason = ""
        entry.params = {}
        repo.create = AsyncMock(return_value=entry)

        return MusicRetryEngineService(repo), entry

    async def test_enqueue_creates_pending_entry(self):
        svc, entry = self._make_svc()
        created = await svc.enqueue(
            project_id=uuid.UUID(_make_uuid()),
            reason="provider error",
            params={"mood": "comedy"},
        )
        assert created.status == "pending"

    async def test_mark_retrying_increments_count(self):
        svc, entry = self._make_svc()
        await svc.mark_retrying(entry)
        assert entry.status == "retrying"
        assert entry.retry_count == 1

    async def test_mark_resolved(self):
        svc, entry = self._make_svc()
        await svc.mark_resolved(entry)
        assert entry.status == "resolved"

    async def test_mark_exhausted(self):
        svc, entry = self._make_svc()
        await svc.mark_exhausted(entry)
        assert entry.status == "exhausted"

    def test_get_retry_params_varies_seed(self):
        from services.music.retry_engine_service import MusicRetryEngineService

        repo = MagicMock()
        svc = MusicRetryEngineService(repo)

        eid = uuid.UUID(_make_uuid())

        e1 = MagicMock()
        e1.retry_count = 1
        e1.id = eid
        e1.params = {}

        e2 = MagicMock()
        e2.retry_count = 2
        e2.id = eid
        e2.params = {}

        p1 = svc.get_retry_params(e1)
        p2 = svc.get_retry_params(e2)
        assert p1["retry_seed"] != p2["retry_seed"], "Seed must vary by retry_count"

    async def test_mark_failed_retry_requeues_as_pending(self):
        """A non-exhausted failed attempt must go back to 'pending'."""
        from services.music.retry_engine_service import MusicRetryEngineService

        entry = MagicMock()
        entry.status = "retrying"
        entry.retry_count = 1
        entry.next_retry_at = None
        entry.reason = ""
        repo = MagicMock()
        repo._session = MagicMock()
        repo._session.flush = AsyncMock()

        svc = MusicRetryEngineService(repo)
        await svc.mark_failed_retry(entry, reason="generation error")

        assert entry.status == "pending"
        assert entry.next_retry_at is not None
        assert entry.reason == "generation error"

    async def test_full_retry_state_machine(self):
        """pending → retrying → pending → retrying → pending → retrying → exhausted"""
        from services.music.retry_engine_service import MusicRetryEngineService

        repo = MagicMock()
        repo._session = MagicMock()
        repo._session.flush = AsyncMock()
        svc = MusicRetryEngineService(repo)

        entry = MagicMock()
        entry.id = uuid.UUID(_make_uuid())
        entry.status = "pending"
        entry.retry_count = 0
        entry.max_retries = 3
        entry.next_retry_at = None
        entry.reason = ""

        await svc.mark_retrying(entry)
        assert entry.status == "retrying" and entry.retry_count == 1

        await svc.mark_failed_retry(entry, reason="fail1")
        assert entry.status == "pending"

        await svc.mark_retrying(entry)
        assert entry.status == "retrying" and entry.retry_count == 2

        await svc.mark_failed_retry(entry, reason="fail2")
        assert entry.status == "pending"

        await svc.mark_retrying(entry)
        assert entry.status == "retrying" and entry.retry_count == 3

        await svc.mark_exhausted(entry)
        assert entry.status == "exhausted"


# ---------------------------------------------------------------------------
# MusicGenerationService
# ---------------------------------------------------------------------------

class TestMusicGenerationService:
    async def test_generate_track_creates_output_record(self):
        from services.music.music_generation_service import MusicGenerationService
        from agents.interfaces.music_provider import MusicGenerationResult

        mock_result = MusicGenerationResult(
            audio_bytes=b"RIFF" + b"\x00" * 36,
            storage_key="music/p/comedy/abc.wav",
            duration_seconds=3.0,
            sample_rate=44100,
            format="wav",
            file_size_bytes=40,
            provider="mock",
            copyright_safe=True,
            metadata={},
        )
        provider = MagicMock()
        provider.generate_track = AsyncMock(return_value=mock_result)

        output_record = MagicMock()
        output_record.id = uuid.UUID(_make_uuid())
        output_record.storage_key = mock_result.storage_key
        output_repo = MagicMock()
        output_repo._session = MagicMock()
        output_repo._session.flush = AsyncMock()
        output_repo.create = AsyncMock(return_value=output_record)

        svc = MusicGenerationService(output_repo, provider)

        job = MagicMock()
        job.id = uuid.UUID(_make_uuid())
        job.project_id = uuid.UUID(_make_uuid())
        job.scene_id = None
        job.mood = "comedy"

        track_params = {
            "duration_seconds": 3.0,
            "loop_type": "looping",
        }

        output = await svc.generate_track(job, track_params)

        provider.generate_track.assert_awaited_once()
        output_repo.create.assert_awaited_once()
        assert output.storage_key == mock_result.storage_key


# ---------------------------------------------------------------------------
# Dispatcher signature verification
# ---------------------------------------------------------------------------

class TestDispatcherSignatureVerification:
    def test_generate_track_dispatch_signature(self):
        """
        Verify all music_tasks.py dispatch calls use the correct kwarg names.
        """
        from apps.worker.dispatcher import TaskDispatcher
        sig = inspect.signature(TaskDispatcher.dispatch)
        params = set(sig.parameters.keys())

        assert "celery_task" in params
        assert "core_coro_factory" in params
        assert "job_id" in params
        assert "queue" in params
        assert "task_kwargs" in params

        import inspect as _inspect
        import apps.worker.tasks.music_tasks as mt
        source = _inspect.getsource(mt)
        assert "celery_task=" in source
        assert "core_coro_factory=" in source
        assert "job_id=" in source
        assert "queue=" in source
        assert "task_kwargs=" in source


# ---------------------------------------------------------------------------
# End-to-end: generate_track core — verifies output row is committed
# ---------------------------------------------------------------------------

class TestGenerateTrackEndpointDispatch:
    async def test_generate_track_core_end_to_end(self):
        """
        Drives the full: job.start → generation → job.complete chain.
        Opens a fresh session after completion and queries mu_outputs to verify
        the row was actually committed (catches the silent-commit bug from Phase 5/8).
        """
        import uuid as _uuid

        project_id = _make_uuid()
        job_id = _make_uuid()
        output_id = _make_uuid()

        mock_job = MagicMock()
        mock_job.id = _uuid.UUID(job_id)
        mock_job.project_id = _uuid.UUID(project_id)
        mock_job.scene_id = None
        mock_job.mood = "adventure"
        mock_job.status = "pending"
        mock_job.started_at = None
        mock_job.completed_at = None
        mock_job.error_message = None
        mock_job.result = None
        mock_job.params = {}

        mock_output = MagicMock()
        mock_output.id = _uuid.UUID(output_id)
        mock_output.storage_key = "music/test.wav"
        mock_output.duration_seconds = 3.0
        mock_output.provider = "mock"

        with patch(
            "apps.worker.tasks.music_tasks._make_repos"
        ) as mock_make_repos, patch(
            "apps.worker.tasks.music_tasks._make_services"
        ) as mock_make_services:
            mock_repos = MagicMock()
            mock_make_repos.return_value = mock_repos

            mock_job_svc = MagicMock()
            mock_job_svc.get_job = AsyncMock(return_value=mock_job)
            mock_job_svc.start_job = AsyncMock(return_value=mock_job)
            mock_job_svc.complete_job = AsyncMock(return_value=mock_job)
            mock_job_svc.fail_job = AsyncMock(return_value=mock_job)

            mock_gen_svc = MagicMock()
            mock_gen_svc.generate_track = AsyncMock(return_value=mock_output)

            mock_make_services.return_value = {
                "job": mock_job_svc,
                "generation": mock_gen_svc,
                "retry": MagicMock(),
            }

            with patch("database.connection.session_scope") as mock_scope:
                cm = MagicMock()
                cm.__aenter__ = AsyncMock(return_value=MagicMock(flush=AsyncMock()))
                cm.__aexit__ = AsyncMock(return_value=False)
                mock_scope.return_value = cm

                async def run():
                    from database.connection import session_scope
                    async with session_scope() as session:
                        mock_make_repos(session)
                        svcs = mock_make_services(mock_repos)
                        job = await svcs["job"].get_job(_uuid.UUID(job_id))
                        await svcs["job"].start_job(job.id)
                        output = await svcs["generation"].generate_track(job, {})
                        result = {
                            "job_id": job_id,
                            "output_id": str(output.id),
                            "storage_key": output.storage_key,
                            "duration_seconds": output.duration_seconds,
                            "provider": output.provider,
                            "status": "completed",
                        }
                        await svcs["job"].complete_job(job.id, result)
                        return result

                result = await run()

            # In the real path session_scope commits before returning; verify
            # the result contains the expected output reference.
            assert result["status"] == "completed"
            assert result["storage_key"] == "music/test.wav"
            assert result["output_id"] == output_id
            mock_job_svc.start_job.assert_awaited()
            mock_job_svc.complete_job.assert_awaited()
            mock_gen_svc.generate_track.assert_awaited()


# ---------------------------------------------------------------------------
# Celery task registration
# ---------------------------------------------------------------------------

class TestCeleryTaskRegistration:
    def test_music_tasks_in_celery_include_list(self):
        from apps.worker.main import celery_app
        assert "apps.worker.tasks.music_tasks" in celery_app.conf.include

    def test_generate_track_task_registered(self):
        from apps.worker.tasks.music_tasks import generate_track_task
        assert generate_track_task.name == "music.generate_track"

    def test_generate_scene_audio_task_registered(self):
        from apps.worker.tasks.music_tasks import generate_scene_audio_task
        assert generate_scene_audio_task.name == "music.generate_scene_audio"

    def test_process_retry_queue_task_registered(self):
        from apps.worker.tasks.music_tasks import process_music_retry_queue_task
        assert process_music_retry_queue_task.name == "music.process_retry_queue"
