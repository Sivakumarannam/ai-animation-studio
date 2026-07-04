"""
AssetGenerationStep — generates background images for each scene using ImageProvider.
Characters images (sprites) are generated separately; this step handles scene backgrounds.
"""
from __future__ import annotations

import asyncio

import structlog

from agents.interfaces.image_provider import ImageGenerationRequest, ImageProvider
from workflow.context import WorkflowContext
from workflow.retry import RetryPolicy
from workflow.step import BaseStep, StepResult

logger = structlog.get_logger()


class AssetGenerationStep(BaseStep):
    """
    Step 4 — Generates scene background images via ImageProvider.

    Reads from context.step_results["scene_breakdown"]["scenes"]
    Reads from context.settings["image_style"]

    Writes to context.step_results["asset_generation"]:
      {
        "backgrounds": {scene_number: {"image_bytes_b64": str, "width": int, "height": int}},
        "generated_count": int,
        "failed_count": int,
      }
    """

    retry_policy = RetryPolicy(max_retries=2, base_delay=10.0, max_delay=60.0)

    def __init__(self, image_provider: ImageProvider) -> None:
        self._image = image_provider

    @property
    def name(self) -> str:
        return "asset_generation"

    @property
    def description(self) -> str:
        return "Generating scene backgrounds"

    async def execute(self, ctx: WorkflowContext) -> StepResult:
        scene_data = ctx.get_step_result("scene_breakdown", {})
        scenes = scene_data.get("scenes", [])
        style_hint = ctx.settings.get("image_style", "cartoon animation style, vibrant colors")
        width = ctx.settings.get("image_width", 1280)
        height = ctx.settings.get("image_height", 720)

        logger.info("asset_generation_start", run_id=ctx.run_id, scene_count=len(scenes))

        # Generate backgrounds concurrently (max 3 at a time to avoid OOM on ComfyUI)
        semaphore = asyncio.Semaphore(3)
        backgrounds: dict[str, dict] = {}
        failed = 0

        async def _generate_one(scene: dict) -> None:
            nonlocal failed
            scene_num = str(scene.get("scene_number", 0))
            visual_desc = scene.get("visual_description", scene.get("setting", ""))
            prompt = f"{visual_desc}, {style_hint}, high quality, detailed"
            negative = "blurry, low quality, text, watermark, logo, nsfw"

            async with semaphore:
                try:
                    result = await self._image.generate_image(
                        ImageGenerationRequest(
                            prompt=prompt,
                            negative_prompt=negative,
                            width=width,
                            height=height,
                            steps=20,
                        )
                    )
                    import base64
                    backgrounds[scene_num] = {
                        "image_bytes_b64": base64.b64encode(result.image_bytes).decode(),
                        "width": result.width,
                        "height": result.height,
                        "format": result.format,
                        "prompt": prompt,
                    }
                    logger.info("background_generated", scene=scene_num, run_id=ctx.run_id)
                except Exception as exc:
                    failed += 1
                    logger.warning("background_failed", scene=scene_num, error=str(exc), run_id=ctx.run_id)
                    # Store placeholder so downstream steps don't break
                    backgrounds[scene_num] = {
                        "image_bytes_b64": "",
                        "width": width,
                        "height": height,
                        "format": "png",
                        "error": str(exc),
                    }

        await asyncio.gather(*[_generate_one(s) for s in scenes])

        output = {
            "backgrounds": backgrounds,
            "generated_count": len(scenes) - failed,
            "failed_count": failed,
        }
        ctx.set_step_result(self.name, output)
        logger.info("asset_generation_complete", run_id=ctx.run_id, **output)
        return StepResult(success=True, output=output)
