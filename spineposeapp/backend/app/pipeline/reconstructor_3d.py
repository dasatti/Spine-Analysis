import math

import numpy as np

from app.pipeline.base import Keypoint
from app.pipeline.metric_engine import CalibrationData


class Reconstructor3D:
    """Populate 3D coordinates on keypoints using calibration and optional depth."""

    @staticmethod
    def reconstruct(
        keypoints: list[Keypoint],
        depth_map: np.ndarray | None,
        calibration: CalibrationData,
    ) -> list[Keypoint]:
        """Return keypoints with x3d/y3d/z3d filled in millimetres."""
        pixels_per_mm = calibration.pixels_per_mm or Reconstructor3D._estimate_scale(keypoints, calibration)
        reconstructed: list[Keypoint] = []
        for kp in keypoints:
            z_mm = Reconstructor3D._depth_at(kp, depth_map, pixels_per_mm)
            reconstructed.append(
                Keypoint(
                    name=kp.name,
                    x=kp.x,
                    y=kp.y,
                    confidence=kp.confidence,
                    source_view=kp.source_view,
                    x3d=kp.x * pixels_per_mm,
                    y3d=kp.y * pixels_per_mm,
                    z3d=z_mm,
                )
            )
        calibration.pixels_per_mm = pixels_per_mm
        return reconstructed

    @staticmethod
    def _estimate_scale(keypoints: list[Keypoint], calibration: CalibrationData) -> float:
        ys = [kp.y for kp in keypoints if kp.confidence > 0.3 and kp.y > 0]
        if len(ys) >= 2:
            span_px = max(ys) - min(ys)
            if span_px > 1:
                return span_px / max(calibration.patient_height_cm * 10.0, 1.0)
        ankles = [kp for kp in keypoints if kp.name in ("left_ankle", "right_ankle") and kp.confidence > 0.3]
        shoulders = [
            kp for kp in keypoints if kp.name in ("left_shoulder", "right_shoulder") and kp.confidence > 0.3
        ]
        if ankles and shoulders:
            top = min(kp.y for kp in shoulders)
            bottom = max(kp.y for kp in ankles)
            span_px = bottom - top
            if span_px > 1:
                return span_px / max(calibration.patient_height_cm * 10.0, 1.0)
        if calibration.camera_distance_cm and calibration.patient_height_cm:
            return calibration.patient_height_cm / max(calibration.camera_distance_cm, 1.0)
        return 0.5

    @staticmethod
    def _depth_at(kp: Keypoint, depth_map: np.ndarray | None, pixels_per_mm: float) -> float:
        if depth_map is not None:
            y_idx = int(np.clip(kp.y, 0, depth_map.shape[0] - 1))
            x_idx = int(np.clip(kp.x, 0, depth_map.shape[1] - 1))
            depth_val = float(depth_map[y_idx, x_idx])
            if depth_val > 0:
                return depth_val
        return kp.y * pixels_per_mm * 0.1
