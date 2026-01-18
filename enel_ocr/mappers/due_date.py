# -*- coding: ascii -*-
from __future__ import annotations

from .first_item import map as first_item_map


def map(texts: list, boxes=None) -> str:
    del boxes
    value = first_item_map(texts)
    if not value:
        return ""
    cleaned = value.strip()
    if len(cleaned) == 10 and cleaned[2] == "/" and cleaned[5] == "/":
        return cleaned.replace("/", "-")
    return cleaned
