# -*- coding: ascii -*-
from __future__ import annotations

import re
import unicodedata

from ..models import TaxInfo


def _normalize_text(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    ascii_text = normalized.encode("ascii", "ignore").decode("ascii")
    return " ".join(ascii_text.lower().split())


def _median(values: list[float]) -> float:
    if not values:
        return 0.0
    sorted_values = sorted(values)
    middle = len(sorted_values) // 2
    if len(sorted_values) % 2 == 1:
        return sorted_values[middle]
    return (sorted_values[middle - 1] + sorted_values[middle]) / 2


def _normalize_box_points(box) -> list[tuple[float, float]] | None:
    if box is None:
        return None
    if isinstance(box, (list, tuple)):
        if not box:
            return None
        first = box[0]
        if isinstance(first, (list, tuple)) and len(first) >= 2:
            return [(point[0], point[1]) for point in box]
        if isinstance(first, (int, float)):
            if len(box) == 4:
                x0, y0, x1, y1 = box
                return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
            if len(box) == 8:
                return [
                    (box[0], box[1]),
                    (box[2], box[3]),
                    (box[4], box[5]),
                    (box[6], box[7]),
                ]
    return None


def _build_items(texts: list, boxes: list) -> list[dict]:
    items = []
    for index, (text, box) in enumerate(zip(texts, boxes)):
        if not text or not box:
            continue
        points = _normalize_box_points(box)
        if not points:
            continue
        xs = [point[0] for point in points]
        ys = [point[1] for point in points]
        y_min = min(ys)
        y_max = max(ys)
        items.append(
            {
                "index": index,
                "text": text,
                "x": min(xs),
                "y_center": (y_min + y_max) / 2,
                "height": y_max - y_min,
            }
        )
    return items


def _group_items_by_row(items: list[dict]) -> list[list[dict]]:
    if not items:
        return []
    heights = [item["height"] for item in items if item["height"] > 0]
    limit = max(8, _median(heights) * 0.6)
    items_sorted = sorted(items, key=lambda item: item["y_center"])
    rows: list[dict] = []
    for item in items_sorted:
        if not rows:
            rows.append({"y_center": item["y_center"], "items": [item]})
            continue
        current = rows[-1]
        if abs(item["y_center"] - current["y_center"]) <= limit:
            current["items"].append(item)
            total = len(current["items"])
            current["y_center"] = (
                (current["y_center"] * (total - 1)) + item["y_center"]
            ) / total
        else:
            rows.append({"y_center": item["y_center"], "items": [item]})
    return [sorted(row["items"], key=lambda item: item["x"]) for row in rows]


def _extract_after_label(text: str, labels: list[str]) -> str:
    normalized = _normalize_text(text)
    for label in labels:
        label_norm = _normalize_text(label)
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
    normalized = _normalize_text(text)
    if "nota fiscal" not in normalized:
        return ""
    match = re.search(r"nota fiscal[^0-9]*(\d{6,})", text, re.IGNORECASE)
    if match:
        return match.group(1)
    return _first_digits(text, 6)


def _extract_access_key(text: str) -> str:
    normalized = _normalize_text(text)
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
    normalized = _normalize_text(text)
    for label in labels:
        label_norm = _normalize_text(label)
        index = normalized.find(label_norm)
        if index == -1:
            continue
        after = text[index + len(label_norm) :]
        date = _first_date(after)
        if date:
            return date
    return ""

def map(texts: list, boxes: list) -> TaxInfo:
    items = _build_items(texts, boxes)
    rows = _group_items_by_row(items)
    lines = [" ".join(item["text"] for item in row).strip() for row in rows]
    lines = [line for line in lines if line]
    full_text = " ".join(lines)
    invoice_number = ""
    invoice_issue_date = ""
    access_key = ""
    cfop = ""
    presentation_date = ""

    for line in lines:
        normalized = _normalize_text(line)
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
