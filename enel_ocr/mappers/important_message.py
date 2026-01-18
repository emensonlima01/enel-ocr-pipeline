# -*- coding: ascii -*-
from __future__ import annotations


def map(texts: list, boxes=None) -> str:
    del boxes
    parts = []
    for text in texts:
        if not text:
            continue
        trimmed = str(text).strip()
        if trimmed:
            parts.append(trimmed)
    return " ".join(parts).strip().upper()
