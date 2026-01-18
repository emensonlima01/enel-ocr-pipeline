# -*- coding: ascii -*-
from __future__ import annotations

from dataclasses import asdict
from decimal import Decimal
from flask import Flask, jsonify, request
from threading import Lock

from .ocr.engine import init_ocr
from .pipeline import run_pipeline

app = Flask(__name__)
OCR = init_ocr()
OCR_LOCK = Lock()


@app.post("/invoice")
def invoice():
    content_type = (request.content_type or "").lower()
    if "application/pdf" not in content_type:
        return jsonify({"error": "only application/pdf is accepted"}), 400
    pdf_bytes = request.get_data()
    if not pdf_bytes:
        return jsonify({"error": "empty body"}), 400
    if not pdf_bytes.startswith(b"%PDF"):
        return jsonify({"error": "invalid pdf"}), 400

    with OCR_LOCK:
        invoice_obj = run_pipeline(pdf_bytes, OCR)

    payload = asdict(invoice_obj)
    return jsonify(_serialize_decimals(payload))


def _serialize_decimals(value):
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, list):
        return [_serialize_decimals(item) for item in value]
    if isinstance(value, dict):
        return {key: _serialize_decimals(item) for key, item in value.items()}
    return value


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
