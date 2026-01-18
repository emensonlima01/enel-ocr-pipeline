# -*- coding: ascii -*-
from __future__ import annotations


def map(texts: list, boxes: list | None = None) -> str:
    del boxes
    for text in texts:
        if not text:
            continue
        trimmed = str(text).strip()
        if trimmed:
            return trimmed.upper()
    return ""
