---
name: Mock provider MinIO upload discipline
description: Every mock provider must upload real bytes to MinIO — not just save a storage_key string to the DB. Pattern and reference implementation.
---

# Mock provider MinIO upload discipline

**Rule:** Every phase's mock provider must return non-empty, valid bytes AND the service layer that persists the output row must upload those bytes to MinIO under `render_result.storage_key` before saving to DB.

**Why:** Phase 10 video assembly (and any future consumer) downloads files from MinIO by storage_key. If the provider only returns a string key with nothing behind it in MinIO, the download fails. The gap went undetected in Phases 7 because nothing tried to READ the animation file until Phase 10 triggered FFmpeg on it.

**Status by phase:**
- Phase 6 (images): ✅ uploads real PNG bytes via Pillow
- Phase 7 (animation): was broken — 8-byte `b"\x00\x00\x00\x08ftyp"` stub, no MinIO upload. Fixed 2026-07-18.
- Phase 8 (voice): ⚠️ MockVoiceProvider returns `b""` — likely same gap as Phase 7 was. Follow-up task #2.
- Phase 9 (music): ✅ uploads real WAV bytes via sine-tone generator

**Reference implementation:** `backend/agents/implementations/mock_music_provider.py` — generates real WAV bytes, returns them in `audio_bytes`, and the music engine service uploads them.

**Shared MP4 utility:** `backend/packages/utils/mp4_stub.py` — `MINIMAL_MP4_STUB` (~400 bytes) is a real ISO Base Media File. Use this for any mock that needs a valid MP4 container.

**How to apply:** When adding a new mock provider or reviewing an existing one:
1. Check that `video_bytes` / `audio_bytes` / `image_bytes` is non-empty and a valid container for its format.
2. Check that the service layer (`SceneCompositionService`, voice engine service, etc.) calls `MinIOStorage.upload_bytes(bucket, key, bytes, content_type)` after the provider call.
3. In tests, mock `MinIOStorage.from_settings` to avoid requiring a real MinIO server; assert `upload_bytes` was called with the correct bucket + key.
