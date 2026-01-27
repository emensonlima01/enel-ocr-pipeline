# -*- coding: ascii -*-
from dataclasses import dataclass
import json
from pathlib import Path


_LAYOUTS_DIR = Path(__file__).resolve().parent / "layouts"


@dataclass(frozen=True)
class Coordinates:
    description: str
    x: int
    y: int
    width: int
    height: int


def build_regions(layout_id: str = "v1") -> list[Coordinates]:
    layout_path = _LAYOUTS_DIR / f"{layout_id}.json"
    with layout_path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)

    regions = payload.get("regions", [])
    return [
        Coordinates(
            description=region["description"],
            x=region["x"],
            y=region["y"],
            width=region["width"],
            height=region["height"],
        )
        for region in regions
    ]
