import os

import structlog

from app.config import settings
from app.pipeline.base import DetectorBase

logger = structlog.get_logger(__name__)

SUPPORTED_DETECTORS = ("spinepose_v2", "yolo_v8", "yolo_custom")
SELECTABLE_DETECTORS = ("spinepose_v2", "yolo_v8")

DETECTOR_LABELS = {
    "spinepose_v2": "SpinePose v2 (MediaPipe)",
    "yolo_v8": "YOLOv8 Pose",
    "yolo_custom": "YOLO Custom Weights",
}


def effective_detector_model(preferred: str | None = None) -> str:
    """Resolve the detector model for a scan from doctor preference or env default."""
    if preferred and preferred in SUPPORTED_DETECTORS:
        return preferred
    return settings.detector_model


def get_detector(model: str | None = None) -> DetectorBase:
    """Return a detector for the requested model (or global default)."""
    selected = model or settings.detector_model
    if selected == "spinepose_v2":
        from app.pipeline.spinepose_detector import SpinePoseDetector

        return SpinePoseDetector(weights_path=settings.model_weights_path)
    if selected in ("yolo_v8", "yolo_custom"):
        from app.pipeline.yolo_detector import YOLODetector

        return YOLODetector(variant=selected, weights_path=settings.model_weights_path)
    raise ValueError(
        f"Unknown detector model '{selected}'. "
        f"Supported values: {', '.join(SUPPORTED_DETECTORS)}"
    )


def validate_detector_config() -> None:
    """Fail fast when custom weights path is configured but missing on disk."""
    if settings.model_weights_path and not os.path.exists(settings.model_weights_path):
        if settings.detector_model not in ("yolo_v8", "spinepose_v2"):
            raise FileNotFoundError(
                f"MODEL_WEIGHTS_PATH='{settings.model_weights_path}' does not exist"
            )

    detector = get_detector(settings.detector_model)
    logger.info(
        "Default detector validated",
        model_name=detector.model_name,
        stub_mode=getattr(detector, "_stub_mode", False),
    )


def detector_backend_ready(model: str) -> bool:
    if model == "spinepose_v2":
        from app.pipeline import pose_inference

        return pose_inference.is_backend_ready()
    if model in ("yolo_v8", "yolo_custom"):
        from app.pipeline import yolo_inference

        return yolo_inference.is_backend_ready(
            variant=model, weights_path=settings.model_weights_path
        )
    return False
