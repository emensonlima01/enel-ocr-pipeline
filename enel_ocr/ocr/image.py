# -*- coding: utf-8 -*-
from __future__ import annotations

import io

import numpy as np
from PIL import Image


def bytes_to_ndarray(image_bytes: bytes) -> np.ndarray:
    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    return np.array(image)
