# -*- coding: ascii -*-
from __future__ import annotations

import re

from .first_item import map as first_item_map


def map(texts: list, boxes=None) -> int:
    del boxes
    value = first_item_map(texts)
    if not value:
        return 0
    cleaned = re.sub(r"[^0-9-]", "", value).strip()
    if not cleaned:
        return 0
    try:
        return int(cleaned)
    except ValueError:
        return 0
