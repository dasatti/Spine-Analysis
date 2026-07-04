from app.pipeline.head_shoulder_metrics import (
    estimate_forward_head_posture_mm,
    estimate_jaw_deviation_mm,
    estimate_shoulder_asymmetry_mm,
)


def _lm(name, x, y, view="front", confidence=0.9):
    return {"name": name, "x": x, "y": y, "confidence": confidence, "view": view}


def test_shoulder_asymmetry_front_view():
    frames = [
        _lm("left_shoulder", 200, 400, view="front"),
        _lm("right_shoulder", 280, 420, view="front"),
    ]
    assert estimate_shoulder_asymmetry_mm(frames, 0.5) == 10.0


def test_forward_head_side_view():
    frames = [
        _lm("left_ear", 160, 100, view="side"),
        _lm("left_shoulder", 110, 200, view="side"),
    ]
    assert estimate_forward_head_posture_mm(frames, 0.5) == 25.0


def test_jaw_deviation_from_eye_midline():
    frames = [
        _lm("left_eye", 220, 100, view="front"),
        _lm("right_eye", 280, 100, view="front"),
        _lm("jaw_midpoint", 260, 140, view="front"),
    ]
    # midline 250, jaw 260 -> 10 px * 0.5 = 5 mm
    assert estimate_jaw_deviation_mm(frames, 0.5) == 5.0


def test_jaw_deviation_unavailable_without_midline():
    frames = [_lm("jaw_midpoint", 260, 140, view="front")]
    assert estimate_jaw_deviation_mm(frames, 0.5) is None
