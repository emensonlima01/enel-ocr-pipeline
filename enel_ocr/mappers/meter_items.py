# -*- coding: ascii -*-
from __future__ import annotations

from ..models import MeterItem
from ._utils import (
    build_items,
    format_date,
    group_items_by_row,
    normalize_text,
    parse_decimal,
    parse_int,
)

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


def _find_section_start(rows: list[list[dict]]) -> int | None:
    for index, row in enumerate(rows):
        row_text = " ".join(item["text"] for item in row)
        normalized = normalize_text(row_text)
        if any(title in normalized for title in SECTION_TITLES):
            return index
    return None


def _find_header_index(rows: list[list[dict]], start: int) -> int | None:
    for index in range(start, len(rows)):
        row_text = " ".join(item["text"] for item in rows[index])
        normalized = normalize_text(row_text)
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
            text = normalize_text(item["text"])
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
    items = build_items(texts, boxes)
    rows = group_items_by_row(items)
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
            reading_date_1=format_date(row.get("reading_date_1", "")).upper(),
            reading_1=parse_decimal(row.get("reading_1", "")),
            reading_date_2=format_date(row.get("reading_date_2", "")).upper(),
            reading_2=parse_decimal(row.get("reading_2", "")),
            multiplier_factor=parse_decimal(row.get("multiplier_factor", "")),
            consumption_kwh=parse_decimal(row.get("consumption_kwh", "")),
            number_of_days=parse_int(row.get("number_of_days", "")),
        )
        for row in result_rows
    ]
