from typing import Any

from plugins.base_plugin import ContentPlugin, PluginMetadata


class TeluguFamilyComedyPlugin(ContentPlugin):
    """
    First official plugin: Telugu Family Comedy Studio.
    Generates funny family-oriented 2D cartoon episodes in Telugu.
    All Telugu-specific logic lives here — never in the core platform.
    """

    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            id="telugu_family_comedy",
            name="Telugu Family Comedy Studio",
            version="1.0.0",
            description="Generate Telugu family comedy cartoon episodes with recurring characters",
            language="te",
            animation_style="cartoon_2d",
            content_rating="general",
            tags=["telugu", "comedy", "family", "cartoon", "2d"],
            author="AI Animation Studio",
        )

    def get_character_archetypes(self) -> list[dict[str, Any]]:
        return [
            {
                "name": "Amma",
                "name_local": "అమ్మ",
                "role": "mother",
                "personality": "caring, strict, funny, always worried about the family",
                "age_range": "35-45",
                "gender": "female",
                "typical_expressions": ["sighing", "scolding lovingly", "proud smiles"],
            },
            {
                "name": "Nanna",
                "name_local": "నాన్న",
                "role": "father",
                "personality": "lazy, funny, loves cricket, tries to escape chores",
                "age_range": "40-50",
                "gender": "male",
                "typical_expressions": ["sleeping", "watching TV", "pretending to work"],
            },
            {
                "name": "Alludu",
                "name_local": "అల్లుడు",
                "role": "son-in-law",
                "personality": "witty, mischievous, trying to impress in-laws",
                "age_range": "25-35",
                "gender": "male",
                "typical_expressions": ["nervous smiles", "scheming looks", "panic"],
            },
            {
                "name": "Ammayyi",
                "name_local": "అమ్మాయి",
                "role": "daughter",
                "personality": "smart, modern, mediates between husband and parents",
                "age_range": "22-30",
                "gender": "female",
                "typical_expressions": ["eye-rolling", "diplomatic smiles", "exasperation"],
            },
        ]

    def get_story_templates(self) -> list[dict[str, Any]]:
        return [
            {
                "id": "everyday_mishap",
                "title": "Everyday Family Mishap",
                "premise_template": "A simple daily task goes hilariously wrong in the family, causing a chain reaction of funny misunderstandings.",
                "genre": "family_comedy",
                "tone": "lighthearted",
                "typical_duration": 180,
            },
            {
                "id": "festival_chaos",
                "title": "Festival Preparation Chaos",
                "premise_template": "The family prepares for a Telugu festival but everything goes comically wrong.",
                "genre": "family_comedy",
                "tone": "festive",
                "typical_duration": 240,
            },
            {
                "id": "modern_vs_traditional",
                "title": "Modern vs Traditional",
                "premise_template": "A generational clash between old-school family values and modern ways leads to funny situations.",
                "genre": "family_comedy",
                "tone": "satirical",
                "typical_duration": 200,
            },
        ]

    def get_default_settings(self) -> dict[str, Any]:
        return {
            "language": "te",
            "animation_style": "cartoon_2d",
            "aspect_ratio": "16:9",
            "fps": 24,
            "resolution": "1080p",
            "background_style": "vibrant_indian_home",
            "subtitle_language": "te",
            "subtitle_font": "Noto Sans Telugu",
        }

    def get_prompt_context(self) -> dict[str, Any]:
        return {
            "language": "Telugu (తెలుగు)",
            "culture": "Telugu-speaking South Indian family",
            "setting": "Modern Telugu household with traditional values",
            "humor_style": "Situational family comedy with cultural references",
            "dialogue_style": "Mix of formal Telugu and colloquial Hyderabadi Telugu",
        }
