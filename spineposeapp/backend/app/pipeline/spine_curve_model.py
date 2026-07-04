from dataclasses import dataclass

from app.pipeline.base import Keypoint
from app.pipeline.sagittal_curve import estimate_sagittal_angles


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
    def fit(
        cls,
        keypoints: list[Keypoint],
        frame_landmarks: list[dict] | None = None,
    ) -> SpineCurve:
        """Build a spine curve, estimating curvature from the side-view frame.

        The interpolated 3D spine landmarks form a straight line and carry no
        curvature, so thoracic/lumbar angles come from the sagittal (side view)
        proxy. When no side view is available both angles are ``None`` and the
        downstream metric is reported as unavailable.
        """
        lookup = {kp.name: kp for kp in keypoints}
        points: list[tuple[float, float, float]] = []
        for name in cls.SPINE_NAMES:
            kp = lookup.get(name)
            if kp and kp.x3d is not None and kp.y3d is not None and kp.z3d is not None:
                points.append((kp.x3d, kp.y3d, kp.z3d))

        thoracic, lumbar = estimate_sagittal_angles(frame_landmarks or [])
        return SpineCurve(
            points=points,
            thoracic_angle_deg=thoracic,
            lumbar_angle_deg=lumbar,
        )
