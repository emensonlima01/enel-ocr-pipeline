# -*- coding: ascii -*-
from __future__ import annotations

from ._utils import normalize_text
from .first_item import map as first_item_map


def map(texts: list, boxes=None) -> str:
    del boxes
    value = first_item_map(texts)
    if value:
        normalized = normalize_text(value)
        if normalized in ("mes/ano", "mes ano"):
            for text in texts[1:]:
                if not text:
                    continue
                candidate = str(text).strip()
                if candidate:
                    value = candidate
                    break
    if not value:
        return ""
    cleaned = value.strip()
    if len(cleaned) == 7 and cleaned[2] == "/":
        return cleaned.replace("/", "-")
    return cleaned
