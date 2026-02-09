# -*- coding: ascii -*-
from __future__ import annotations

from ._utils import normalize_text, parse_decimal
from .first_item import map as first_item_map
from ._utils import parse_decimal


def map(texts: list, boxes=None) -> Decimal:
    del boxes
    value = first_item_map(texts)
    if value:
        normalized = normalize_text(value)
        if any(keyword in normalized for keyword in ("pagar", "paga", "pagamento")):
            for text in texts[1:]:
                if not text:
                    continue
                candidate = str(text).strip()
                if candidate:
                    value = candidate
                    break
    return parse_decimal(value)
