# -*- coding: ascii -*-
from __future__ import annotations

import re
import unicodedata


def _normalize_text(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    ascii_text = normalized.encode("ascii", "ignore").decode("ascii")
    return " ".join(ascii_text.lower().split())


def _extract_name(lines: list[str]) -> str:
    for line in lines:
        normalized = _normalize_text(line)
        if "cpf" in normalized or "cnpj" in normalized:
            continue
        if "cep" in normalized:
            continue
        if not normalized:
            continue
        return line.strip()
    return ""


def _extract_tax_number(lines: list[str]) -> str:
    for line in lines:
        normalized = _normalize_text(line)
        if "cpf" not in normalized and "cnpj" not in normalized:
            continue
        match = re.search(
            r"\b\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}\b|\b\d{3}\.\d{3}\.\d{3}-\d{2}\b",
            line,
        )
        if match:
            return match.group(0)
        digits = "".join(re.findall(r"\d+", line))
        if len(digits) in (11, 14):
            return digits
    return ""


def map(texts: list[str]) -> tuple[str, str]:
    lines = [text.strip() for text in texts if text and text.strip()]
    name = _extract_name(lines)
    tax_number = _extract_tax_number(lines)
    return name.upper(), tax_number.upper()
