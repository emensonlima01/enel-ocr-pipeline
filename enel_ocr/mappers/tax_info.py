# -*- coding: ascii -*-
from __future__ import annotations

import re

from ..models import TaxInfo
from ._utils import build_items, group_items_by_row, normalize_text


def _extract_after_label(text: str, labels: list[str]) -> str:
    normalized = normalize_text(text)
    for label in labels:
        label_norm = normalize_text(label)
        index = normalized.find(label_norm)
        if index == -1:
            continue
        after = text[index + len(label_norm) :].strip(" :.-")
        if after:
            return after
    return ""


def _first_date(text: str) -> str:
    match = re.search(r"\d{2}/\d{2}/\d{4}", text)
    if not match:
        return ""
    return match.group(0).replace("/", "-")


def _first_digits(text: str, min_len: int) -> str:
    for match in re.findall(r"\d+", text):
        if len(match) >= min_len:
            return match
    return ""

def _extract_invoice_number(text: str) -> str:
    normalized = normalize_text(text)
    if "nota fiscal" not in normalized:
        return ""
    match = re.search(r"nota fiscal[^0-9]*(\d{6,})", text, re.IGNORECASE)
    if match:
        return match.group(1)
    return _first_digits(text, 6)


def _extract_access_key(text: str) -> str:
    normalized = normalize_text(text)
    label_index = normalized.find("chave de acesso")
    if label_index != -1:
        raw_after = text[label_index + len("chave de acesso") :]
        compact = "".join(re.findall(r"\d+", raw_after))
        if len(compact) >= 44:
            return compact
    compact_all = "".join(re.findall(r"\d+", text))
    if len(compact_all) >= 44:
        return compact_all[:44]
    return ""


def _extract_cfop(text: str) -> str:
    match = re.search(r"\bcfop\D*(\d{4})\b", text, re.IGNORECASE)
    return match.group(1) if match else ""


def _extract_date_after_label(text: str, labels: list[str]) -> str:
    normalized = normalize_text(text)
    for label in labels:
        label_norm = normalize_text(label)
        index = normalized.find(label_norm)
        if index == -1:
            continue
        after = text[index + len(label_norm) :]
        date = _first_date(after)
        if date:
            return date
    return ""

def map(texts: list, boxes: list) -> TaxInfo:
    items = build_items(texts, boxes)
    rows = group_items_by_row(items)
    lines = [" ".join(item["text"] for item in row).strip() for row in rows]
    lines = [line for line in lines if line]
    full_text = " ".join(lines)
    invoice_number = ""
    invoice_issue_date = ""
    access_key = ""
    cfop = ""
    presentation_date = ""

    for line in lines:
        normalized = normalize_text(line)
        if not invoice_number and "nota fiscal" in normalized:
            invoice_number = _extract_invoice_number(line)
            invoice_issue_date = (
                invoice_issue_date
                or _extract_date_after_label(line, ["data de emissao", "emissao"])
            )
        if not invoice_issue_date and "emissao" in normalized:
            invoice_issue_date = _extract_date_after_label(
                line, ["data de emissao", "emissao"]
            )
        if not access_key and "chave de acesso" in normalized:
            access_key = _extract_access_key(line)
        if not cfop and "cfop" in normalized:
            cfop = _extract_cfop(line)
        if not presentation_date and "apresentacao" in normalized:
            presentation_date = _extract_date_after_label(
                line, ["data de apresentacao", "apresentacao"]
            )

    if not invoice_number:
        invoice_number = _extract_invoice_number(full_text)
    if not invoice_issue_date:
        invoice_issue_date = _extract_date_after_label(
            full_text, ["data de emissao", "emissao"]
        )
    if not access_key:
        access_key = _extract_access_key(full_text)
    if not cfop:
        cfop = _extract_cfop(full_text)
    if not presentation_date:
        presentation_date = _extract_date_after_label(
            full_text, ["data de apresentacao", "apresentacao"]
        )

    return TaxInfo(
        invoice_number=invoice_number.upper(),
        invoice_issue_date=invoice_issue_date.upper(),
        access_key=access_key.upper(),
        cfop=cfop.upper(),
        presentation_date=presentation_date.upper(),
        tax_items=[],
    )
