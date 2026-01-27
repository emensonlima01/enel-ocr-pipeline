# -*- coding: ascii -*-
from __future__ import annotations

import re

from .first_item import map as first_item_map


def _split_pair(text: str) -> tuple[str, str]:
    if not text:
        return "", ""
    raw = str(text)
    digits = re.findall(r"\d+", raw)
    if len(digits) >= 2:
        return digits[0], digits[1]
    if len(digits) == 1:
        return digits[0], ""
    parts = [part.strip() for part in re.split(r"[\\/|\\-]+", raw) if part.strip()]
    if len(parts) >= 2:
        return parts[0], parts[1]
    if parts:
        return parts[0], ""
    return raw.strip(), ""


def map(texts: list, boxes=None, layout_id: str = "v1") -> str:
    del boxes
    value = first_item_map(texts)
    if layout_id != "v2":
        return value
    _left, right = _split_pair(value)
    return right or value
