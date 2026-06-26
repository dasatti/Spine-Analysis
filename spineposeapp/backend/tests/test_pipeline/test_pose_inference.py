import cv2
import numpy as np

from app.pipeline.pose_inference import detect_landmarks_in_frame


def test_detect_landmarks_on_synthetic_person(tmp_path):
    image_path = tmp_path / "person.png"
    canvas = np.zeros((640, 480, 3), dtype=np.uint8)
    # Simple stick figure for YOLO to potentially detect structure
    cv2.circle(canvas, (240, 80), 20, (255, 255, 255), -1)
    cv2.line(canvas, (240, 100), (240, 220), (255, 255, 255), 8)
    cv2.line(canvas, (240, 140), (180, 180), (255, 255, 255), 6)
    cv2.line(canvas, (240, 140), (300, 180), (255, 255, 255), 6)
    cv2.line(canvas, (240, 220), (200, 320), (255, 255, 255), 6)
    cv2.line(canvas, (240, 220), (280, 320), (255, 255, 255), 6)
    cv2.imwrite(str(image_path), canvas)

    landmarks = detect_landmarks_in_frame(str(image_path), "front")
    assert isinstance(landmarks, list)
