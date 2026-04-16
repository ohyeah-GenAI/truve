"""IllusionDiffusion generation backend.

Swap backends via ILLUSION_BACKEND env var or --backend CLI flag:
    hf  (default) — AP123/IllusionDiffusion HF Space via direct HTTP queue API

Uses Gradio's HTTP queue protocol directly (no gradio_client) to avoid the
/info endpoint, which crashes on some Gradio server versions due to a boolean
JSON schema bug in gradio_client/utils.py.

Queue protocol:
    POST /upload              → upload image file
    POST /queue/join          → join queue, get event_id
    GET  /queue/data          → SSE stream, wait for process_completed

Future backends:
    replicate — lucataco/illusion-diffusion-hq (for production scale)
    runpod    — self-hosted IllusionDiffusion on RunPod
"""
from __future__ import annotations

import io
import json
import os
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol

import requests
from PIL import Image

from vqa_illusion.base_image_backend import GenerationResult


@dataclass
class IllusionRequest:
    base_image_path: Path
    prompt: str
    negative_prompt: str = (
        "low quality, blurry, noisy, oversaturated, cluttered composition, "
        "multiple subjects, centered character, portrait, watermark, "
        "deformed shapes, disconnected objects"
    )
    controlnet_conditioning_scale: float = 1.5
    guidance_scale: float = 7.5
    num_inference_steps: int = 40
    seed: int = -1  # -1 = random


class IllusionBackend(Protocol):
    def generate(self, req: IllusionRequest) -> GenerationResult:
        ...


class HFIllusionSpaceBackend:
    """IllusionDiffusion HF Space via direct Gradio HTTP queue API.

    Bypasses gradio_client.Client entirely to avoid the /info endpoint,
    which triggers a boolean-schema TypeError in some Gradio server versions.

    Protocol:
        POST /upload  → upload image, get server-side tmp path
        POST /queue/join  → enqueue request, get event_id
        GET  /queue/data  → SSE stream until process_completed
    """

    DEFAULT_SPACE = "AP123/IllusionDiffusion"
    API_NAME = "/inference"

    def __init__(self, hf_token: str | None = None, space: str | None = None) -> None:
        self._space = space or self.DEFAULT_SPACE
        owner, repo = self._space.split("/")
        # HF Spaces URL: owner-repo.hf.space (lowercase, underscores → hyphens)
        self._base_url = (
            f"https://{owner.lower()}-{repo.lower().replace('_', '-')}.hf.space"
        )
        self._headers: dict[str, str] = {}
        if hf_token:
            self._headers["Authorization"] = f"Bearer {hf_token}"
        self._fn_index = self._resolve_fn_index()
        print(f"  [HFIllusionSpaceBackend] space={self._space}  fn_index={self._fn_index}")

    def _resolve_fn_index(self) -> int:
        """Get fn_index for the /inference function from /config."""
        try:
            resp = requests.get(
                f"{self._base_url}/config",
                headers=self._headers,
                timeout=30,
            )
            resp.raise_for_status()
            config = resp.json()
            for dep in config.get("dependencies", []):
                if dep.get("api_name") == self.API_NAME:
                    return dep["id"]
        except Exception as e:
            print(f"  [HFIllusionSpaceBackend] /config lookup failed ({e}), defaulting fn_index=2")
        return 2  # fallback based on typical IllusionDiffusion app structure

    def _upload_image(self, path: Path) -> str:
        """Upload image to Space, return server-side tmp path."""
        with open(path, "rb") as f:
            resp = requests.post(
                f"{self._base_url}/upload",
                files={"files": (path.name, f, "image/png")},
                headers=self._headers,
                timeout=60,
            )
        resp.raise_for_status()
        return resp.json()[0]  # list of uploaded paths, take first

    def generate(self, req: IllusionRequest) -> GenerationResult:
        t0 = time.time()

        # 1. Upload base image
        server_path = self._upload_image(req.base_image_path)

        # 2. Join queue
        session_hash = uuid.uuid4().hex[:11]
        payload = {
            "data": [
                {"path": server_path, "meta": {"_type": "gradio.FileData"}},
                req.prompt,
                req.negative_prompt,
                float(req.guidance_scale),
                float(req.controlnet_conditioning_scale),
                0.0,   # control_guidance_start
                1.0,   # control_guidance_end
                1.0,   # upscaler_strength
                int(req.seed),
                "DPM++ Karras SDE",
            ],
            "fn_index": self._fn_index,
            "session_hash": session_hash,
        }
        resp = requests.post(
            f"{self._base_url}/queue/join",
            json=payload,
            headers=self._headers,
            timeout=30,
        )
        resp.raise_for_status()
        event_id = resp.json().get("event_id")

        # 3. Stream SSE until process_completed
        output_data = None
        with requests.get(
            f"{self._base_url}/queue/data",
            params={"session_hash": session_hash},
            headers={**self._headers, "Accept": "text/event-stream"},
            stream=True,
            timeout=300,
        ) as sse:
            sse.raise_for_status()
            for raw in sse.iter_lines():
                if not raw:
                    continue
                line = raw.decode() if isinstance(raw, bytes) else raw
                if not line.startswith("data:"):
                    continue
                event = json.loads(line[5:])
                msg = event.get("msg", "")
                if msg == "process_completed":
                    if not event.get("success", True):
                        raise RuntimeError(f"Space returned error: {event}")
                    output_data = event["output"]["data"]
                    break
                elif msg == "queue_full":
                    raise RuntimeError("Space queue is full, try again later")

        if output_data is None:
            raise RuntimeError("SSE stream ended without process_completed")

        # output_data[0] = image (FileData dict), output_data[1] = seed used
        out_item = output_data[0]
        if isinstance(out_item, dict):
            img_url = out_item.get("url") or out_item.get("path")
            if img_url and not img_url.startswith("http"):
                img_url = f"{self._base_url}/file={img_url}"
            img_resp = requests.get(img_url, headers=self._headers, timeout=60)
            img_resp.raise_for_status()
            image = Image.open(io.BytesIO(img_resp.content))
        else:
            image = Image.open(out_item)

        elapsed = time.time() - t0
        print(f"  [HFIllusionSpaceBackend] done in {elapsed:.1f}s")
        return GenerationResult(image=image, predict_time=elapsed, estimated_cost_usd=None)


_BACKENDS: dict[str, type] = {
    "hf": HFIllusionSpaceBackend,
}

_ENV_KEYS: dict[str, str | None] = {
    "hf": "HF_API_KEY",  # optional — raises rate limit without token
}


def get_illusion_backend(name: str | None = None) -> IllusionBackend:
    """Return an instantiated illusion backend.

    Priority: explicit name > ILLUSION_BACKEND env var > 'hf'
    """
    backend_name = name or os.environ.get("ILLUSION_BACKEND", "hf")
    if backend_name not in _BACKENDS:
        raise ValueError(
            f"Unknown illusion backend '{backend_name}'. Available: {sorted(_BACKENDS)}"
        )

    env_key = _ENV_KEYS[backend_name]
    token = os.environ.get(env_key) if env_key else None

    if backend_name == "hf":
        space = os.environ.get("ILLUSION_HF_SPACE")
        return HFIllusionSpaceBackend(hf_token=token, space=space)

    return _BACKENDS[backend_name](token)
