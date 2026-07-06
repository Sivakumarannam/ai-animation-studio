---
name: MockLLMProvider prompt routing pitfalls
description: Keyword-substring routing in mock LLM providers is fragile to prompt-label collisions; how to avoid/debug it.
---

When a mock/fake LLM provider routes prompts to response templates via `if keyword in prompt` substring checks, unrelated prompts can accidentally satisfy an earlier, wrong branch if they embed a label that happens to contain that keyword (e.g. a season-planning prompt containing `"Story idea: <premise>"` matches an idea-generation check; an evaluation prompt listing a `dialogue_score` dimension matches a dialogue-template check).

**Why:** This produces silent wrong-shape data (e.g. a list where a dict was expected) rather than an obvious error, and the resulting crash (`AttributeError: 'X' object has no attribute 'get'`) appears far from the actual routing bug, in whatever service code calls `.get()` on the result.

**How to apply:** When adding a new prompt/template pair to a mock LLM provider, or debugging an unexpected type coming out of `generate_json()`:
1. Order routing checks from most-specific/least-ambiguous phrase to most-generic, and verify no other real prompt in the codebase contains that phrase as an incidental substring.
2. Also verify each template's returned JSON *keys* actually match what the calling service reads via `.get(key)` — a routing fix doesn't help if the template shape itself doesn't match the consumer's contract (e.g. a narration template returning `opening_narration/scene_narrations/closing_narration` when the consumer reads `narration`).
3. Reproduce failures by calling the mock provider directly in isolation with the exact prompt string before assuming the bug is in the consuming service.
