"""
MockLLMProvider — deterministic, zero-dependency AI provider for development and testing.

Responses are generated from templates keyed on prompt keywords so the output is
predictable across runs (important for tests). No network calls, no API keys required.

To switch to a real provider, change AI_PROVIDER in the environment — no code changes needed.
"""
from __future__ import annotations

import json
from typing import Any

from agents.interfaces.llm_provider import LLMMessage, LLMProvider, LLMResponse


_MOCK_MODEL = "mock/story-intelligence-v1"


class MockLLMProvider(LLMProvider):
    """
    Deterministic mock that returns pre-defined story intelligence responses.
    All outputs are syntactically valid JSON when generate_json() is used.
    """

    @property
    def provider_name(self) -> str:
        return _MOCK_MODEL

    async def is_available(self) -> bool:
        return True

    async def complete(
        self,
        messages: list[LLMMessage],
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs: Any,
    ) -> LLMResponse:
        prompt = " ".join(m.content for m in messages).lower()
        content = self._route(prompt)
        return LLMResponse(
            content=content,
            model=_MOCK_MODEL,
            tokens_used=len(content.split()),
            metadata={"mock": True},
        )

    # ------------------------------------------------------------------
    # Internal routing — pick a template based on prompt keywords
    # ------------------------------------------------------------------

    def _route(self, prompt: str) -> str:  # noqa: C901
        """
        Route on the most specific/unambiguous phrase first.

        IMPORTANT: several real prompts embed labels that look like keywords for
        *other* templates (e.g. the season-planning prompt includes a
        "Story idea: <premise>" label, and the evaluation prompt lists a
        "dialogue_score" dimension). Ordering must go from most-specific,
        least-ambiguous phrases to the most generic ones, and each phrase must
        be chosen so it cannot appear as an incidental substring of an
        unrelated prompt.
        """
        if "unique story ideas" in prompt or "story idea generator" in prompt:
            return self._story_ideas()
        if "plan a season" in prompt or "season planning ai" in prompt:
            return self._season_plan()
        if "plan episode" in prompt or "episode planning ai" in prompt:
            return self._episode_plan()
        if "break this episode into" in prompt or "scene planning ai" in prompt:
            return self._scene_breakdown()
        if "write dialogue" in prompt or "dialogue writer ai" in prompt:
            return self._dialogue()
        if "write narration" in prompt or "narration writer ai" in prompt:
            return self._narration()
        if "image prompt" in prompt or "visual prompt ai" in prompt:
            return self._image_prompt()
        if "animation prompt" in prompt or "animation prompt ai" in prompt:
            return self._animation_prompt()
        if "evaluate this episode" in prompt or "story quality evaluator ai" in prompt or "scale of 0-100" in prompt:
            return self._evaluation()
        if "build a detailed story world" in prompt or (
            "world" in prompt and ("build" in prompt or "creat" in prompt or "design" in prompt)
        ):
            return self._world_building()
        if "memory_type" in prompt or "story memory extraction ai" in prompt:
            return self._memory_summary()
        if "character consist" in prompt or "character profile" in prompt:
            return self._character_consistency()
        if "improve this episode" in prompt or "story improvement ai" in prompt:
            return self._episode_plan()
        if "story plan" in prompt or "plan the story" in prompt:
            return self._story_plan()
        # generic fallback
        return json.dumps({"result": "Mock response for: " + prompt[:80], "status": "ok"})

    # ------------------------------------------------------------------
    # Templates — all return valid JSON strings
    # ------------------------------------------------------------------

    def _story_ideas(self) -> str:
        return json.dumps([
            {
                "title": "The Missing Mango",
                "premise": "Grandmother's prized mango disappears the night before the festival; the whole family suspects each other.",
                "genre": "comedy",
                "tone": "light-hearted",
                "story_type": "comedy",
                "target_audience": "family",
                "estimated_episodes": 3,
                "themes": ["family", "trust", "festivals"],
            },
            {
                "title": "Raju's Big Secret",
                "premise": "Young Raju accidentally breaks Grandfather's radio and tries to fix it before anyone notices.",
                "genre": "comedy",
                "tone": "warm",
                "story_type": "comedy",
                "target_audience": "children",
                "estimated_episodes": 2,
                "themes": ["honesty", "problem-solving", "family"],
            },
            {
                "title": "The Night Visitor",
                "premise": "A traveling storyteller arrives in the village and each family member thinks he is someone different.",
                "genre": "comedy",
                "tone": "whimsical",
                "story_type": "comedy",
                "target_audience": "general",
                "estimated_episodes": 4,
                "themes": ["identity", "perception", "hospitality"],
            },
        ])

    def _story_plan(self) -> str:
        return json.dumps({
            "title": "The Missing Mango",
            "logline": "A missing mango reveals unexpected truths about a Telugu family on the eve of their biggest festival.",
            "three_act_structure": {
                "act_1": "Setup: The mango is discovered missing; accusations fly.",
                "act_2": "Confrontation: Each family member investigates; hilarious misunderstandings ensue.",
                "act_3": "Resolution: The crow is revealed as the culprit; the family laughs and reconciles.",
            },
            "themes": ["trust", "family bonds", "jumping to conclusions"],
            "character_arcs": {
                "Grandmother": "Moves from suspicion to laughter and acceptance.",
                "Raju": "Learns that honesty saves more trouble than silence.",
            },
            "season_count": 1,
            "estimated_total_episodes": 3,
        })

    def _season_plan(self) -> str:
        return json.dumps({
            "season_number": 1,
            "title": "Season 1 — The Mango Mysteries",
            "description": "Three episodes of escalating chaos around the annual mango festival.",
            "story_arc": "The family learns to trust each other through a series of comedic misadventures.",
            "episode_summaries": [
                {"episode_number": 1, "title": "The Disappearance", "summary": "The mango goes missing."},
                {"episode_number": 2, "title": "The Investigation", "summary": "Everyone suspects everyone."},
                {"episode_number": 3, "title": "The Culprit Revealed", "summary": "The crow is caught; family reunites."},
            ],
            "recurring_themes": ["family", "trust", "humor"],
            "character_development_goals": ["Raju becomes more honest", "Grandmother becomes more patient"],
        })

    def _episode_plan(self) -> str:
        return json.dumps({
            "episode_number": 1,
            "title": "The Disappearance",
            "summary": "On the morning of the festival, Grandmother's prize mango is gone. The chaos begins.",
            "opening": "Grandmother lovingly checks her mango tree at dawn; it is bare. She gasps.",
            "middle": "She wakes everyone one by one. Grandfather blames the neighbour's goat. Raju blames his sister. The neighbour blames Grandfather.",
            "ending": "As the argument peaks, everyone hears a crow cawing from the roof — with the mango in its beak.",
            "moral": "Assumptions create more problems than the problem itself.",
            "duration_target_seconds": 300,
            "scene_count": 5,
            "characters_featured": ["Grandmother", "Grandfather", "Raju", "Sister", "Neighbour"],
        })

    def _scene_breakdown(self) -> str:
        return json.dumps([
            {
                "scene_number": 1,
                "scene_goal": "Establish that the mango is missing and Grandmother is distressed.",
                "location": "Backyard mango tree, dawn",
                "character_names": ["Grandmother"],
                "camera_direction": "Close-up on empty branch, then pan to Grandmother's shocked face.",
                "duration_seconds": 45,
                "emotional_tone": "surprise → distress",
            },
            {
                "scene_number": 2,
                "scene_goal": "Wake the family and begin the accusations.",
                "location": "Kitchen and bedrooms",
                "character_names": ["Grandmother", "Grandfather", "Raju"],
                "camera_direction": "Quick cuts between doors being knocked.",
                "duration_seconds": 60,
                "emotional_tone": "urgency → comedy",
            },
            {
                "scene_number": 3,
                "scene_goal": "Accusations escalate; neighbour is blamed.",
                "location": "Front porch",
                "character_names": ["Grandfather", "Neighbour", "Raju"],
                "camera_direction": "Medium shot, two-character dialogue.",
                "duration_seconds": 75,
                "emotional_tone": "heated → absurd",
            },
            {
                "scene_number": 4,
                "scene_goal": "Family argument peaks; everyone is talking at once.",
                "location": "Living room",
                "character_names": ["Grandmother", "Grandfather", "Raju", "Sister"],
                "camera_direction": "Wide shot showing everyone gesturing.",
                "duration_seconds": 60,
                "emotional_tone": "chaos → peak comedy",
            },
            {
                "scene_number": 5,
                "scene_goal": "Reveal the crow; tension dissolves into laughter.",
                "location": "Rooftop",
                "character_names": ["Grandmother", "Grandfather", "Raju", "Sister", "Neighbour"],
                "camera_direction": "Pan up to rooftop crow with mango.",
                "duration_seconds": 60,
                "emotional_tone": "shock → laughter → relief",
            },
        ])

    def _dialogue(self) -> str:
        return json.dumps([
            {
                "character": "Grandmother",
                "line": "Aargh! My mango! My beautiful festival mango is gone!",
                "emotion": "distressed",
                "action": "waves arms at empty tree branch",
            },
            {
                "character": "Grandfather",
                "line": "That neighbour's goat again! I told you we needed a fence!",
                "emotion": "indignant",
                "action": "shakes finger toward next house",
            },
            {
                "character": "Raju",
                "line": "Maybe Sister took it. She was sneaking around last night.",
                "emotion": "shifty",
                "action": "avoids eye contact",
            },
            {
                "character": "Sister",
                "line": "Me?! I was asleep! Raju was the one who—",
                "emotion": "outraged",
                "action": "points accusingly",
            },
            {
                "character": "Crow",
                "line": "CAW!",
                "emotion": "triumphant",
                "action": "holds mango in beak on rooftop",
            },
        ])

    def _narration(self) -> str:
        return json.dumps({
            "narration": "Dawn broke quietly over the old mango tree — but not for long. "
                         "The news spread through the house faster than Grandmother's voice.",
        })

    def _image_prompt(self) -> str:
        return json.dumps({
            "image_prompt": "A wide-angle cartoon illustration of a traditional Telugu backyard at dawn. A large mango tree stands in the center, its branches empty. An elderly woman in a bright saree stands below, mouth open in shock, hands raised. Warm orange sunrise light, vivid colors, family-friendly animated style.",
            "style": "cartoon 2D animation",
            "mood": "comedic shock",
            "color_palette": ["warm orange", "deep green", "bright yellow", "red saree"],
        })

    def _animation_prompt(self) -> str:
        return json.dumps({
            "animation_prompt": "Character walks to mango tree. Reaches up. Finds nothing. Does a slow double-take. Eyes grow wide. Arms shoot out dramatically. Freeze frame for 0.5 seconds.",
            "key_motions": ["walk to tree", "reach-up gesture", "double-take", "arms out freeze"],
            "timing_seconds": 4.5,
            "style_notes": "Exaggerated cartoon expressions, squash-and-stretch on the double-take.",
        })

    def _evaluation(self) -> str:
        return json.dumps({
            "originality_score": 78.0,
            "consistency_score": 85.0,
            "creativity_score": 82.0,
            "grammar_score": 90.0,
            "flow_score": 80.0,
            "entertainment_score": 88.0,
            "educational_value_score": 75.0,
            "story_arc_score": 84.0,
            "dialogue_score": 86.0,
            "overall_score": 83.0,
            "approved": True,
            "feedback": {
                "strengths": ["Strong character voices", "Clear comedic arc", "Cultural authenticity"],
                "improvements": ["Opening could be punchier", "Neighbour character needs more screen time"],
                "suggestions": ["Add a running gag about the mango in episode 2", "Include a recipe scene for warmth"],
            },
        })

    def _world_building(self) -> str:
        return json.dumps({
            "name": "Sundarapuram Village",
            "description": "A fictional small Telugu village where a multi-generational family navigates modern and traditional life with warmth and humor.",
            "rules": [
                "Grandmother's opinion is law, even when wrong",
                "Festival season makes everyone slightly irrational",
                "Animals often reveal truths that humans cannot",
            ],
            "locations": {
                "family_home": "A large traditional house with a backyard mango tree",
                "backyard": "The garden with the famous mango tree",
                "kitchen": "Grandmother's domain — always fragrant with spices",
                "village_square": "Where the festival takes place",
                "neighbour_house": "Next door — always involved in misunderstandings",
            },
            "factions": [
                {"name": "The Elders", "members": ["Grandmother", "Grandfather"], "goal": "Preserve traditions"},
                {"name": "The Youngsters", "members": ["Raju", "Sister"], "goal": "Navigate between old and new"},
            ],
            "lore": "Sundarapuram has held the mango festival for 100 years. The village elder who grows the largest mango wins honorary chairmanship of the festival committee.",
        })

    def _memory_summary(self) -> str:
        return json.dumps({
            "memories_stored": [
                {"type": "character", "key": "Grandmother.personality", "value": {"traits": ["loving", "dramatic", "proud"], "catchphrase": "My mango!"}},
                {"type": "event", "key": "episode_1.mango_missing", "value": {"outcome": "crow took it", "moral": "assumptions are dangerous"}},
                {"type": "relationship", "key": "Grandfather-Neighbour", "value": {"status": "frenemies", "running_tension": "fence dispute"}},
                {"type": "joke", "key": "recurring.goat_blame", "value": {"setup": "Something goes wrong", "punchline": "Grandfather blames neighbour's goat"}},
            ],
            "summary": "Episode 1 established core family dynamics and the recurring goat-blame gag.",
        })

    def _character_consistency(self) -> str:
        return json.dumps({
            "characters": [
                {
                    "name": "Grandmother",
                    "physical": {"hair": "silver bun", "eyes": "dark brown", "clothing": "bright sarees"},
                    "personality": ["dramatic", "loving", "proud", "quick to accuse"],
                    "voice": "strong, expressive Telugu accent",
                    "catchphrases": ["My mango!", "In my day...", "I told you so!"],
                    "goals": ["Win the festival mango prize", "Keep the family together"],
                    "consistency_notes": "Never changes clothing style; always wears bangles",
                },
                {
                    "name": "Raju",
                    "physical": {"hair": "black, messy", "eyes": "brown", "clothing": "school uniform or casual"},
                    "personality": ["curious", "impulsive", "good-hearted", "often in trouble"],
                    "voice": "young, enthusiastic",
                    "catchphrases": ["It wasn't me!", "I have an idea!"],
                    "goals": ["Avoid getting blamed", "Help in his own clumsy way"],
                    "consistency_notes": "Always has ink stains on fingers",
                },
            ],
        })
