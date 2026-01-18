# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Final

import fitz  # PyMuPDF

DEFAULT_DPI: Final[int] = 300


def pdf_page_to_image_bytes(pdf_bytes: bytes, page_number: int, dpi: int = DEFAULT_DPI) -> bytes:
    if page_number < 1:
        raise ValueError("page_number deve ser 1 ou maior")

    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    try:
        if page_number > doc.page_count:
            raise ValueError("page_number maior que o total de paginas")

        page = doc.load_page(page_number - 1)
        zoom = dpi / 72.0
        matrix = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=matrix, alpha=False)
        return pix.tobytes("png")
    finally:
        doc.close()
