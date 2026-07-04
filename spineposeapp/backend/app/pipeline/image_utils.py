"""Shared image loading helpers for the pose pipeline."""

from __future__ import annotations

import cv2
import numpy as np
import structlog

logger = structlog.get_logger(__name__)


def read_image_bgr(image_path: str) -> np.ndarray | None:
    """Read an image as BGR, applying EXIF orientation.

    Browsers honour the EXIF orientation flag when displaying photos, while
    cv2.imread ignores it. Detection must run on the same pixel orientation
    the user sees, so PIL + exif_transpose is the primary path.
    """
    try:
        from PIL import Image, ImageOps

        with Image.open(image_path) as pil_image:
            upright = ImageOps.exif_transpose(pil_image)
            rgb = np.array(upright.convert("RGB"))
        return cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
    except Exception as exc:
        logger.warning("PIL read failed, falling back to cv2", path=image_path, error=str(exc))

    image = cv2.imread(image_path, cv2.IMREAD_COLOR)
    if image is None:
        logger.warning("Failed to read image", path=image_path)
    return image
