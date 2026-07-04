import asyncio
import json
import uuid
from typing import Any

import httpx

from agents.interfaces.image_provider import ImageGenerationRequest, ImageGenerationResult, ImageProvider
from packages.core.exceptions import ProviderError


SDXL_WORKFLOW_TEMPLATE: dict[str, Any] = {
    "3": {"inputs": {"seed": 0, "steps": 20, "cfg": 7.5, "sampler_name": "euler", "scheduler": "normal", "denoise": 1, "model": ["4", 0], "positive": ["6", 0], "negative": ["7", 0], "latent_image": ["5", 0]}, "class_type": "KSampler"},
    "4": {"inputs": {"ckpt_name": "sd_xl_base_1.0.safetensors"}, "class_type": "CheckpointLoaderSimple"},
    "5": {"inputs": {"width": 1024, "height": 576, "batch_size": 1}, "class_type": "EmptyLatentImage"},
    "6": {"inputs": {"text": "", "clip": ["4", 1]}, "class_type": "CLIPTextEncode"},
    "7": {"inputs": {"text": "", "clip": ["4", 1]}, "class_type": "CLIPTextEncode"},
    "8": {"inputs": {"samples": ["3", 0], "vae": ["4", 2]}, "class_type": "VAEDecode"},
    "9": {"inputs": {"filename_prefix": "aistudio", "images": ["8", 0]}, "class_type": "SaveImage"},
}


class ComfyUIProvider(ImageProvider):
    """Image provider backed by a local ComfyUI instance."""

    def __init__(self, base_url: str = "http://localhost:8188") -> None:
        self._base_url = base_url.rstrip("/")

    @property
    def provider_name(self) -> str:
        return "comfyui/sdxl"

    async def generate_image(self, request: ImageGenerationRequest) -> ImageGenerationResult:
        workflow = json.loads(json.dumps(SDXL_WORKFLOW_TEMPLATE))
        workflow["6"]["inputs"]["text"] = request.prompt
        workflow["7"]["inputs"]["text"] = request.negative_prompt
        workflow["5"]["inputs"]["width"] = request.width
        workflow["5"]["inputs"]["height"] = request.height
        workflow["3"]["inputs"]["steps"] = request.steps
        workflow["3"]["inputs"]["cfg"] = request.guidance_scale
        workflow["3"]["inputs"]["seed"] = int(uuid.uuid4().int % (2**32))

        client_id = str(uuid.uuid4())
        payload = {"prompt": workflow, "client_id": client_id}

        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                queue_resp = await client.post(f"{self._base_url}/prompt", json=payload)
                queue_resp.raise_for_status()
                prompt_id = queue_resp.json()["prompt_id"]

                for _ in range(120):
                    await asyncio.sleep(2)
                    hist_resp = await client.get(f"{self._base_url}/history/{prompt_id}")
                    hist = hist_resp.json()
                    if prompt_id in hist and hist[prompt_id].get("outputs"):
                        outputs = hist[prompt_id]["outputs"]
                        for node_output in outputs.values():
                            images = node_output.get("images", [])
                            if images:
                                img_ref = images[0]
                                img_resp = await client.get(
                                    f"{self._base_url}/view",
                                    params={"filename": img_ref["filename"], "subfolder": img_ref.get("subfolder", ""), "type": img_ref.get("type", "output")},
                                )
                                img_resp.raise_for_status()
                                return ImageGenerationResult(
                                    image_bytes=img_resp.content,
                                    width=request.width,
                                    height=request.height,
                                    format="png",
                                    model="sdxl",
                                    metadata={"prompt_id": prompt_id},
                                )
                raise ProviderError("comfyui", "Image generation timed out")
        except httpx.HTTPError as e:
            raise ProviderError("comfyui", str(e)) from e

    async def is_available(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                r = await client.get(f"{self._base_url}/system_stats")
                return r.status_code == 200
        except Exception:
            return False
