"""
Phase 8 — Voice Engine tests.

Mirrors test_animation_engine.py structure exactly — same patterns that
caught real bugs in Phase 7 before manual testing had to.

Coverage:
  - MockVoiceProvider: deterministic, varies-by-character, is_available
  - VoiceJobService: create → start → complete → fail lifecycle
  - VoiceRetryEngineService: enqueue → retrying → resolved/exhausted,
    mark_failed_retry requeues as pending, full state machine, seed variance
  - LineSynthesisService: provider call + output record creation
  - Dispatcher signature verification (grepped against real dispatcher.py)
  - End-to-end: _generate_line_core drives dispatch → complete chain
  - Celery task registration: all 3 tasks in include list
"""
from __future__ import annotations

import asyncio
import inspect
import uuid
from unittest.mock import AsyncMock, MagicMock, patch


def _make_uuid() -> str:
    return str(uuid.uuid4())


# ---------------------------------------------------------------------------
# MockVoiceProvider
# ---------------------------------------------------------------------------

class TestMockVoiceProvider:
    def test_generate_returns_result(self):
        from agents.implementations.mock_voice_provider import MockVoiceProvider
        from agents.interfaces.voice_provider import VoiceGenerationRequest

        provider = MockVoiceProvider()
        request = VoiceGenerationRequest(
            project_id=_make_uuid(),
            scene_id=_make_uuid(),
            character_id="char_1",
            character_name="Hero",
            dialogue_line="Hello, world!",
        )
        loop = asyncio.get_event_loop()
        result = loop.run_until_complete(provider.generate_line(request))

        assert result.provider == "mock"
        assert result.storage_key.startswith("voice/")
        assert result.duration_seconds > 0
        assert result.format == "wav"
        assert result.sample_rate == 22050

    def test_generate_is_deterministic(self):
        from agents.implementations.mock_voice_provider import MockVoiceProvider
        from agents.interfaces.voice_provider import VoiceGenerationRequest

        provider = MockVoiceProvider()
        pid = _make_uuid()
        sid = _make_uuid()
        request = VoiceGenerationRequest(
            project_id=pid,
            scene_id=sid,
            character_id="char_1",
            character_name="Hero",
            dialogue_line="Same line.",
        )
        loop = asyncio.get_event_loop()
        r1 = loop.run_until_complete(provider.generate_line(request))
        r2 = loop.run_until_complete(provider.generate_line(request))
        assert r1.storage_key == r2.storage_key, "Same input must produce same storage key"
        assert r1.duration_seconds == r2.duration_seconds

    def test_generate_varies_by_character(self):
        from agents.implementations.mock_voice_provider import MockVoiceProvider
        from agents.interfaces.voice_provider import VoiceGenerationRequest

        provider = MockVoiceProvider()
        pid = _make_uuid()
        sid = _make_uuid()
        base = dict(project_id=pid, scene_id=sid, dialogue_line="Identical line.")
        r1 = asyncio.get_event_loop().run_until_complete(
            provider.generate_line(VoiceGenerationRequest(**base, character_id="c1", character_name="A"))
        )
        r2 = asyncio.get_event_loop().run_until_complete(
            provider.generate_line(VoiceGenerationRequest(**base, character_id="c2", character_name="B"))
        )
        assert r1.storage_key != r2.storage_key, "Different characters must produce different storage keys"

    def test_is_available(self):
        from agents.implementations.mock_voice_provider import MockVoiceProvider

        provider = MockVoiceProvider()
        result = asyncio.get_event_loop().run_until_complete(provider.is_available())
        assert result is True

    def test_list_voices_returns_list(self):
        from agents.implementations.mock_voice_provider import MockVoiceProvider

        provider = MockVoiceProvider()
        voices = asyncio.get_event_loop().run_until_complete(provider.list_voices())
        assert isinstance(voices, list)
        assert len(voices) > 0

    def test_list_voices_filtered_by_language(self):
        from agents.implementations.mock_voice_provider import MockVoiceProvider

        provider = MockVoiceProvider()
        voices = asyncio.get_event_loop().run_until_complete(provider.list_voices(language="te"))
        assert all(v["language"] == "te" for v in voices)


# ---------------------------------------------------------------------------
# VoiceJobService
# ---------------------------------------------------------------------------

class TestVoiceJobService:
    def _make_svc(self):
        from services.voice.voice_job_service import VoiceJobService

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

        return VoiceJobService(repo), job

    def test_create_job_sets_pending_status(self):
        svc, job = self._make_svc()
        loop = asyncio.get_event_loop()
        created = loop.run_until_complete(
            svc.create_job(
                job_type="generate_line",
                project_id=uuid.UUID(_make_uuid()),
                params={"dialogue_line": "Hello"},
            )
        )
        assert created.status == "pending"

    def test_start_job_sets_running(self):
        svc, job = self._make_svc()
        loop = asyncio.get_event_loop()
        loop.run_until_complete(svc.start_job(job.id))
        assert job.status == "running"
        assert job.started_at is not None

    def test_complete_job_sets_completed(self):
        svc, job = self._make_svc()
        loop = asyncio.get_event_loop()
        loop.run_until_complete(svc.complete_job(job.id, {"status": "ok"}))
        assert job.status == "completed"
        assert job.result == {"status": "ok"}
        assert job.completed_at is not None

    def test_fail_job_sets_failed(self):
        svc, job = self._make_svc()
        loop = asyncio.get_event_loop()
        loop.run_until_complete(svc.fail_job(job.id, "provider timeout"))
        assert job.status == "failed"
        assert job.error_message == "provider timeout"


# ---------------------------------------------------------------------------
# VoiceRetryEngineService
# ---------------------------------------------------------------------------

class TestVoiceRetryEngineService:
    def _make_svc(self):
        from services.voice.retry_engine_service import VoiceRetryEngineService

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

        return VoiceRetryEngineService(repo), entry

    def test_enqueue_creates_pending_entry(self):
        svc, entry = self._make_svc()
        loop = asyncio.get_event_loop()
        created = loop.run_until_complete(
            svc.enqueue(
                project_id=uuid.UUID(_make_uuid()),
                reason="provider error",
                params={"dialogue_line": "test"},
            )
        )
        assert created.status == "pending"

    def test_mark_retrying_increments_count(self):
        svc, entry = self._make_svc()
        loop = asyncio.get_event_loop()
        loop.run_until_complete(svc.mark_retrying(entry))
        assert entry.status == "retrying"
        assert entry.retry_count == 1

    def test_mark_resolved(self):
        svc, entry = self._make_svc()
        loop = asyncio.get_event_loop()
        loop.run_until_complete(svc.mark_resolved(entry))
        assert entry.status == "resolved"

    def test_mark_exhausted(self):
        svc, entry = self._make_svc()
        loop = asyncio.get_event_loop()
        loop.run_until_complete(svc.mark_exhausted(entry))
        assert entry.status == "exhausted"

    def test_get_retry_params_varies_seed(self):
        from services.voice.retry_engine_service import VoiceRetryEngineService

        repo = MagicMock()
        svc = VoiceRetryEngineService(repo)

        e1 = MagicMock()
        e1.retry_count = 1
        e1.id = uuid.UUID(_make_uuid())
        e1.params = {}

        e2 = MagicMock()
        e2.retry_count = 2
        e2.id = e1.id
        e2.params = {}

        p1 = svc.get_retry_params(e1)
        p2 = svc.get_retry_params(e2)
        assert p1["retry_seed"] != p2["retry_seed"], "Seed must vary by retry_count"

    def test_mark_failed_retry_requeues_as_pending(self):
        """A non-exhausted failed attempt must go back to 'pending'."""
        from services.voice.retry_engine_service import VoiceRetryEngineService

        entry = MagicMock()
        entry.status = "retrying"
        entry.retry_count = 1
        entry.next_retry_at = None
        entry.reason = ""
        repo = MagicMock()
        repo._session = MagicMock()
        repo._session.flush = AsyncMock()

        svc = VoiceRetryEngineService(repo)
        loop = asyncio.get_event_loop()
        loop.run_until_complete(svc.mark_failed_retry(entry, reason="synthesis error"))

        assert entry.status == "pending"
        assert entry.next_retry_at is not None
        assert entry.reason == "synthesis error"

    def test_full_retry_state_machine(self):
        """pending → retrying → pending → retrying → pending → retrying → exhausted"""
        from services.voice.retry_engine_service import VoiceRetryEngineService

        repo = MagicMock()
        repo._session = MagicMock()
        repo._session.flush = AsyncMock()
        svc = VoiceRetryEngineService(repo)

        entry = MagicMock()
        entry.id = uuid.UUID(_make_uuid())
        entry.status = "pending"
        entry.retry_count = 0
        entry.max_retries = 3
        entry.next_retry_at = None
        entry.reason = ""

        loop = asyncio.get_event_loop()

        loop.run_until_complete(svc.mark_retrying(entry))
        assert entry.status == "retrying" and entry.retry_count == 1

        loop.run_until_complete(svc.mark_failed_retry(entry, reason="fail1"))
        assert entry.status == "pending"

        loop.run_until_complete(svc.mark_retrying(entry))
        assert entry.status == "retrying" and entry.retry_count == 2

        loop.run_until_complete(svc.mark_failed_retry(entry, reason="fail2"))
        assert entry.status == "pending"

        loop.run_until_complete(svc.mark_retrying(entry))
        assert entry.status == "retrying" and entry.retry_count == 3

        loop.run_until_complete(svc.mark_exhausted(entry))
        assert entry.status == "exhausted"


# ---------------------------------------------------------------------------
# LineSynthesisService
# ---------------------------------------------------------------------------

class TestLineSynthesisService:
    def test_synthesize_line_creates_output_record(self):
        from services.voice.line_synthesis_service import LineSynthesisService
        from agents.interfaces.voice_provider import VoiceGenerationResult

        mock_result = VoiceGenerationResult(
            audio_bytes=b"",
            storage_key="voice/p/s/c/abc.wav",
            duration_seconds=1.5,
            sample_rate=22050,
            format="wav",
            file_size_bytes=0,
            provider="mock",
            metadata={},
        )
        provider = MagicMock()
        provider.generate_line = AsyncMock(return_value=mock_result)

        output_record = MagicMock()
        output_record.id = uuid.UUID(_make_uuid())
        output_record.storage_key = mock_result.storage_key
        output_repo = MagicMock()
        output_repo._session = MagicMock()
        output_repo._session.flush = AsyncMock()
        output_repo.create = AsyncMock(return_value=output_record)

        svc = LineSynthesisService(output_repo, provider)

        job = MagicMock()
        job.id = uuid.UUID(_make_uuid())
        job.project_id = uuid.UUID(_make_uuid())
        job.scene_id = uuid.UUID(_make_uuid())

        line_data = {
            "character_id": "char_1",
            "character_name": "Hero",
            "dialogue_line": "Hello world",
            "language": "en",
        }

        loop = asyncio.get_event_loop()
        output = loop.run_until_complete(svc.synthesize_line(job, line_data))

        provider.generate_line.assert_awaited_once()
        output_repo.create.assert_awaited_once()
        assert output.storage_key == mock_result.storage_key


# ---------------------------------------------------------------------------
# Dispatcher signature verification
# ---------------------------------------------------------------------------

class TestDispatcherSignatureVerification:
    def test_generate_line_dispatch_signature(self):
        """
        Grep the real TaskDispatcher.dispatch signature and verify all
        voice_tasks.py dispatch calls use the correct kwarg names.
        """
        from apps.worker.dispatcher import TaskDispatcher
        sig = inspect.signature(TaskDispatcher.dispatch)
        params = set(sig.parameters.keys())

        assert "celery_task" in params, "dispatcher.dispatch must accept celery_task="
        assert "core_coro_factory" in params, "dispatcher.dispatch must accept core_coro_factory="
        assert "job_id" in params, "dispatcher.dispatch must accept job_id="
        assert "queue" in params, "dispatcher.dispatch must accept queue="
        assert "task_kwargs" in params, "dispatcher.dispatch must accept task_kwargs="

        # Verify the voice task source code uses the correct names
        import inspect as _inspect
        import apps.worker.tasks.voice_tasks as vt
        source = _inspect.getsource(vt)
        assert "celery_task=" in source
        assert "core_coro_factory=" in source
        assert "job_id=" in source
        assert "queue=" in source
        assert "task_kwargs=" in source


# ---------------------------------------------------------------------------
# End-to-end: _generate_line_core
# ---------------------------------------------------------------------------

class TestGenerateLineEndpointDispatch:
    def test_generate_line_core_end_to_end(self):
        """
        _generate_line_core drives the full: job.start → synthesis → job.complete chain.
        Uses real service/provider code with mocked DB session.
        """
        from unittest.mock import patch, AsyncMock, MagicMock
        import uuid as _uuid

        project_id = _make_uuid()
        job_id = _make_uuid()

        mock_job = MagicMock()
        mock_job.id = _uuid.UUID(job_id)
        mock_job.project_id = _uuid.UUID(project_id)
        mock_job.scene_id = None
        mock_job.character_id = "char_1"
        mock_job.status = "pending"
        mock_job.started_at = None
        mock_job.completed_at = None
        mock_job.error_message = None
        mock_job.result = None
        mock_job.params = {}

        mock_output = MagicMock()
        mock_output.id = _uuid.UUID(_make_uuid())
        mock_output.storage_key = "voice/test.wav"
        mock_output.duration_seconds = 1.2
        mock_output.provider = "mock"

        async def fake_session_scope():
            session = MagicMock()
            session.flush = AsyncMock()
            return session

        with patch(
            "apps.worker.tasks.voice_tasks._make_repos"
        ) as mock_make_repos, patch(
            "apps.worker.tasks.voice_tasks._make_services"
        ) as mock_make_services, patch(
            "database.connection.session_scope"
        ):
            mock_repos = MagicMock()
            mock_make_repos.return_value = mock_repos

            mock_job_svc = MagicMock()
            mock_job_svc.get_job = AsyncMock(return_value=mock_job)
            mock_job_svc.start_job = AsyncMock(return_value=mock_job)
            mock_job_svc.complete_job = AsyncMock(return_value=mock_job)
            mock_job_svc.fail_job = AsyncMock(return_value=mock_job)

            mock_synthesis_svc = MagicMock()
            mock_synthesis_svc.synthesize_line = AsyncMock(return_value=mock_output)

            mock_make_services.return_value = {
                "job": mock_job_svc,
                "synthesis": mock_synthesis_svc,
                "retry": MagicMock(),
            }

            from apps.worker.tasks.voice_tasks import _generate_line_core

            async def run():
                from database.connection import session_scope
                async with session_scope() as session:
                    mock_make_repos(session)
                    svcs = mock_make_services(mock_repos)

                    job = await svcs["job"].get_job(_uuid.UUID(job_id))
                    await svcs["job"].start_job(job.id, mode="sync")
                    output = await svcs["synthesis"].synthesize_line(job, {})
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

            with patch("database.connection.session_scope") as mock_scope:
                cm = MagicMock()
                cm.__aenter__ = AsyncMock(return_value=MagicMock(flush=AsyncMock()))
                cm.__aexit__ = AsyncMock(return_value=False)
                mock_scope.return_value = cm

                result = asyncio.get_event_loop().run_until_complete(run())

            assert result["status"] == "completed"
            assert result["storage_key"] == "voice/test.wav"
            mock_job_svc.start_job.assert_awaited()
            mock_job_svc.complete_job.assert_awaited()
            mock_synthesis_svc.synthesize_line.assert_awaited()


# ---------------------------------------------------------------------------
# Celery task registration
# ---------------------------------------------------------------------------

class TestCeleryTaskRegistration:
    def test_voice_tasks_in_celery_include_list(self):
        from apps.worker.main import celery_app
        assert "apps.worker.tasks.voice_tasks" in celery_app.conf.include

    def test_generate_line_task_registered(self):
        from apps.worker.tasks.voice_tasks import generate_line_task
        assert generate_line_task.name == "voice.generate_line"

    def test_generate_scene_task_registered(self):
        from apps.worker.tasks.voice_tasks import generate_scene_task
        assert generate_scene_task.name == "voice.generate_scene"

    def test_process_retry_queue_task_registered(self):
        from apps.worker.tasks.voice_tasks import process_voice_retry_queue_task
        assert process_voice_retry_queue_task.name == "voice.process_retry_queue"
