"""Shared image loading helpers for the pose pipeline."""

from __future__ import annotations

import cv2
import numpy as np
import structlog

logger = structlog.get_logger(__name__)


def read_image_bgr(image_path: str) -> np.ndarray | None:
    image = cv2.imread(image_path, cv2.IMREAD_COLOR)
    if image is not None:
        return image
    try:
        from PIL import Image

        with Image.open(image_path) as pil_image:
            rgb = np.array(pil_image.convert("RGB"))
        return cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
    except Exception as exc:
        logger.warning("Failed to read image", path=image_path, error=str(exc))
        return None
