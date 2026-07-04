from app.pipeline.spine_back_metrics import (
    estimate_adams_rib_hump_present,
    estimate_scapula_asymmetry_index,
    estimate_spine_drift_mm,
    estimate_vertebral_rotation_index,
)


def _lm(name, x, y, view="back", confidence=0.9):
    return {"name": name, "x": x, "y": y, "confidence": confidence, "view": view}


def test_spine_drift_from_back_view():
    frames = [
        _lm("left_hip", 200, 500, view="back"),
        _lm("right_hip", 300, 500, view="back"),
        _lm("spine_c7", 255, 200, view="back"),
        _lm("spine_t4", 270, 300, view="back"),
        _lm("spine_l3", 240, 420, view="back"),
        _lm("spine_s1", 250, 500, view="back"),
    ]
    # midline x=250, max dev 20 px * 0.5 = 10 mm
    assert estimate_spine_drift_mm(frames, 0.5) == 10.0


def test_scapula_index_back_view():
    frames = [
        _lm("left_shoulder", 200, 400, view="back"),
        _lm("right_shoulder", 300, 420, view="back"),
    ]
    index = estimate_scapula_asymmetry_index(frames, 0.5)
    assert index is not None
    assert 0.0 < index <= 0.1


def test_adams_rib_hump_detected():
    frames = [
        _lm("left_shoulder", 200, 400, view="adams"),
        _lm("right_shoulder", 300, 430, view="adams"),
    ]
    # 30 px * 0.5 = 15 mm > 8 mm threshold
    assert estimate_adams_rib_hump_present(frames, 0.5) is True


def test_adams_rib_hump_not_detected():
    frames = [
        _lm("left_shoulder", 200, 400, view="adams"),
        _lm("right_shoulder", 300, 405, view="adams"),
    ]
    assert estimate_adams_rib_hump_present(frames, 0.5) is False


def test_vertebral_rotation_index():
    frames = [
        _lm("left_shoulder", 200, 400, view="adams"),
        _lm("right_shoulder", 300, 430, view="adams"),
    ]
    index = estimate_vertebral_rotation_index(frames, 0.5)
    assert index == 0.05
