# -*- coding: ascii -*-
from __future__ import annotations

from .first_item import map as first_item_map
from ._utils import parse_decimal


def map(texts: list, boxes=None) -> Decimal:
    del boxes
    return parse_decimal(first_item_map(texts))
