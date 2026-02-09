# -*- coding: ascii -*-
from __future__ import annotations

from decimal import Decimal, InvalidOperation
import re
import unicodedata


def normalize_text(value: str, case: str = "lower") -> str:
    normalized = unicodedata.normalize("NFKD", value)
    ascii_text = normalized.encode("ascii", "ignore").decode("ascii")
    compact = " ".join(ascii_text.split())
    if case == "upper":
        return compact.upper()
    if case == "lower":
        return compact.lower()
    return compact


def median(values: list[float]) -> float:
    if not values:
        return 0.0
    sorted_values = sorted(values)
    middle = len(sorted_values) // 2
    if len(sorted_values) % 2 == 1:
        return sorted_values[middle]
    return (sorted_values[middle - 1] + sorted_values[middle]) / 2


def normalize_box_points(box) -> list[tuple[float, float]] | None:
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


def build_items(texts: list, boxes: list) -> list[dict]:
    items = []
    for index, (text, box) in enumerate(zip(texts, boxes)):
        if not text or not box:
            continue
        points = normalize_box_points(box)
        if not points:
            continue
        xs = [point[0] for point in points]
        ys = [point[1] for point in points]
        x_min = min(xs)
        x_max = max(xs)
        y_min = min(ys)
        y_max = max(ys)
        items.append(
            {
                "index": index,
                "text": text,
                "x": x_min,
                "x_center": (x_min + x_max) / 2,
                "y_center": (y_min + y_max) / 2,
                "height": y_max - y_min,
            }
        )
    return items


def group_items_by_row(items: list[dict]) -> list[list[dict]]:
    if not items:
        return []
    heights = [item["height"] for item in items if item["height"] > 0]
    limit = max(8, median(heights) * 0.6)
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


def parse_decimal(value: str) -> Decimal:
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


def parse_int(value: str) -> int:
    if not value:
        return 0
    cleaned = re.sub(r"[^0-9\-]", "", value).strip()
    if not cleaned:
        return 0
    try:
        return int(cleaned)
    except ValueError:
        return 0


def format_date(value: str) -> str:
    if not value:
        return ""
    match = re.search(r"\d{2}/\d{2}/\d{4}", value)
    if not match:
        return value.strip()
    return match.group(0).replace("/", "-")
