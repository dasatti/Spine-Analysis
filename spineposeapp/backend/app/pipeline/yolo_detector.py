import logging
import os

from app.pipeline.base import DetectorBase
from app.pipeline.keypoint_normalizer import REQUIRED_LANDMARKS

logger = logging.getLogger(__name__)


class YOLODetector(DetectorBase):
    """YOLO pose detector with optional stub mode when weights are unavailable."""

    def __init__(self, variant: str, weights_path: str | None) -> None:
        self._variant = variant
        self._model = None
        if weights_path and os.path.exists(weights_path):
            self._model = self._load_yolo(weights_path)
            self._stub_mode = False
            logger.info("YOLO detector (%s) loaded from %s", variant, weights_path)
        else:
            self._stub_mode = True
            logger.warning(
                "YOLO detector (%s) running in STUB MODE — set MODEL_WEIGHTS_PATH.",
                variant,
            )

    @staticmethod
    def _load_yolo(weights_path: str) -> object:
        """Load YOLO weights. Real inference is a future enhancement."""
        logger.info("YOLO weight file present at %s; using placeholder loader", weights_path)
        return {"weights_path": weights_path}

    @property
    def model_name(self) -> str:
        return self._variant

    def detect(self, frame_paths: dict[str, str]) -> dict:
        if self._stub_mode:
            return self._stub_output(frame_paths)
        return self._run_inference(frame_paths)

    def _stub_output(self, frame_paths: dict[str, str]) -> dict:
        landmarks: list[dict[str, float | str]] = []
        for view in frame_paths:
            for name in REQUIRED_LANDMARKS:
                landmarks.append(
                    {
                        "name": name,
                        "x": 0.0,
                        "y": 0.0,
                        "confidence": 0.0,
                        "view": view,
                    }
                )
        return {"detector": self.model_name, "landmarks": landmarks}

    def _run_inference(self, frame_paths: dict[str, str]) -> dict:
        """Placeholder for real YOLO pose inference."""
        logger.warning("YOLO inference not implemented; returning stub output")
        return self._stub_output(frame_paths)
