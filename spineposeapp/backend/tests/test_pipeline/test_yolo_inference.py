import cv2
import numpy as np
import pytest

from app.pipeline.landmark_mapping import build_unified_landmarks


def test_build_unified_landmarks_includes_spine_chain():
    landmarks = build_unified_landmarks(
        "front",
        nose=(240.0, 80.0, 0.9),
        left_ear=(220.0, 75.0, 0.85),
        right_ear=(260.0, 75.0, 0.85),
        left_shoulder=(200.0, 140.0, 0.95),
        right_shoulder=(280.0, 140.0, 0.95),
        left_hip=(210.0, 220.0, 0.9),
        right_hip=(270.0, 220.0, 0.9),
        left_knee=(205.0, 300.0, 0.88),
        right_knee=(275.0, 300.0, 0.88),
        left_ankle=(200.0, 380.0, 0.85),
        right_ankle=(280.0, 380.0, 0.85),
    )
    names = {item["name"] for item in landmarks}
    assert "c7_proxy" in names
    assert "spine_l5" in names
    assert "left_shoulder" in names


@pytest.mark.skipif(
    not __import__("importlib").util.find_spec("ultralytics"),
    reason="ultralytics not installed",
)
def test_yolo_detect_landmarks_on_synthetic_person(tmp_path):
    from app.pipeline.yolo_inference import detect_landmarks_in_frame

    image_path = tmp_path / "person.png"
    canvas = np.zeros((640, 480, 3), dtype=np.uint8)
    cv2.circle(canvas, (240, 80), 20, (255, 255, 255), -1)
    cv2.line(canvas, (240, 100), (240, 220), (255, 255, 255), 8)
    cv2.line(canvas, (240, 140), (180, 180), (255, 255, 255), 6)
    cv2.line(canvas, (240, 140), (300, 180), (255, 255, 255), 6)
    cv2.line(canvas, (240, 220), (200, 320), (255, 255, 255), 6)
    cv2.line(canvas, (240, 220), (280, 320), (255, 255, 255), 6)
    cv2.imwrite(str(image_path), canvas)

    landmarks = detect_landmarks_in_frame(str(image_path), "front")
    assert isinstance(landmarks, list)
