# -*- coding: ascii -*-
from __future__ import annotations


def map(texts: list[str]) -> str:
    parts = [text.strip() for text in texts if text and text.strip()]
    return " ".join(parts).upper()
