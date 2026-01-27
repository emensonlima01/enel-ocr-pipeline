# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import List, Tuple

import numpy as np
from paddleocr import PaddleOCR


def init_ocr() -> PaddleOCR:
    return PaddleOCR(
        use_angle_cls=False,
        lang="pt",
        ocr_version="PP-OCRv3"
    )


def run_ocr(
    ocr: PaddleOCR, image_np: np.ndarray
) -> Tuple[List[str], List[List[List[float]]], List[float]]:
    result = ocr.ocr(image_np, cls=False)
    if not result or not result[0]:
        return [], [], []
    lines = result[0]
    if not lines:
        return [], [], []
    boxes = [box for box, (_text, _score) in lines]
    texts = [text for _box, (text, _score) in lines]
    scores = [float(score) for _box, (_text, score) in lines]

    return texts, boxes, scores
