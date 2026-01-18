# -*- coding: ascii -*-
from __future__ import annotations

from decimal import Decimal, InvalidOperation
import re

from .first_item import map as first_item_map


def _parse_decimal(value: str) -> Decimal:
    if not value:
        return Decimal("0")
    cleaned = re.sub(r"[^0-9,.\-]", "", value).strip()
    if not cleaned:
        return Decimal("0")
    is_negative = cleaned.endswith("-")
    if is_negative:
        cleaned = cleaned[:-1].strip()
    if "," in cleaned and "." in cleaned:
        cleaned = cleaned.replace(".", "").replace(",", ".")
    elif "," in cleaned:
        cleaned = cleaned.replace(",", ".")
    try:
        parsed = Decimal(cleaned)
        return -parsed if is_negative else parsed
    except InvalidOperation:
        return Decimal("0")


def map(texts: list, boxes=None) -> Decimal:
    del boxes
    return _parse_decimal(first_item_map(texts))
