"""Base image generation backends.

Swap backends via BASE_IMAGE_BACKEND env var or --backend CLI flag:
    replicate  (default) — black-forest-labs/flux-schnell on Replicate
    hf         — black-forest-labs/FLUX.1-schnell on HF Inference API
"""
from __future__ import annotations

import io
import os
from dataclasses import dataclass
from typing import Protocol

from PIL import Image


# Approximate cost per second of GPU time (USD) per Replicate model
# https://replicate.com/pricing
REPLICATE_COST_PER_SEC: dict[str, float] = {
    "black-forest-labs/flux-schnell": 0.004,  # 실측 ~$0.004/image (2026-04-09)
    "black-forest-labs/flux-dev": 0.025,
    "black-forest-labs/flux-pro": 0.055,
}


@dataclass
class GenerationResult:
    image: Image.Image
    predict_time: float | None  # seconds, None if unavailable
    estimated_cost_usd: float | None


class BaseImageBackend(Protocol):
    def generate(self, prompt: str) -> GenerationResult:
        ...


class ReplicateFluxBackend:
    """Replicate: black-forest-labs/flux-schnell (default)."""

    MODEL = "black-forest-labs/flux-schnell"

    def __init__(self, api_token: str) -> None:
        self._api_token = api_token

    def generate(self, prompt: str) -> GenerationResult:
        import replicate

        client = replicate.Client(api_token=self._api_token)

        # Use predictions.create() to get timing metrics
        prediction = client.predictions.create(
            model=self.MODEL,
            input={"prompt": prompt, "num_outputs": 1},
        )
        prediction.wait()

        output = prediction.output[0]
        # replicate-python >= 1.0 returns FileOutput (has .read()),
        # older versions or certain models return a URL string.
        if isinstance(output, str):
            import urllib.request
            with urllib.request.urlopen(output, timeout=30) as resp:
                raw = resp.read()
        else:
            raw = output.read()
        image = Image.open(io.BytesIO(raw))

        predict_time = getattr(prediction.metrics, "predict_time", None) if prediction.metrics else None
        cost = REPLICATE_COST_PER_SEC.get(self.MODEL)

        return GenerationResult(
            image=image,
            predict_time=predict_time,
            estimated_cost_usd=cost,  # flux-schnell is flat-rate per image
        )


class HFInferenceBackend:
    """HuggingFace Inference API: black-forest-labs/FLUX.1-schnell."""

    MODEL = "black-forest-labs/FLUX.1-schnell"

    def __init__(self, api_key: str) -> None:
        self._api_key = api_key

    def generate(self, prompt: str) -> GenerationResult:
        from huggingface_hub import InferenceClient

        client = InferenceClient(token=self._api_key)
        image = client.text_to_image(prompt, model=self.MODEL)
        return GenerationResult(image=image, predict_time=None, estimated_cost_usd=None)


# Registry — add new backends here
_BACKENDS: dict[str, type] = {
    "replicate": ReplicateFluxBackend,
    "hf": HFInferenceBackend,
}

_ENV_KEYS: dict[str, str] = {
    "replicate": "REPLICATE_API_TOKEN",
    "hf": "HF_API_KEY",
}


def get_backend(name: str | None = None) -> BaseImageBackend:
    """Return an instantiated backend.

    Priority: explicit name > BASE_IMAGE_BACKEND env var > 'replicate'
    """
    backend_name = name or os.environ.get("BASE_IMAGE_BACKEND", "replicate")
    if backend_name not in _BACKENDS:
        raise ValueError(
            f"Unknown backend '{backend_name}'. Available: {sorted(_BACKENDS)}"
        )
    env_key = _ENV_KEYS[backend_name]
    api_key = os.environ.get(env_key)
    if not api_key:
        raise EnvironmentError(
            f"Backend '{backend_name}' requires {env_key} environment variable"
        )
    return _BACKENDS[backend_name](api_key)
