# -*- coding: ascii -*-
from __future__ import annotations

import io
from typing import Iterable, List, Tuple

import numpy as np
from PIL import Image


class ImageCropper:
    def __init__(self, image_bytes: bytes) -> None:
        self._image = Image.open(io.BytesIO(image_bytes))
        self._image.load()

    def crop(self, coord: Tuple[int, int, int, int]) -> bytes:
        x, y, width, height = coord
        box = (x, y, x + width, y + height)
        cropped = self._image.crop(box)
        out = io.BytesIO()
        cropped.save(out, format="PNG")
        return out.getvalue()

    def crop_ndarray(self, coord: Tuple[int, int, int, int]) -> np.ndarray:
        x, y, width, height = coord
        box = (x, y, x + width, y + height)
        cropped = self._image.crop(box).convert("RGB")
        return np.array(cropped)

    def crop_many_ndarray(
        self, coords: Iterable[Tuple[int, int, int, int]]
    ) -> List[np.ndarray]:
        return [self.crop_ndarray(coord) for coord in coords]


def crop_image_bytes(image_bytes: bytes, coord: Tuple[int, int, int, int]) -> bytes:
    """
    coord = (x, y, width, height)
    retorna bytes PNG do recorte.
    """
    return ImageCropper(image_bytes).crop(coord)
