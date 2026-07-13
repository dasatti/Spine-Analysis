"""YOLO classification model for side-view kyphosis detection."""

from __future__ import annotations

from pathlib import Path

from app.config import settings
from app.pipeline.side_view_classifier import (
    ClassificationPrediction,
    is_backend_ready as _is_backend_ready,
    predict_classification,
    resolve_weights_path as _resolve_weights_path,
)

DEFAULT_WEIGHTS = (
    Path(__file__).resolve().parents[2] / "models" / "yolo26n-cls-kyphosis.pt"
)
KYPHOSIS_LABEL = "kyphosis"

KyphosisPrediction = ClassificationPrediction


def resolve_weights_path(weights_path: str | None = None) -> Path:
    return _resolve_weights_path(
        DEFAULT_WEIGHTS,
        weights_path or settings.kyphosis_classifier_weights_path,
    )


def predict_kyphosis(
    image_path: str,
    weights_path: str | None = None,
    *,
    imgsz: int = 640,
) -> ClassificationPrediction:
    """Run side-view image through the kyphosis classification model."""
    return predict_classification(
        image_path,
        default_weights=DEFAULT_WEIGHTS,
        configured_path=weights_path or settings.kyphosis_classifier_weights_path,
        model_label="Kyphosis classification",
        imgsz=imgsz,
    )


def is_backend_ready(weights_path: str | None = None) -> bool:
    return _is_backend_ready(
        DEFAULT_WEIGHTS,
        weights_path or settings.kyphosis_classifier_weights_path,
    )


__all__ = [
    "DEFAULT_WEIGHTS",
    "KYPHOSIS_LABEL",
    "KyphosisPrediction",
    "predict_kyphosis",
    "resolve_weights_path",
    "is_backend_ready",
]
