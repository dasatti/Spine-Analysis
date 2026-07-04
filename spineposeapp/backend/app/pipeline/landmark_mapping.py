"""Shared landmark schema helpers for pose detectors."""

from __future__ import annotations

SPINE_CHAIN = [
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


def landmark_dict(name: str, x: float, y: float, confidence: float, view: str) -> dict:
    return {
        "name": name,
        "x": round(x, 2),
        "y": round(y, 2),
        "confidence": round(max(0.0, min(1.0, confidence)), 4),
        "view": view,
    }


def midpoint(
    a: tuple[float, float, float], b: tuple[float, float, float]
) -> tuple[float, float, float]:
    return (a[0] + b[0]) / 2.0, (a[1] + b[1]) / 2.0, min(a[2], b[2])


def interpolate_spine(
    neck: tuple[float, float, float], sacrum: tuple[float, float, float]
) -> dict[str, tuple[float, float, float]]:
    points: dict[str, tuple[float, float, float]] = {}
    for i, name in enumerate(SPINE_CHAIN):
        t = i / max(len(SPINE_CHAIN) - 1, 1)
        x = neck[0] * (1.0 - t) + sacrum[0] * t
        y = neck[1] * (1.0 - t) + sacrum[1] * t
        conf = min(neck[2], sacrum[2]) * (0.95 - abs(t - 0.5) * 0.1)
        points[name] = (x, y, max(conf, 0.0))
    return points


def world_landmark_dict(
    name: str, x: float, y: float, z: float, confidence: float, view: str
) -> dict:
    return {
        "name": name,
        "x3d": round(x, 1),
        "y3d": round(y, 1),
        "z3d": round(z, 1),
        "confidence": round(max(0.0, min(1.0, confidence)), 4),
        "source_view": view,
    }


def build_world_landmarks(
    view: str, points: dict[str, tuple[float, float, float, float] | None]
) -> list[dict]:
    """Map metric 3D body points (x, y, z in mm, confidence) into twin landmarks.

    Coordinates follow the MediaPipe world convention: origin at hip centre,
    x right, y down, z toward the camera.
    """
    landmarks: list[dict] = []
    for name, point in points.items():
        if name == "nose" or point is None or point[3] <= 0.3:
            continue
        landmarks.append(world_landmark_dict(name, point[0], point[1], point[2], point[3], view))

    ls = points.get("left_shoulder")
    rs = points.get("right_shoulder")
    lh = points.get("left_hip")
    rh = points.get("right_hip")
    if not (ls and rs and lh and rh):
        return landmarks

    shoulder_mid = tuple((a + b) / 2.0 for a, b in zip(ls[:3], rs[:3]))
    hip_mid = tuple((a + b) / 2.0 for a, b in zip(lh[:3], rh[:3]))
    trunk_conf = min(ls[3], rs[3], lh[3], rh[3])

    # Neck sits slightly above the shoulder line (y is down in world space).
    neck = (shoulder_mid[0], shoulder_mid[1] - 40.0, shoulder_mid[2])
    landmarks.append(
        world_landmark_dict("c7_proxy", neck[0], neck[1], neck[2], trunk_conf * 0.9, view)
    )

    for i, name in enumerate(SPINE_CHAIN):
        t = i / max(len(SPINE_CHAIN) - 1, 1)
        x = neck[0] * (1.0 - t) + hip_mid[0] * t
        y = neck[1] * (1.0 - t) + hip_mid[1] * t
        z = neck[2] * (1.0 - t) + hip_mid[2] * t
        conf = trunk_conf * (0.95 - abs(t - 0.5) * 0.1)
        if conf > 0.3:
            landmarks.append(world_landmark_dict(name, x, y, z, conf, view))

    nose = points.get("nose")
    if nose and nose[3] > 0.3:
        landmarks.append(
            world_landmark_dict("jaw_midpoint", nose[0], nose[1], nose[2], nose[3] * 0.95, view)
        )

    return landmarks


def build_unified_landmarks(
    view: str,
    *,
    nose: tuple[float, float, float] | None,
    left_ear: tuple[float, float, float] | None,
    right_ear: tuple[float, float, float] | None,
    left_shoulder: tuple[float, float, float] | None,
    right_shoulder: tuple[float, float, float] | None,
    left_hip: tuple[float, float, float] | None,
    right_hip: tuple[float, float, float] | None,
    left_knee: tuple[float, float, float] | None,
    right_knee: tuple[float, float, float] | None,
    left_ankle: tuple[float, float, float] | None,
    right_ankle: tuple[float, float, float] | None,
) -> list[dict]:
    """Map body keypoints into the unified SpinePose landmark list."""
    direct = {
        "left_ear": left_ear,
        "right_ear": right_ear,
        "left_shoulder": left_shoulder,
        "right_shoulder": right_shoulder,
        "left_hip": left_hip,
        "right_hip": right_hip,
        "left_knee": left_knee,
        "right_knee": right_knee,
        "left_ankle": left_ankle,
        "right_ankle": right_ankle,
    }

    landmarks: list[dict] = []
    for name, point in direct.items():
        if point and point[2] > 0.3:
            landmarks.append(landmark_dict(name, point[0], point[1], point[2], view))

    if not left_shoulder or not right_shoulder or not left_hip or not right_hip:
        if nose and nose[2] > 0.3:
            landmarks.append(landmark_dict("jaw_midpoint", nose[0], nose[1], nose[2] * 0.95, view))
        return landmarks

    shoulder_mid = midpoint(left_shoulder, right_shoulder)
    hip_mid = midpoint(left_hip, right_hip)
    neck = (
        shoulder_mid[0],
        shoulder_mid[1] - abs(left_shoulder[1] - right_shoulder[1]) * 0.15 - 8.0,
        min(left_shoulder[2], right_shoulder[2]) * 0.9,
    )

    c7_x, c7_y, c7_conf = neck
    landmarks.append(landmark_dict("c7_proxy", c7_x, c7_y, c7_conf, view))

    for spine_name, (sx, sy, sconf) in interpolate_spine(neck, hip_mid).items():
        if sconf > 0.3:
            landmarks.append(landmark_dict(spine_name, sx, sy, sconf, view))

    if nose and nose[2] > 0.3:
        landmarks.append(landmark_dict("jaw_midpoint", nose[0], nose[1], nose[2] * 0.95, view))
        landmarks.append(
            landmark_dict("facial_midline", nose[0], nose[1] - 10, nose[2] * 0.9, view)
        )

    return landmarks
