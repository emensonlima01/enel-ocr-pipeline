# -*- coding: ascii -*-
from __future__ import annotations

import re
from ..models import TariffFlagPeriod
from ._utils import normalize_text

_COLOR_RANGE_RE = re.compile(
    r"(AMARELA|VERDE|VERMELHA)\s*:?\s*"
    r"(\d{1,2}[/-]\d{1,2}(?:[/-]\d{2,4})?)\s*(?:-|A|ATE)\s*"
    r"(\d{1,2}[/-]\d{1,2}(?:[/-]\d{2,4})?)"
)


def _normalize_date(value: str) -> str:
    match = re.match(r"^(\d{1,2})[/-](\d{1,2})(?:[/-](\d{2,4}))?$", value)
    if not match:
        return ""
    day = int(match.group(1))
    month = int(match.group(2))
    return f"{day:02d}-{month:02d}"


def map(message: str) -> list[TariffFlagPeriod]:
    if not message:
        return []
    normalized = normalize_text(message, case="upper")
    results: list[TariffFlagPeriod] = []
    seen = set()

    def add(flag: str, start_date: str, end_date: str) -> None:
        key = (flag, start_date, end_date)
        if key in seen:
            return
        seen.add(key)
        results.append(
            TariffFlagPeriod(
                flag=flag,
                start_date=start_date,
                end_date=end_date,
            )
        )

    for flag_name, start_date, end_date in _COLOR_RANGE_RE.findall(normalized):
        normalized_start = _normalize_date(start_date)
        normalized_end = _normalize_date(end_date)
        if not normalized_start or not normalized_end:
            continue
        add(flag_name, normalized_start, normalized_end)
        if len(results) >= 2:
            break

    return results
