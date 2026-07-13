"""YOLO classification model for side-view lordosis detection."""

from __future__ import annotations

from pathlib import Path

from app.config import settings
from app.pipeline.side_view_classifier import (
    ClassificationPrediction,
    is_backend_ready as _is_backend_ready,
    predict_classification,
)

DEFAULT_WEIGHTS = Path(__file__).resolve().parents[2] / "models" / "yolo26n-cls-lordosis.pt"
LORDOSIS_LABEL = "lordosis"

LordosisPrediction = ClassificationPrediction


def predict_lordosis(
    image_path: str,
    weights_path: str | None = None,
    *,
    imgsz: int = 640,
) -> ClassificationPrediction:
    """Run side-view image through the lordosis classification model."""
    return predict_classification(
        image_path,
        default_weights=DEFAULT_WEIGHTS,
        configured_path=weights_path or settings.lordosis_classifier_weights_path,
        model_label="Lordosis classification",
        imgsz=imgsz,
    )


def is_backend_ready(weights_path: str | None = None) -> bool:
    return _is_backend_ready(
        DEFAULT_WEIGHTS,
        weights_path or settings.lordosis_classifier_weights_path,
    )
