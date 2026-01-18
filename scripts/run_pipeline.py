# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path

from enel_ocr.ocr.engine import init_ocr
from enel_ocr.pipeline import run_pipeline

PDF_PATH = Path(r"E:\]131313-141411.pdf")


def main() -> None:
    pdf_bytes = PDF_PATH.read_bytes()
    ocr = init_ocr()
    run_pipeline(pdf_bytes, ocr)


if __name__ == "__main__":
    main()
