---
name: MusicGenerationRequest dataclass field order
description: scene_id has a default value and must come after non-default fields like mood
---

## Rule
In `MusicGenerationRequest`, `mood: str` (no default) must be declared BEFORE `scene_id: str = ""` (has default). Python dataclasses raise `TypeError: non-default argument 'mood' follows default argument` otherwise.

**Why:** Python dataclasses require all fields with defaults to come after fields without defaults — same restriction as function signatures.

**How to apply:** When adding new optional fields to any provider interface dataclass, place them after all required (no-default) fields. Applies to MusicGenerationRequest and any future PhaseN request dataclasses.
