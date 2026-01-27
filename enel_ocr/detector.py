# -*- coding: ascii -*-
from __future__ import annotations

import json
import unicodedata
from pathlib import Path

from .ocr.crop import ImageCropper
from .ocr.engine import run_ocr

_HEADERS_PATH = Path(__file__).resolve().parent / "layouts" / "headers.json"


def _normalize_text(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text)
    without_accents = "".join(
        char for char in normalized if not unicodedata.combining(char)
    )
    return " ".join(without_accents.upper().split())


def _parse_region(region: dict) -> tuple[int, int, int, int] | None:
    try:
        x = int(float(region["x"]))
        y = int(float(region["y"]))
        w = int(float(region["w"]))
        h = int(float(region["h"]))
    except (KeyError, TypeError, ValueError):
        return None

    if w <= 0 or h <= 0:
        return None

    return (x, y, w, h)


def detect_layout(ocr, cropper: ImageCropper) -> str:
    if not _HEADERS_PATH.exists():
        return "v1"

    with _HEADERS_PATH.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)

    v1_rules = payload.get("v1", {})
    anchors = [_normalize_text(str(anchor)) for anchor in v1_rules.get("anchors", [])]
    region = v1_rules.get("region", {})
    coords = _parse_region(region)
    if not coords or not anchors:
        return "v1"

    image_np = cropper.crop_ndarray(coords)
    texts, _boxes, _scores = run_ocr(ocr, image_np)
    haystack = _normalize_text(" ".join(texts))

    if any(anchor in haystack for anchor in anchors):
        return "v1"

    if "v2" in payload:
        return "v2"

    return "v1"
