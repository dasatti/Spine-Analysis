"""Shared YOLO side-view image classification helpers."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import structlog

logger = structlog.get_logger(__name__)

NORMAL_LABEL = "normal"


@dataclass(frozen=True)
class ClassificationPrediction:
    class_name: str
    confidence: float


def resolve_weights_path(default_weights: Path, configured_path: str | None) -> Path:
    if configured_path:
        path = Path(configured_path)
        if path.exists():
            return path
    if default_weights.exists():
        return default_weights
    raise FileNotFoundError(
        f"Classifier weights not found. Expected at {default_weights} or configured path."
    )


@lru_cache(maxsize=8)
def _get_model(resolved_weights: str):
    from ultralytics import YOLO

    logger.info("Loading side-view classifier", weights=resolved_weights)
    return YOLO(resolved_weights)


def predict_classification(
    image_path: str,
    *,
    default_weights: Path,
    configured_path: str | None = None,
    model_label: str = "classifier",
    imgsz: int = 640,
) -> ClassificationPrediction:
    """Run a side-view image through a YOLO classification model."""
    resolved = str(resolve_weights_path(default_weights, configured_path))
    model = _get_model(resolved)
    results = model.predict(source=image_path, imgsz=imgsz, verbose=False)
    if not results:
        raise RuntimeError(f"{model_label} returned no results")

    result = results[0]
    if result.probs is None:
        raise RuntimeError(f"{model_label} result has no class probabilities")

    class_id = int(result.probs.top1)
    class_name = str(result.names[class_id]).strip().lower()
    confidence = float(result.probs.top1conf)

    logger.info(
        f"{model_label} complete",
        class_name=class_name,
        confidence=round(confidence, 4),
        image_path=image_path,
    )
    return ClassificationPrediction(class_name=class_name, confidence=confidence)


def is_backend_ready(default_weights: Path, configured_path: str | None = None) -> bool:
    try:
        resolve_weights_path(default_weights, configured_path)
        return True
    except Exception:
        return False
