from app.pipeline.base import Keypoint
from app.pipeline.keypoint_normalizer import KeypointNormalizer, REQUIRED_LANDMARKS


def test_normalize_landmarks_list_format():
    raw = {
        "landmarks": [
            {"name": "left_shoulder", "x": 10.0, "y": 20.0, "confidence": 0.95, "view": "front"},
            {"name": "left_shoulder", "x": 12.0, "y": 22.0, "confidence": 0.50, "view": "side"},
        ]
    }
    result = KeypointNormalizer.normalize(raw, "spinepose_v2")
    left_shoulder = next(kp for kp in result if kp.name == "left_shoulder")
    assert left_shoulder.confidence == 0.95
    assert left_shoulder.x == 10.0


def test_normalize_view_dict_format():
    raw = {
        "front": [
            {"name": "left_hip", "x": 1.0, "y": 2.0, "confidence": 0.88},
        ]
    }
    result = KeypointNormalizer.normalize(raw, "spinepose_v2")
    left_hip = next(kp for kp in result if kp.name == "left_hip")
    assert left_hip.confidence == 0.88
    assert left_hip.source_view == "front"


def test_normalize_fills_missing_landmarks_with_zero_confidence():
    raw = {"landmarks": []}
    result = KeypointNormalizer.normalize(raw, "spinepose_v2")
    assert len(result) == len(REQUIRED_LANDMARKS)
    assert all(kp.confidence == 0.0 for kp in result)
