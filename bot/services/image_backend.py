from __future__ import annotations

import asyncio
import base64
from abc import ABC, abstractmethod
from typing import Optional

import httpx

from config import Config

NEGATIVE_PROMPT = (
    "child, minor, underage, violence, gore, snuff, illegal content, "
    "watermark, blurry, low quality"
)

GENERATION_TIMEOUT = 90


class ImageBackend(ABC):
    @abstractmethod
    async def generate(self, prompt: str, negative_prompt: str = "") -> bytes:
        ...


class ReplicateBackend(ImageBackend):
    def __init__(self, api_key: str, model_version: str) -> None:
        self._api_key = api_key
        self._model_version = model_version
        self._base_url = "https://api.replicate.com/v1"

    async def generate(self, prompt: str, negative_prompt: str = "") -> bytes:
        headers = {
            "Authorization": f"Token {self._api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "version": self._model_version,
            "input": {
                "prompt": prompt,
                "negative_prompt": NEGATIVE_PROMPT + (f", {negative_prompt}" if negative_prompt else ""),
                "width": 768,
                "height": 1024,
                "num_inference_steps": 30,
                "guidance_scale": 7.5,
            },
        }

        async with httpx.AsyncClient(timeout=GENERATION_TIMEOUT) as client:
            resp = await client.post(
                f"{self._base_url}/predictions",
                headers=headers,
                json=payload,
            )
            resp.raise_for_status()
            prediction = resp.json()
            poll_url = prediction["urls"]["get"]

            deadline = asyncio.get_event_loop().time() + GENERATION_TIMEOUT
            delay = 1.0
            while asyncio.get_event_loop().time() < deadline:
                await asyncio.sleep(delay)
                poll = await client.get(poll_url, headers=headers)
                poll.raise_for_status()
                data = poll.json()
                status = data.get("status")
                if status == "succeeded":
                    output = data.get("output")
                    image_url = output[0] if isinstance(output, list) else output
                    img_resp = await client.get(image_url)
                    img_resp.raise_for_status()
                    return img_resp.content
                if status in ("failed", "canceled"):
                    raise RuntimeError(f"Replicate prediction {status}: {data.get('error')}")
                delay = min(delay * 1.5, 4.0)

        raise TimeoutError("Replicate generation timed out")


class StableDiffusionBackend(ImageBackend):
    def __init__(self, api_url: str, api_key: str = "") -> None:
        self._api_url = api_url.rstrip("/")
        self._api_key = api_key

    async def generate(self, prompt: str, negative_prompt: str = "") -> bytes:
        headers: dict[str, str] = {"Content-Type": "application/json"}
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"

        payload = {
            "prompt": prompt,
            "negative_prompt": NEGATIVE_PROMPT + (f", {negative_prompt}" if negative_prompt else ""),
            "width": 768,
            "height": 1024,
            "steps": 30,
            "cfg_scale": 7.5,
        }

        async with httpx.AsyncClient(timeout=GENERATION_TIMEOUT) as client:
            resp = await client.post(
                f"{self._api_url}/sdapi/v1/txt2img",
                headers=headers,
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()
            images = data.get("images")
            if not images:
                raise RuntimeError("SD API returned no images")
            return base64.b64decode(images[0])


def get_backend(cfg: Config) -> ImageBackend:
    if cfg.ACTIVE_BACKEND == "sd":
        return StableDiffusionBackend(cfg.SD_API_URL, cfg.SD_API_KEY)
    return ReplicateBackend(cfg.REPLICATE_API_KEY, cfg.REPLICATE_MODEL_VERSION)
