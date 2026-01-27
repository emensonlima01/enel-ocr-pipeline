# -*- coding: ascii -*-
from __future__ import annotations

import re
import unicodedata

from ..models import CreditInfo


def _normalize_text(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    ascii_text = normalized.encode("ascii", "ignore").decode("ascii")
    return " ".join(ascii_text.upper().split())


def _extract_kwh(text: str, pattern: str) -> float | None:
    match = re.search(pattern, text)
    if not match:
        return None
    raw = match.group(1)
    raw = raw.replace(",", "")
    try:
        return float(raw)
    except ValueError:
        return None


def map(message: str) -> CreditInfo:
    if not message:
        return CreditInfo(
            injected_hfp_kwh=0.0,
            used_kwh=0.0,
            updated_kwh=0.0,
            expiring_kwh=0.0,
        )
    normalized = _normalize_text(message)
    injected = _extract_kwh(
        normalized, r"ENERGIA INJETADA HFP NO M.S:\s*([0-9.,]+)\s*KWH"
    )
    used = _extract_kwh(
        normalized, r"SALDO UTILIZADO NO M.S:\s*([0-9.,]+)\s*KWH"
    )
    updated = _extract_kwh(normalized, r"SALDO ATUALIZADO:\s*([0-9.,]+)\s*KWH")
    expiring = _extract_kwh(
        normalized,
        r"CREDITOS A EXPIRAR NO PROXIMO M.S:\s*([0-9.,]+)\s*KWH",
    )

    return CreditInfo(
        injected_hfp_kwh=injected or 0.0,
        used_kwh=used or 0.0,
        updated_kwh=updated or 0.0,
        expiring_kwh=expiring or 0.0,
    )
