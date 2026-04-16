"""LLM backends for IllusionDiffusion prompt refinement (QC fallback only).

Per v2 architecture, LLM is NOT used for initial prompt generation.
Initial prompts are built deterministically via prompt_templates.build_illusion_prompt().

LLM is invoked ONLY when a generated image fails QC (silhouette weak, background cluttered, etc.)
to minimally refine the existing prompt based on failure context.

Swap backends via PROMPT_BACKEND env var or --backend CLI flag:
    openai   (default) — gpt-4o-mini
    claude             — claude-haiku-4-5
"""
from __future__ import annotations

import os
from typing import Protocol

SYSTEM_PROMPT = (
    "You are an expert at writing prompts for IllusionDiffusion, "
    "a ControlNet-based image generation model that hides object silhouettes "
    "inside photorealistic background scenes. "
    "Given an object name and a short scene hint, generate a rich, detailed "
    "background scene prompt that will produce a stunning illusion image. "
    "Include specific scene details, lighting quality, atmosphere, and photography style keywords. "
    "Always start with 'RAW photo,' and end with '8k uhd, photorealistic, highly detailed'. "
    "Return only the prompt string, nothing else."
)

USER_TEMPLATE = (
    "Object: {label}\n"
    "Scene hint: {hint}\n"
    "Generate the IllusionDiffusion background prompt:"
)


class PromptBackend(Protocol):
    def generate(self, label: str, hint: str) -> str:
        ...


class OpenAIPromptBackend:
    """OpenAI: gpt-4o-mini (default)."""

    MODEL = "gpt-4o-mini"

    def __init__(self, api_key: str) -> None:
        self._api_key = api_key

    def generate(self, label: str, hint: str) -> str:
        from openai import OpenAI

        client = OpenAI(api_key=self._api_key)
        response = client.chat.completions.create(
            model=self.MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": USER_TEMPLATE.format(label=label, hint=hint)},
            ],
            temperature=0.7,
            max_tokens=200,
        )
        return response.choices[0].message.content.strip()


class ClaudePromptBackend:
    """Anthropic: claude-haiku-4-5."""

    MODEL = "claude-haiku-4-5"

    def __init__(self, api_key: str) -> None:
        self._api_key = api_key

    def generate(self, label: str, hint: str) -> str:
        import anthropic

        client = anthropic.Anthropic(api_key=self._api_key)
        message = client.messages.create(
            model=self.MODEL,
            max_tokens=200,
            system=SYSTEM_PROMPT,
            messages=[
                {"role": "user", "content": USER_TEMPLATE.format(label=label, hint=hint)},
            ],
        )
        return message.content[0].text.strip()


_BACKENDS: dict[str, type] = {
    "openai": OpenAIPromptBackend,
    "claude": ClaudePromptBackend,
}

_ENV_KEYS: dict[str, str] = {
    "openai": "OPENAI_API_KEY",
    "claude": "ANTHROPIC_API_KEY",
}


def get_prompt_backend(name: str | None = None) -> PromptBackend:
    backend_name = name or os.environ.get("PROMPT_BACKEND", "openai")
    if backend_name not in _BACKENDS:
        raise ValueError(f"Unknown backend '{backend_name}'. Available: {sorted(_BACKENDS)}")
    env_key = _ENV_KEYS[backend_name]
    api_key = os.environ.get(env_key)
    if not api_key:
        raise EnvironmentError(f"Backend '{backend_name}' requires {env_key} environment variable")
    return _BACKENDS[backend_name](api_key)
