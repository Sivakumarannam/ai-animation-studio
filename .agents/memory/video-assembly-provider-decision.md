---
name: Video assembly provider decision
description: Why VideoAssemblyService does not use FFmpegRenderer/RendererProvider
---

## Rule
Phase 10 VideoAssemblyService DOES NOT use FFmpegRenderer.render() or RendererProvider.
It queries an_render_outputs / vo_outputs / mu_outputs tables directly and calls FFmpeg itself.

**Why:** FFmpegRenderer.render() accepts SceneRenderSpec with background_url/audio_url strings
written by in-memory pipeline steps. Phase 10 works from persisted DB records with
`mock://...` or MinIO storage keys. Cross-table queries and the duration quality gate
don't fit inside RendererProvider.render().

**How to apply:** If a real storage backend is added, VideoAssemblyService._ffmpeg_assemble()
already has the FFmpeg concat path. Add a file-resolver method that maps storage_key →
local temp path (download from MinIO), then _have_real_files() returns True and real
assembly runs automatically.
