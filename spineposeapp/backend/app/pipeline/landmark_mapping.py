"""Shared landmark schema helpers for pose detectors."""

from __future__ import annotations

import math

SIDE_VIEW = "side"

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
    """Evenly spaced spine points on a straight line (front/back views)."""
    points: dict[str, tuple[float, float, float]] = {}
    for i, name in enumerate(SPINE_CHAIN):
        t = i / max(len(SPINE_CHAIN) - 1, 1)
        x = neck[0] * (1.0 - t) + sacrum[0] * t
        y = neck[1] * (1.0 - t) + sacrum[1] * t
        conf = min(neck[2], sacrum[2]) * (0.95 - abs(t - 0.5) * 0.1)
        points[name] = (x, y, max(conf, 0.0))
    return points


def _pick_visible_side(
    left: tuple[float, float, float] | None,
    right: tuple[float, float, float] | None,
    threshold: float = 0.3,
) -> tuple[float, float, float] | None:
    """Return the higher-confidence left/right joint (for profile views)."""
    candidates = [point for point in (left, right) if point and point[2] >= threshold]
    if not candidates:
        return None
    return max(candidates, key=lambda point: point[2])


def _angle_at(
    a: tuple[float, float], b: tuple[float, float], c: tuple[float, float]
) -> float | None:
    bax, bay = a[0] - b[0], a[1] - b[1]
    bcx, bcy = c[0] - b[0], c[1] - b[1]
    norm_ba = math.hypot(bax, bay)
    norm_bc = math.hypot(bcx, bcy)
    if norm_ba < 1e-6 or norm_bc < 1e-6:
        return None
    cos_angle = (bax * bcx + bay * bcy) / (norm_ba * norm_bc)
    cos_angle = max(-1.0, min(1.0, cos_angle))
    return math.degrees(math.acos(cos_angle))


def _sagittal_facing_sign(
    ear: tuple[float, float, float] | None,
    shoulder: tuple[float, float, float],
) -> float:
    """+1 when the subject faces toward +x (ear anterior to shoulder), else -1."""
    if ear is None or abs(ear[0] - shoulder[0]) < 1.0:
        return 1.0
    return 1.0 if ear[0] >= shoulder[0] else -1.0


def _trunk_flexion_deg(
    a: tuple[float, float, float] | None,
    b: tuple[float, float, float] | None,
    c: tuple[float, float, float] | None,
    resting_deg: float,
) -> float:
    if not (a and b and c):
        return resting_deg
    angle = _angle_at((a[0], a[1]), (b[0], b[1]), (c[0], c[1]))
    if angle is None:
        return resting_deg
    return max(resting_deg, 180.0 - angle)


def interpolate_spine_sagittal(
    neck: tuple[float, float, float],
    sacrum: tuple[float, float, float],
    *,
    ear: tuple[float, float, float] | None = None,
    shoulder: tuple[float, float, float] | None = None,
    hip: tuple[float, float, float] | None = None,
    knee: tuple[float, float, float] | None = None,
) -> dict[str, tuple[float, float, float]]:
    """Spine chain with thoracic kyphosis and lumbar lordosis for side-view overlays.

    Vertebrae are not detected by pose models; this bends the interpolated chain
    using visible ear/shoulder/hip/knee geometry so the overlay matches the
    natural sagittal S-curve rather than a straight neck-to-hip line.
    """
    trunk_height = max(abs(sacrum[1] - neck[1]), 1.0)
    base_conf = min(neck[2], sacrum[2])
    facing = _sagittal_facing_sign(ear, shoulder or neck)

    thoracic_flex = _trunk_flexion_deg(ear, shoulder, hip, resting_deg=12.0)
    lumbar_flex = _trunk_flexion_deg(shoulder, hip, knee, resting_deg=10.0)

    kyphosis_amp = trunk_height * 0.10 * min(thoracic_flex / 35.0, 1.8)
    lordosis_amp = trunk_height * 0.08 * min(lumbar_flex / 35.0, 1.8)
    posterior_base = facing * trunk_height * 0.04

    points: dict[str, tuple[float, float, float]] = {}
    chain_len = len(SPINE_CHAIN)
    for i, name in enumerate(SPINE_CHAIN):
        t = i / max(chain_len - 1, 1)
        bx = neck[0] * (1.0 - t) + sacrum[0] * t
        by = neck[1] * (1.0 - t) + sacrum[1] * t

        # Spine column sits slightly posterior to the shoulder/hip joints.
        bx -= posterior_base * (1.0 - 0.3 * t)

        # Thoracic kyphosis: mid-back bulges posterior (convex posteriorly).
        if t <= 0.55:
            bump = math.sin(math.pi * t / 0.55)
            bx -= facing * kyphosis_amp * bump

        # Lumbar lordosis: low back swings anterior relative to mid-thoracic.
        if t >= 0.45:
            bump = math.sin(math.pi * (t - 0.45) / 0.55)
            bx += facing * lordosis_amp * bump * 0.85

        conf = base_conf * (0.95 - abs(t - 0.5) * 0.1)
        points[name] = (bx, by, max(conf, 0.0))
    return points


def _side_view_spine_anchors(
    shoulder: tuple[float, float, float],
    hip: tuple[float, float, float],
    ear: tuple[float, float, float] | None,
) -> tuple[tuple[float, float, float], tuple[float, float, float]]:
    """Neck and sacrum proxies from the visible-side shoulder and hip."""
    facing = _sagittal_facing_sign(ear, shoulder)
    neck = (
        shoulder[0] - facing * 8.0,
        shoulder[1] - 12.0,
        shoulder[2] * 0.9,
    )
    sacrum = (
        hip[0] - facing * 5.0,
        hip[1],
        hip[2],
    )
    return neck, sacrum


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


def twin_landmarks_from_frame(frame_landmarks: list[dict]) -> list[dict]:
    """Build digital-twin landmarks from front, side, and back frame keypoints.

    Each view uses its own 2D capture coordinates mapped into a flat 3D plane
    aligned with that view's camera preset in the viewer:

    - front/back: image (x, y) -> (x3d, y3d, 0)
    - side: image (x, y) -> (0, y3d, z3d) so the side camera sees depth (z) vs height (y)
    """
    twin: list[dict] = []
    for kp in frame_landmarks:
        view = kp.get("view") or kp.get("source_view") or ""
        if view not in {"front", "side", "back", "upper_body"}:
            continue
        confidence = float(kp.get("confidence", 0.0))
        if confidence <= 0.3:
            continue
        x = float(kp["x"])
        y = float(kp["y"])
        if view == "side":
            x3d, y3d, z3d = 0.0, y, x
        else:
            x3d, y3d, z3d = x, y, 0.0
        twin.append(
            {
                "name": str(kp["name"]),
                "x3d": round(x3d, 1),
                "y3d": round(y3d, 1),
                "z3d": round(z3d, 1),
                "confidence": confidence,
                "source_view": view,
            }
        )
    return twin


def twin_landmarks_from_front_frame(frame_landmarks: list[dict]) -> list[dict]:
    """Backward-compatible alias; prefer ``twin_landmarks_from_frame``."""
    return twin_landmarks_from_frame(frame_landmarks)


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
    left_eye: tuple[float, float, float] | None = None,
    right_eye: tuple[float, float, float] | None = None,
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
        "left_eye": left_eye,
        "right_eye": right_eye,
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

    if view == SIDE_VIEW:
        shoulder = _pick_visible_side(left_shoulder, right_shoulder)
        hip = _pick_visible_side(left_hip, right_hip)
        if not shoulder or not hip:
            if nose and nose[2] > 0.3:
                landmarks.append(
                    landmark_dict("jaw_midpoint", nose[0], nose[1], nose[2] * 0.95, view)
                )
            return landmarks

        ear = _pick_visible_side(left_ear, right_ear)
        knee = _pick_visible_side(left_knee, right_knee)
        neck, sacrum = _side_view_spine_anchors(shoulder, hip, ear)
        spine_points = interpolate_spine_sagittal(
            neck,
            sacrum,
            ear=ear,
            shoulder=shoulder,
            hip=hip,
            knee=knee,
        )
    else:
        if not left_shoulder or not right_shoulder or not left_hip or not right_hip:
            if nose and nose[2] > 0.3:
                landmarks.append(
                    landmark_dict("jaw_midpoint", nose[0], nose[1], nose[2] * 0.95, view)
                )
            return landmarks

        shoulder_mid = midpoint(left_shoulder, right_shoulder)
        hip_mid = midpoint(left_hip, right_hip)
        neck = (
            shoulder_mid[0],
            shoulder_mid[1] - abs(left_shoulder[1] - right_shoulder[1]) * 0.15 - 8.0,
            min(left_shoulder[2], right_shoulder[2]) * 0.9,
        )
        spine_points = interpolate_spine(neck, hip_mid)

    c7_x, c7_y, c7_conf = neck
    landmarks.append(landmark_dict("c7_proxy", c7_x, c7_y, c7_conf, view))

    for spine_name, (sx, sy, sconf) in spine_points.items():
        if sconf > 0.3:
            landmarks.append(landmark_dict(spine_name, sx, sy, sconf, view))

    if nose and nose[2] > 0.3:
        landmarks.append(landmark_dict("jaw_midpoint", nose[0], nose[1], nose[2] * 0.95, view))
        landmarks.append(
            landmark_dict("facial_midline", nose[0], nose[1] - 10, nose[2] * 0.9, view)
        )

    return landmarks
