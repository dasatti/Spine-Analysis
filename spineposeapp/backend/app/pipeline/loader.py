import os

import structlog

from app.config import settings
from app.pipeline.base import DetectorBase

logger = structlog.get_logger(__name__)


def get_detector() -> DetectorBase:
    """Return the detector configured by settings.detector_model."""
    model = settings.detector_model
    if model == "spinepose_v2":
        from app.pipeline.spinepose_detector import SpinePoseDetector

        return SpinePoseDetector(weights_path=settings.model_weights_path)
    if model in ("yolo_v8", "yolo_custom"):
        from app.pipeline.yolo_detector import YOLODetector

        return YOLODetector(variant=model, weights_path=settings.model_weights_path)
    raise ValueError(
        f"Unknown DETECTOR_MODEL='{model}'. "
        "Supported values: spinepose_v2, yolo_v8, yolo_custom"
    )


def validate_detector_config() -> None:
    """Fail fast when weights path is configured but missing on disk."""
    if settings.model_weights_path and not os.path.exists(settings.model_weights_path):
        raise FileNotFoundError(
            f"MODEL_WEIGHTS_PATH='{settings.model_weights_path}' does not exist"
        )
    detector = get_detector()
    logger.info(
        "Detector validated",
        model_name=detector.model_name,
        stub_mode=getattr(detector, "_stub_mode", False),
    )
