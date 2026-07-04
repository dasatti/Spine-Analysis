from app.pipeline.landmark_mapping import SPINE_CHAIN
from app.pipeline.landmark_refresh import (
    refresh_frame_landmarks,
    refresh_synthetic_landmarks_for_view,
)


def _kp(name: str, x: float, y: float, view: str = "front", confidence: float = 0.95) -> dict:
    return {"name": name, "x": x, "y": y, "confidence": confidence, "view": view}


def _front_body_landmarks():
    return [
        _kp("left_shoulder", 200, 140),
        _kp("right_shoulder", 280, 140),
        _kp("left_hip", 210, 220),
        _kp("right_hip", 270, 220),
        _kp("left_knee", 205, 300),
        _kp("right_knee", 275, 300),
        _kp("left_ankle", 200, 380),
        _kp("right_ankle", 280, 380),
        _kp("left_ear", 220, 75),
        _kp("right_ear", 260, 75),
        _kp("jaw_midpoint", 240, 80),
    ]


def test_refresh_rebuilds_spine_chain_from_body_joints():
    landmarks = _front_body_landmarks()
    refreshed = refresh_synthetic_landmarks_for_view("front", landmarks)
    names = {item["name"] for item in refreshed}
    assert "c7_proxy" in names
    assert "spine_l3" in names
    assert all(name in names for name in SPINE_CHAIN)


def test_refresh_updates_spine_when_shoulder_moves():
    base = _front_body_landmarks()
    shifted = _front_body_landmarks()
    for item in shifted:
        if item["name"] == "left_shoulder":
            item["x"] = 190

    base_refreshed = refresh_synthetic_landmarks_for_view("front", base)
    shifted_refreshed = refresh_synthetic_landmarks_for_view("front", shifted)

    def spine_x(items):
        return next(kp["x"] for kp in items if kp["name"] == "spine_t4")

    assert spine_x(base_refreshed) != spine_x(shifted_refreshed)


def test_preserve_manual_spine_keeps_edited_vertebra():
    landmarks = _front_body_landmarks()
    landmarks.append(_kp("spine_t4", 999, 200))
    refreshed = refresh_synthetic_landmarks_for_view(
        "front",
        landmarks,
        preserve_manual_spine=True,
    )
    t4 = next(kp for kp in refreshed if kp["name"] == "spine_t4")
    assert t4["x"] == 999


def test_refresh_frame_landmarks_only_target_views():
    front = _front_body_landmarks()
    side = [
        _kp("left_shoulder", 300, 150, view="side"),
        _kp("right_shoulder", 305, 152, view="side"),
        _kp("left_hip", 295, 300, view="side"),
        _kp("right_hip", 292, 302, view="side"),
    ]
    combined = front + side
    refreshed = refresh_frame_landmarks(combined, views=["front"])
    side_names = {kp["name"] for kp in refreshed if kp["view"] == "side"}
    assert "spine_l3" not in side_names
