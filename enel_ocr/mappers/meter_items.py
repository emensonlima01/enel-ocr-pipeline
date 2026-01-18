# -*- coding: ascii -*-
from __future__ import annotations

from decimal import Decimal, InvalidOperation
import re
import unicodedata

from ..models import MeterItem

COLUMN_ORDER = [
    "meter_number",
    "segment_time",
    "reading_date_1",
    "reading_1",
    "reading_date_2",
    "reading_2",
    "multiplier_factor",
    "consumption_kwh",
    "number_of_days",
]
SECTION_TITLES = [
    "equipamentos de medicao e consumo no periodo",
]
HEADER_KEYWORDS = {
    "medidor",
    "horario",
    "segmento",
    "data",
    "leitura",
    "fator",
    "multiplicador",
    "consumo",
    "kwh",
    "dias",
}


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


def _parse_int(value: str) -> int:
    if not value:
        return 0
    cleaned = re.sub(r"[^0-9\-]", "", value).strip()
    if not cleaned:
        return 0
    try:
        return int(cleaned)
    except ValueError:
        return 0


def _format_date(value: str) -> str:
    if not value:
        return ""
    match = re.search(r"\d{2}/\d{2}/\d{4}", value)
    if not match:
        return value.strip()
    return match.group(0).replace("/", "-")


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


def _find_section_start(rows: list[list[dict]]) -> int | None:
    for index, row in enumerate(rows):
        row_text = " ".join(item["text"] for item in row)
        normalized = _normalize_text(row_text)
        if any(title in normalized for title in SECTION_TITLES):
            return index
    return None


def _find_header_index(rows: list[list[dict]], start: int) -> int | None:
    for index in range(start, len(rows)):
        row_text = " ".join(item["text"] for item in rows[index])
        normalized = _normalize_text(row_text)
        matches = [key for key in HEADER_KEYWORDS if key in normalized]
        if len(matches) >= 3 and "medidor" in normalized:
            return index
    return None


def _infer_column_positions(header_items: list[dict]) -> dict[str, float]:
    positions: dict[str, float] = {}
    ordered_mapping = [
        ("meter_number", ["medidor"]),
        ("segment_time", ["horario", "segmento"]),
        ("reading_date_1", ["data"]),
        ("reading_1", ["leitura"]),
        ("reading_date_2", ["data"]),
        ("reading_2", ["leitura"]),
        ("multiplier_factor", ["fator", "multiplicador"]),
        ("consumption_kwh", ["consumo", "kwh"]),
        ("number_of_days", ["dias"]),
    ]
    used = set()
    for column, keywords in ordered_mapping:
        for item in header_items:
            if item["index"] in used:
                continue
            text = _normalize_text(item["text"])
            if any(keyword in text for keyword in keywords):
                positions[column] = item.get("x_center", item["x"])
                used.add(item["index"])
                break
    return positions


def _assign_row_items(
    items: list[dict],
    column_positions: dict[str, float],
) -> dict[str, str]:
    row = {column: "" for column in COLUMN_ORDER}
    if not column_positions:
        return row
    sorted_positions = sorted(column_positions.items(), key=lambda item: item[1])
    boundaries = []
    for index in range(len(sorted_positions) - 1):
        boundaries.append(
            (sorted_positions[index][1] + sorted_positions[index + 1][1]) / 2
        )
    for item in items:
        x_value = item["x_center"]
        column_index = 0
        for boundary in boundaries:
            if x_value < boundary:
                break
            column_index += 1
        column_name = sorted_positions[
            min(column_index, len(sorted_positions) - 1)
        ][0]
        if row[column_name]:
            row[column_name] = f"{row[column_name]} {item['text']}".strip()
        else:
            row[column_name] = item["text"]
    return row


def map(texts: list, boxes: list) -> list[MeterItem]:
    items = _build_items(texts, boxes)
    rows = _group_items_by_row(items)
    section_start = _find_section_start(rows)
    if section_start is None:
        return []
    header_index = _find_header_index(rows, section_start + 1)
    if header_index is None:
        return []
    header_items = list(rows[header_index])
    column_positions = _infer_column_positions(header_items)
    if "meter_number" not in column_positions:
        return []
    result_rows = []
    for row in rows[header_index + 1 :]:
        row_data = _assign_row_items(row, column_positions)
        if not row_data["meter_number"] and not row_data["segment_time"]:
            continue
        result_rows.append(row_data)
    if not result_rows:
        return []
    return [
        MeterItem(
            meter_number=row.get("meter_number", "").upper(),
            segment_time=row.get("segment_time", "").upper(),
            reading_date_1=_format_date(row.get("reading_date_1", "")).upper(),
            reading_1=_parse_decimal(row.get("reading_1", "")),
            reading_date_2=_format_date(row.get("reading_date_2", "")).upper(),
            reading_2=_parse_decimal(row.get("reading_2", "")),
            multiplier_factor=_parse_decimal(row.get("multiplier_factor", "")),
            consumption_kwh=_parse_decimal(row.get("consumption_kwh", "")),
            number_of_days=_parse_int(row.get("number_of_days", "")),
        )
        for row in result_rows
    ]
