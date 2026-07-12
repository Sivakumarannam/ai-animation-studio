---
name: ImageProvider interface contract
description: How ImageProvider.generate_image()/generate() must be called, and the mock/real provider selection pattern for Phase 6 asset generation.
---

`ImageProvider` (agents/interfaces/image_provider.py) takes a single `ImageGenerationRequest`
dataclass (`generate_image(request)`; `generate(request)` is a backward-compat alias, not a
flat-kwargs entrypoint) and returns an `ImageGenerationResult` dataclass (`image_bytes`, `width`,
`height`, `format`, `model`, `seed`, `metadata`) — not a dict. A caller that passes flat kwargs like
`prompt=`, `cfg_scale=`, `sampler=` or reads the result via `.get("image_data")` will raise
`TypeError: got an unexpected keyword argument 'prompt'`.

**Why:** `ComfyUIProvider` is the only production implementation and is written correctly against
the dataclass contract, so the interface is the source of truth — the caller drifted, not the
provider.

Also: unlike every other AI provider in this codebase (LLM, embedding, vector store, research,
evaluation — all default to a zero-dependency "mock" and opt into a real backend via a settings
string), `_register_image()` in `agents/provider_factory.py` used to always instantiate
`ComfyUIProvider` unconditionally, so asset generation could never complete without a real ComfyUI
server. Fixed by adding `agents/implementations/mock_image_provider.py` (deterministic placeholder
PNGs via Pillow) and an `AG_IMAGE_PROVIDER` setting (default `"mock"`) following the same pattern as
`SI_AI_PROVIDER`/`EMBEDDING_PROVIDER`.

**How to apply:** when wiring a new AI-backed feature, always give it a "mock" default provider
option gated by a settings string, matching this project's established convention — don't assume a
real external backend (ComfyUI, Ollama, etc.) is available in this environment.
