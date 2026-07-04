from app.pipeline.leg_metrics import estimate_hka_angle_deg, estimate_knee_flexion_deg


def _lm(name, x, y, view="front", confidence=0.9):
    return {"name": name, "x": x, "y": y, "confidence": confidence, "view": view}


def test_straight_leg_front_view():
    frames = [
        _lm("left_hip", 200, 400, view="front"),
        _lm("left_knee", 200, 550, view="front"),
        _lm("left_ankle", 200, 700, view="front"),
    ]
    assert estimate_knee_flexion_deg(frames, "left") == 0.0


def test_bent_knee_front_view():
    frames = [
        _lm("left_hip", 200, 400, view="front"),
        _lm("left_knee", 250, 520, view="front"),
        _lm("left_ankle", 200, 700, view="front"),
    ]
    flexion = estimate_knee_flexion_deg(frames, "left")
    assert flexion is not None
    assert flexion > 10.0


def test_prefers_front_over_side():
    frames = [
        _lm("left_hip", 200, 400, view="front"),
        _lm("left_knee", 200, 550, view="front"),
        _lm("left_ankle", 200, 700, view="front"),
        _lm("left_hip", 210, 410, view="side"),
        _lm("left_knee", 260, 530, view="side"),
        _lm("left_ankle", 220, 710, view="side"),
    ]
    assert estimate_knee_flexion_deg(frames, "left") == 0.0


def test_falls_back_to_side_view():
    frames = [
        _lm("left_hip", 100, 400, view="side"),
        _lm("left_knee", 100, 550, view="side"),
        _lm("left_ankle", 100, 700, view="side"),
    ]
    assert estimate_knee_flexion_deg(frames, "left") == 0.0


def test_unavailable_without_chain():
    frames = [_lm("left_hip", 200, 400, view="front")]
    assert estimate_knee_flexion_deg(frames, "left") is None


def test_hka_straight_leg_front_view():
    frames = [
        _lm("left_hip", 200, 400, view="front"),
        _lm("left_knee", 200, 550, view="front"),
        _lm("left_ankle", 200, 700, view="front"),
    ]
    assert estimate_hka_angle_deg(frames, "left") == 180.0


def test_hka_ignores_side_view():
    frames = [
        _lm("left_hip", 100, 400, view="side"),
        _lm("left_knee", 130, 550, view="side"),
        _lm("left_ankle", 100, 700, view="side"),
    ]
    assert estimate_hka_angle_deg(frames, "left") is None


def test_hka_falls_back_to_back_view():
    frames = [
        _lm("right_hip", 260, 400, view="back"),
        _lm("right_knee", 260, 550, view="back"),
        _lm("right_ankle", 260, 700, view="back"),
    ]
    assert estimate_hka_angle_deg(frames, "right") == 180.0
