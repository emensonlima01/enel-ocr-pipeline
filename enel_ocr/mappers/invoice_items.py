# -*- coding: ascii -*-
from __future__ import annotations

from ..models import InvoiceItem
from ._utils import build_items, group_items_by_row, normalize_text, parse_decimal

COLUMN_ORDER = [
    "description",
    "unit",
    "quantity",
    "unit_price_with_taxes",
    "amount",
    "pis_cofins",
    "icms_tax_base",
    "icms_rate",
    "icms_amount",
    "unit_rate",
]
HEADER_COLUMNS = [
    ("description", ["descricao", "itens", "fatura"]),
    ("unit", ["unid"]),
    ("quantity", ["quant"]),
    ("unit_price_with_taxes", ["preco"]),
    ("amount", ["valor"]),
    ("pis_cofins", ["pis", "cofins"]),
    ("icms_tax_base", ["base"]),
    ("icms_rate", ["aliquota"]),
    ("icms_amount", ["icms"]),
    ("unit_rate", ["tarifa"]),
]

HEADER_KEYWORDS = {
    "descricao",
    "itens",
    "fatura",
    "unid",
    "quant",
    "preco",
    "valor",
    "pis",
    "cofins",
    "base",
    "aliquota",
    "icms",
    "tarifa",
}


def _row_like_header(row: list[dict]) -> bool:
    row_text = " ".join(item["text"] for item in row)
    normalized = normalize_text(row_text)
    matches = [key for key in HEADER_KEYWORDS if key in normalized]
    has_description = any(
        key in normalized for key in ("descricao", "itens", "fatura")
    )
    return len(matches) >= 3 and has_description


def _row_extends_header(row: list[dict]) -> bool:
    row_text = " ".join(item["text"] for item in row)
    normalized = normalize_text(row_text)
    if any(char.isdigit() for char in normalized):
        return False
    return any(key in normalized for key in HEADER_KEYWORDS)


def _find_header_index(rows: list[list[dict]]) -> int | None:
    for index, row in enumerate(rows):
        if _row_like_header(row):
            return index
    return None


def _infer_column_positions(header_items: list[dict]) -> dict[str, float]:
    positions: dict[str, float] = {}
    used = set()
    for column, keywords in HEADER_COLUMNS:
        for item in header_items:
            if item["index"] in used:
                continue
            text = normalize_text(item["text"])
            if any(keyword in text for keyword in keywords):
                if column == "description":
                    matched = [
                        candidate
                        for candidate in header_items
                        if any(
                            keyword in normalize_text(candidate["text"])
                            for keyword in keywords
                        )
                    ]
                    positions[column] = max(
                        candidate.get("x_center", candidate["x"])
                        for candidate in matched
                    )
                else:
                    positions[column] = item.get("x_center", item["x"])
                used.add(item["index"])
                break
    if "amount" not in positions:
        unit_price = positions.get("unit_price_with_taxes")
        pis = positions.get("pis_cofins")
        if unit_price is not None and pis is not None:
            positions["amount"] = (unit_price + pis) / 2
    return positions


def _assign_line_items(
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


def _is_numeric_text(value: str) -> bool:
    if not value:
        return False
    allowed = set("0123456789.,-%")
    return all(char in allowed for char in value.strip())


def _is_numeric_row(items: list[dict]) -> bool:
    if not items:
        return False
    return all(_is_numeric_text(item["text"]) for item in items)


def _description_limit(column_positions: dict[str, float]) -> float | None:
    sorted_positions = sorted(column_positions.items(), key=lambda item: item[1])
    for index, (column_name, position) in enumerate(sorted_positions):
        if column_name == "description" and index + 1 < len(sorted_positions):
            next_position = sorted_positions[index + 1][1]
            return position + ((next_position - position) * 0.75)
    return None


def _is_description_code_row(items: list[dict], limit: float | None) -> bool:
    if limit is None or not items:
        return False
    if not all(item["x"] < limit for item in items):
        return False
    combined = "".join(item["text"].strip() for item in items)
    if not combined:
        return False
    return combined.isdigit() and len(combined) <= 6


def map(texts: list, boxes: list) -> list[InvoiceItem]:
    items = build_items(texts, boxes)
    rows = group_items_by_row(items)
    header_index = _find_header_index(rows)
    if header_index is None:
        return []
    header_items = list(rows[header_index])
    for row in rows[header_index + 1 : header_index + 3]:
        if _row_extends_header(row):
            header_items.extend(row)
        else:
            break
    column_positions = _infer_column_positions(header_items)
    if "description" not in column_positions:
        return []
    description_limit = _description_limit(column_positions)
    result_rows = []
    pending_numeric_items = None
    for row in rows[header_index + 1 :]:
        if _is_description_code_row(row, description_limit) and result_rows:
            result_rows[-1]["description"] = (
                f"{result_rows[-1]['description']} {' '.join(item['text'] for item in row)}"
            ).strip()
            continue
        if _is_numeric_row(row):
            pending_numeric_items = row
            continue
        row_data = _assign_line_items(row, column_positions)
        if row_data.get("unit"):
            allowed_units = {"kwh", "kw", "mwh", "m3", "wh", "unid"}
            unit_tokens = row_data["unit"].split()
            kept_units = []
            moved_tokens = []
            for token in unit_tokens:
                normalized_token = normalize_text(token)
                if normalized_token in allowed_units:
                    kept_units.append(token)
                else:
                    moved_tokens.append(token)
            if moved_tokens:
                suffix = " ".join(moved_tokens)
                row_data["description"] = (
                    f"{row_data.get('description', '')} {suffix}"
                ).strip()
            row_data["unit"] = " ".join(kept_units)

        normalized_description = normalize_text(row_data["description"])
        if not normalized_description:
            if result_rows:
                result_rows[-1]["description"] = (
                    f"{result_rows[-1]['description']} {' '.join(item['text'] for item in row)}"
                ).strip()
            continue
        if normalized_description == "total" and pending_numeric_items:
            numeric_row = _assign_line_items(pending_numeric_items, column_positions)
            for column, value in numeric_row.items():
                if not row_data.get(column):
                    row_data[column] = value
            pending_numeric_items = None
        result_rows.append(row_data)
        if normalized_description == "total":
            break
    if not result_rows:
        return []
    return [
        InvoiceItem(
            description=row.get("description", "").upper(),
            unit=row.get("unit", "").upper(),
            quantity=parse_decimal(row.get("quantity", "")),
            unit_price_with_taxes=parse_decimal(
                row.get("unit_price_with_taxes", "")
            ),
            amount=parse_decimal(row.get("amount", "")),
            pis_cofins=parse_decimal(row.get("pis_cofins", "")),
            icms_tax_base=parse_decimal(row.get("icms_tax_base", "")),
            icms_rate=parse_decimal(row.get("icms_rate", "")),
            icms_amount=parse_decimal(row.get("icms_amount", "")),
            unit_rate=parse_decimal(row.get("unit_rate", "")),
        )
        for row in result_rows
    ]
