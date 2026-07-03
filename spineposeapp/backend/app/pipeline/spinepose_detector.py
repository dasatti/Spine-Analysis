import os

import structlog

from app.pipeline.base import DetectorBase
from app.pipeline import pose_inference

logger = structlog.get_logger(__name__)


class SpinePoseDetector(DetectorBase):
    """SpinePose v2 detector using MediaPipe Pose Landmarker."""

    def __init__(self, weights_path: str | None) -> None:
        self._weights_path = weights_path
        self._stub_mode = False
        if weights_path and os.path.exists(weights_path):
            logger.info("SpinePose v2 custom weights configured", weights_path=weights_path)
        else:
            logger.info("SpinePose v2 using MediaPipe pose backend")

    @property
    def model_name(self) -> str:
        return "spinepose_v2"

    def detect(self, frame_paths: dict[str, str]) -> dict:
        return pose_inference.detect_all_frames(
            frame_paths,
            weights_path=self._weights_path,
            detector_name=self.model_name,
        )
