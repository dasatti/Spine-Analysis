from app.pipeline.pelvis_metrics import (
    estimate_pelvic_obliquity_mm,
    estimate_pelvic_tilt_sagittal_deg,
)


def _lm(name, x, y, view="front", confidence=0.9):
    return {"name": name, "x": x, "y": y, "confidence": confidence, "view": view}


def test_obliquity_from_front_view_only():
    frames = [
        _lm("left_hip", 200, 400, view="front"),
        _lm("right_hip", 280, 420, view="front"),
        _lm("left_hip", 210, 410, view="side"),
        _lm("right_hip", 215, 405, view="side"),
    ]
    # 20 px difference, scale 0.5 -> 10 mm
    assert estimate_pelvic_obliquity_mm(frames, 0.5) == 10.0


def test_obliquity_ignores_side_view():
    frames = [
        _lm("left_hip", 200, 400, view="side"),
        _lm("right_hip", 280, 420, view="side"),
    ]
    assert estimate_pelvic_obliquity_mm(frames, 0.5) is None


def test_tilt_from_vertical_thigh_in_side_view():
    frames = [
        _lm("left_hip", 100, 400, view="side"),
        _lm("left_knee", 130, 600, view="side"),
    ]
    tilt = estimate_pelvic_tilt_sagittal_deg(frames)
    assert tilt is not None
    assert 8.0 < tilt < 10.0


def test_tilt_unavailable_without_side_view():
    frames = [
        _lm("left_hip", 100, 400, view="front"),
        _lm("left_knee", 130, 600, view="front"),
    ]
    assert estimate_pelvic_tilt_sagittal_deg(frames) is None
