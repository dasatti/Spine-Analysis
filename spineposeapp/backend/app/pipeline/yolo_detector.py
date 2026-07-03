import os

import structlog

from app.pipeline.base import DetectorBase
from app.pipeline import yolo_inference

logger = structlog.get_logger(__name__)


class YOLODetector(DetectorBase):
    """YOLOv8 pose detector backed by Ultralytics."""

    def __init__(self, variant: str, weights_path: str | None) -> None:
        self._variant = variant
        self._weights_path = weights_path
        self._stub_mode = False
        if variant == "yolo_custom" and not (weights_path and os.path.exists(weights_path)):
            raise FileNotFoundError(
                "yolo_custom requires MODEL_WEIGHTS_PATH pointing to an existing .pt file"
            )
        logger.info("YOLO detector initialised", variant=variant, weights_path=weights_path)

    @property
    def model_name(self) -> str:
        return self._variant

    def detect(self, frame_paths: dict[str, str]) -> dict:
        return yolo_inference.detect_all_frames(
            frame_paths,
            weights_path=self._weights_path,
            detector_name=self.model_name,
            variant=self._variant,
        )
