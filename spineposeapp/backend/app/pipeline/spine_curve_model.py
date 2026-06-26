import math
from dataclasses import dataclass

import numpy as np

from app.pipeline.base import Keypoint


@dataclass
class SpineCurve:
    """Fitted spine curve used by kyphosis and lordosis metrics."""

    points: list[tuple[float, float, float]]
    thoracic_angle_deg: float | None
    lumbar_angle_deg: float | None


class SpineCurveModel:
    """Fit a simplified spine curve from 3D keypoints."""

    SPINE_NAMES = [
        "spine_c7",
        "spine_t1",
        "spine_t4",
        "spine_t7",
        "spine_t10",
        "spine_l1",
        "spine_l3",
        "spine_l5",
        "spine_s1",
    ]

    @classmethod
    def fit(cls, keypoints: list[Keypoint]) -> SpineCurve:
        """Build a spine curve from available 3D spine landmarks."""
        lookup = {kp.name: kp for kp in keypoints}
        points: list[tuple[float, float, float]] = []
        for name in cls.SPINE_NAMES:
            kp = lookup.get(name)
            if kp and kp.x3d is not None and kp.y3d is not None and kp.z3d is not None:
                points.append((kp.x3d, kp.y3d, kp.z3d))

        thoracic = cls._segment_angle(points, 0, min(4, len(points) - 1))
        lumbar = cls._segment_angle(points, max(0, len(points) - 5), len(points) - 1)
        return SpineCurve(
            points=points,
            thoracic_angle_deg=thoracic,
            lumbar_angle_deg=lumbar,
        )

    @staticmethod
    def _segment_angle(
        points: list[tuple[float, float, float]], start: int, end: int
    ) -> float | None:
        if end <= start or end >= len(points):
            return None
        p1 = np.array(points[start])
        p2 = np.array(points[end])
        vertical = np.array([0.0, 1.0, 0.0])
        segment = p2 - p1
        norm = np.linalg.norm(segment)
        if norm < 1e-6:
            return None
        cos_angle = np.dot(segment / norm, vertical)
        cos_angle = float(np.clip(cos_angle, -1.0, 1.0))
        return abs(math.degrees(math.acos(cos_angle)))
