import os

import structlog

from app.pipeline.base import DetectorBase
from app.pipeline.pose_inference import detect_all_frames

logger = structlog.get_logger(__name__)


class YOLODetector(DetectorBase):
    """YOLO pose detector backed by Ultralytics YOLOv8 pose estimation."""

    def __init__(self, variant: str, weights_path: str | None) -> None:
        self._variant = variant
        self._weights_path = weights_path
        self._stub_mode = False
        if weights_path and os.path.exists(weights_path):
            logger.info("YOLO detector loaded", variant=variant, weights_path=weights_path)
        else:
            logger.info("YOLO detector using default weights", variant=variant)

    @property
    def model_name(self) -> str:
        return self._variant

    def detect(self, frame_paths: dict[str, str]) -> dict:
        return detect_all_frames(
            frame_paths,
            weights_path=self._weights_path,
            detector_name=self.model_name,
        )
