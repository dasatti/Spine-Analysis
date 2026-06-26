import os

import structlog

from app.pipeline.base import DetectorBase
from app.pipeline.keypoint_normalizer import REQUIRED_LANDMARKS

logger = structlog.get_logger(__name__)


class SpinePoseDetector(DetectorBase):
    """SpinePose v2 detector with optional stub mode when weights are unavailable."""

    def __init__(self, weights_path: str | None) -> None:
        self._model = None
        if weights_path and os.path.exists(weights_path):
            self._model = self._load_model(weights_path)
            self._stub_mode = False
            logger.info("SpinePose v2 loaded", weights_path=weights_path)
        else:
            self._stub_mode = True
            logger.warning(
                "SpinePose v2 running in stub mode",
                reason="no weights loaded; set MODEL_WEIGHTS_PATH",
            )

    @staticmethod
    def _load_model(weights_path: str) -> object:
        """Load SpinePose v2 weights. Real inference is a future enhancement."""
        logger.info("SpinePose weight file present", weights_path=weights_path)
        return {"weights_path": weights_path}

    @property
    def model_name(self) -> str:
        return "spinepose_v2"

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
        """Placeholder for real SpinePose v2 inference."""
        logger.warning("SpinePose inference not implemented; returning stub output")
        return self._stub_output(frame_paths)
