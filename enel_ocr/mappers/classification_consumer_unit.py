# -*- coding: ascii -*-
from __future__ import annotations

from .first_item import map as first_item_map


def map(texts: list, boxes=None) -> str:
    del boxes
    return first_item_map(texts)
