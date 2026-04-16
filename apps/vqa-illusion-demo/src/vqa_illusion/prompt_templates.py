"""Deterministic IllusionDiffusion prompt builder.

Architecture: prompt_generation_architecture_illusion_diffusion_v2.md

Design:
- Shape type  → form control keywords (structure, not aesthetics)
- Scene       → semantic anchor (pre-assigned per object in catalog, not generated)
- Two tiers   → short (default, 10-25 tokens) / extended (fallback, 20-40 tokens)
- LLM         → NOT used here; reserved for QC-failure refinement only

Negative prompt structure:
  GLOBAL_NEGATIVE + TYPE_NEGATIVE_EXTRA (per shape type)
  All concealment constraints live in the negative — no "no X" in positive prompts.
"""
from __future__ import annotations

VALID_TYPES = {
    "rounded_mass",
    "elongated",
    "complex_silhouette",
    "vertical_structure",
    "thin_structure",
    "geometric_structure",
}

# Form control keyword per shape type
FORM_CONTROL: dict[str, str] = {
    "rounded_mass":        "smooth forms",
    "elongated":           "flowing forms",
    "complex_silhouette":  "layered forms",
    "vertical_structure":  "vertical depth",
    "thin_structure":      "minimal forms",
    "geometric_structure": "structured forms",
}

GLOBAL_NEGATIVE = (
    "low quality, blurry, noisy, oversaturated, cluttered composition, "
    "multiple subjects, centered character, portrait, watermark, "
    "deformed shapes, disconnected objects, "
    "icon-like shape, central focal subject, distinct recognizable subject"
)

# Type-specific negative keywords — blocks the most readable silhouette forms per shape category
TYPE_NEGATIVE_EXTRA: dict[str, str] = {
    "rounded_mass":        "isolated round object, single blob subject",
    "elongated":           "isolated stick figure, lone elongated subject",
    "complex_silhouette":  "icon-like outline, isolated creature shape, scattered isolated shapes",
    "vertical_structure":  "singular tall subject, lone vertical element, isolated vertical pole",
    "thin_structure":      "busy composition, intricate details, isolated thin line",
    "geometric_structure": "readable building, recognizable vehicle, distinct architectural subject",
}


def build_illusion_prompt(
    shape_type: str,
    scene: str,
    *,
    extended: bool = False,
) -> tuple[str, str]:
    """Return (positive_prompt, negative_prompt).

    Short  (default): "{scene}, {form_control}, soft light, cohesive composition"
    Extended (fallback): "a {scene} with {form_control}, subtle texture, soft light, cohesive composition"

    Args:
        shape_type: One of VALID_TYPES.
        scene:      Semantic anchor pre-assigned in catalog (terrain/mass/composition anchor).
        extended:   Use the extended fallback template (for QC re-generation).
    """
    if shape_type not in VALID_TYPES:
        raise ValueError(f"Unknown shape type '{shape_type}'. Valid: {sorted(VALID_TYPES)}")

    form = FORM_CONTROL[shape_type]

    if extended:
        positive = f"a {scene} with {form}, subtle texture, soft light, cohesive composition"
    else:
        positive = f"{scene}, {form}, soft light, cohesive composition"

    extra = TYPE_NEGATIVE_EXTRA.get(shape_type, "")
    negative = f"{GLOBAL_NEGATIVE}, {extra}" if extra else GLOBAL_NEGATIVE

    return positive, negative
