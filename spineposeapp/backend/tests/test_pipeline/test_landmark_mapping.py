from app.pipeline.landmark_mapping import (
    SPINE_CHAIN,
    build_unified_landmarks,
    interpolate_spine,
    interpolate_spine_sagittal,
    twin_landmarks_from_frame,
)


def _spine_lookup(landmarks: list[dict]) -> dict[str, dict]:
    return {item["name"]: item for item in landmarks if item["name"] in SPINE_CHAIN}


def test_front_view_spine_is_collinear():
    neck = (240.0, 120.0, 0.9)
    sacrum = (240.0, 420.0, 0.9)
    points = interpolate_spine(neck, sacrum)
    xs = [points[name][0] for name in SPINE_CHAIN]
    assert max(xs) - min(xs) < 0.01


def test_side_view_spine_has_sagittal_curve():
    """Curved side-view spine deviates from a straight neck-to-sacrum line."""
    neck = (300.0, 140.0, 0.9)
    sacrum = (290.0, 420.0, 0.9)
    ear = (330.0, 100.0, 0.85)
    shoulder = (305.0, 155.0, 0.95)
    hip = (292.0, 420.0, 0.9)
    knee = (288.0, 520.0, 0.88)

    points = interpolate_spine_sagittal(
        neck,
        sacrum,
        ear=ear,
        shoulder=shoulder,
        hip=hip,
        knee=knee,
    )

    straight_x = lambda t: neck[0] * (1.0 - t) + sacrum[0] * t
    deviations = []
    for i, name in enumerate(SPINE_CHAIN):
        t = i / (len(SPINE_CHAIN) - 1)
        deviations.append(abs(points[name][0] - straight_x(t)))

    assert max(deviations) > 5.0
    # Kyphosis peak should sit in the thoracic region.
    thoracic_dev = abs(points["spine_t4"][0] - straight_x(3 / 8))
    lumbar_dev = abs(points["spine_l3"][0] - straight_x(6 / 8))
    assert thoracic_dev > 2.0
    assert lumbar_dev > 2.0


def test_side_view_uses_visible_side_joints():
    """Side view should anchor on the visible shoulder/hip, not left/right midpoints."""
    landmarks = build_unified_landmarks(
        "side",
        nose=(340.0, 90.0, 0.9),
        left_ear=(335.0, 95.0, 0.4),
        right_ear=(345.0, 95.0, 0.92),
        left_shoulder=(310.0, 150.0, 0.35),
        right_shoulder=(305.0, 152.0, 0.95),
        left_hip=(295.0, 300.0, 0.3),
        right_hip=(292.0, 302.0, 0.93),
        left_knee=(290.0, 400.0, 0.3),
        right_knee=(288.0, 402.0, 0.9),
        left_ankle=(285.0, 500.0, 0.85),
        right_ankle=(283.0, 502.0, 0.88),
    )
    spine = _spine_lookup(landmarks)
    assert "spine_t4" in spine
    assert "spine_l3" in spine
    # Visible right shoulder x=305; spine should not sit at left/right midpoint (~307.5).
    assert abs(spine["spine_t4"]["x"] - 307.5) > 3.0


def test_twin_landmarks_include_all_capture_views():
    frame_landmarks = [
        {"name": "left_hip", "x": 210, "y": 220, "confidence": 0.9, "view": "front"},
        {"name": "left_hip", "x": 292, "y": 420, "confidence": 0.9, "view": "side"},
        {"name": "left_hip", "x": 400, "y": 225, "confidence": 0.9, "view": "back"},
        {"name": "left_hip", "x": 100, "y": 100, "confidence": 0.9, "view": "adams"},
    ]
    twin = twin_landmarks_from_frame(frame_landmarks)
    views = {item["source_view"] for item in twin}
    assert views == {"front", "side", "back"}
    side = next(item for item in twin if item["source_view"] == "side")
    assert side["x3d"] == 0.0
    assert side["y3d"] == 420.0
    assert side["z3d"] == 292.0
