from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

CATALOG_PATH = Path(__file__).resolve().parents[2] / "data" / "object_catalog.json"


@dataclass(frozen=True)
class CatalogEntry:
    stem: str
    label: str
    label_ko: str
    base_prompt: str
    type: str
    scene: str
    scene_ko: str
    description_ko: str
    scene_candidates: tuple[str, ...] = ()
    scene_candidates_ko: tuple[str, ...] = ()
    scene_elaborated_ko: tuple[str, ...] = ()

    def all_scenes(self) -> list[str]:
        """Primary scene + all candidates, in order."""
        return [self.scene, *self.scene_candidates]


def load_catalog(path: Path = CATALOG_PATH) -> list[CatalogEntry]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    return [
        CatalogEntry(
            stem=item["stem"],
            label=item["label"],
            label_ko=item["label_ko"],
            base_prompt=item["base_prompt"],
            type=item["type"],
            scene=item["scene"],
            scene_ko=item["scene_ko"],
            description_ko=item["description_ko"],
            scene_candidates=tuple(item.get("scene_candidates", [])),
            scene_candidates_ko=tuple(item.get("scene_candidates_ko", [])),
            scene_elaborated_ko=tuple(item.get("scene_elaborated_ko", [])),
        )
        for item in raw
    ]


def get_entry(stem: str, path: Path = CATALOG_PATH) -> CatalogEntry:
    entries = {e.stem: e for e in load_catalog(path)}
    if stem not in entries:
        raise ValueError(f"Object '{stem}' not found in catalog. Available: {sorted(entries)}")
    return entries[stem]
