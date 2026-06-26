"""Shared pose inference using MediaPipe Pose Landmarker (Tasks API)."""

from __future__ import annotations

import urllib.request
from functools import lru_cache
from pathlib import Path

import cv2
import mediapipe as mp
import numpy as np
import structlog
from mediapipe.tasks.python import vision

logger = structlog.get_logger(__name__)

MODEL_DIR = Path(__file__).resolve().parent / "models"
MODEL_PATH = MODEL_DIR / "pose_landmarker_heavy.task"
MODEL_URL = (
    "https://storage.googleapis.com/mediapipe-models/pose_landmarker/"
    "pose_landmarker_heavy/float16/1/pose_landmarker_heavy.task"
)

# MediaPipe Pose landmark indices
MP = {
    "nose": 0,
    "left_ear": 7,
    "right_ear": 8,
    "left_shoulder": 11,
    "right_shoulder": 12,
    "left_hip": 23,
    "right_hip": 24,
    "left_knee": 25,
    "right_knee": 26,
    "left_ankle": 27,
    "right_ankle": 28,
}

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

DIRECT_MAP: dict[str, str] = {
    "left_ear": "left_ear",
    "right_ear": "right_ear",
    "left_shoulder": "left_shoulder",
    "right_shoulder": "right_shoulder",
    "left_hip": "left_hip",
    "right_hip": "right_hip",
    "left_knee": "left_knee",
    "right_knee": "right_knee",
    "left_ankle": "left_ankle",
    "right_ankle": "right_ankle",
}


def _ensure_model() -> Path:
    if MODEL_PATH.exists() and MODEL_PATH.stat().st_size > 0:
        return MODEL_PATH

    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    logger.info("Downloading MediaPipe pose model", url=MODEL_URL, path=str(MODEL_PATH))
    urllib.request.urlretrieve(MODEL_URL, MODEL_PATH)
    return MODEL_PATH


@lru_cache(maxsize=1)
def _get_pose_detector() -> vision.PoseLandmarker:
    model_path = _ensure_model()
    options = vision.PoseLandmarkerOptions(
        base_options=mp.tasks.BaseOptions(model_asset_path=str(model_path)),
        running_mode=vision.RunningMode.IMAGE,
        num_poses=1,
        min_pose_detection_confidence=0.5,
        min_pose_presence_confidence=0.5,
        min_tracking_confidence=0.5,
    )
    return vision.PoseLandmarker.create_from_options(options)


def _read_image_bgr(image_path: str) -> np.ndarray | None:
    image = cv2.imread(image_path, cv2.IMREAD_COLOR)
    if image is not None:
        return image
    try:
        from PIL import Image

        with Image.open(image_path) as pil_image:
            rgb = np.array(pil_image.convert("RGB"))
        return cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
    except Exception as exc:
        logger.warning("Failed to read image", path=image_path, error=str(exc))
        return None


def _landmark_dict(name: str, x: float, y: float, confidence: float, view: str) -> dict:
    return {
        "name": name,
        "x": round(x, 2),
        "y": round(y, 2),
        "confidence": round(max(0.0, min(1.0, confidence)), 4),
        "view": view,
    }


def _point_from_mp(landmarks, idx: int, width: int, height: int) -> tuple[float, float, float]:
    lm = landmarks[idx]
    visibility = float(getattr(lm, "visibility", getattr(lm, "presence", 1.0)))
    return lm.x * width, lm.y * height, visibility


def _midpoint(
    a: tuple[float, float, float], b: tuple[float, float, float]
) -> tuple[float, float, float]:
    return (a[0] + b[0]) / 2.0, (a[1] + b[1]) / 2.0, min(a[2], b[2])


def _interpolate_spine(
    neck: tuple[float, float, float], sacrum: tuple[float, float, float]
) -> dict[str, tuple[float, float, float]]:
    points: dict[str, tuple[float, float, float]] = {}
    for i, name in enumerate(SPINE_CHAIN):
        t = i / max(len(SPINE_CHAIN) - 1, 1)
        x = neck[0] * (1.0 - t) + sacrum[0] * t
        y = neck[1] * (1.0 - t) + sacrum[1] * t
        conf = min(neck[2], sacrum[2]) * (0.95 - abs(t - 0.5) * 0.1)
        points[name] = (x, y, max(conf, 0.0))
    return points


def detect_landmarks_in_frame(
    image_path: str,
    view: str,
    weights_path: str | None = None,
) -> list[dict]:
    """Run pose inference on a single frame and map to unified landmark schema."""
    del weights_path  # MediaPipe backend; custom weights reserved for future SpinePose model
    image = _read_image_bgr(image_path)
    if image is None:
        return []

    height, width = image.shape[:2]
    rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
    landmarker = _get_pose_detector()
    results = landmarker.detect(mp_image)
    if not results.pose_landmarks:
        logger.warning("No pose detected", path=image_path, view=view)
        return []

    lms = results.pose_landmarks[0]
    left_shoulder = _point_from_mp(lms, MP["left_shoulder"], width, height)
    right_shoulder = _point_from_mp(lms, MP["right_shoulder"], width, height)
    left_hip = _point_from_mp(lms, MP["left_hip"], width, height)
    right_hip = _point_from_mp(lms, MP["right_hip"], width, height)
    shoulder_mid = _midpoint(left_shoulder, right_shoulder)
    hip_mid = _midpoint(left_hip, right_hip)
    neck = (
        shoulder_mid[0],
        shoulder_mid[1] - abs(left_shoulder[1] - right_shoulder[1]) * 0.15 - 8.0,
        min(left_shoulder[2], right_shoulder[2]) * 0.9,
    )
    nose = _point_from_mp(lms, MP["nose"], width, height)

    landmarks: list[dict] = []
    for target, mp_name in DIRECT_MAP.items():
        x, y, conf = _point_from_mp(lms, MP[mp_name], width, height)
        if conf > 0.3:
            landmarks.append(_landmark_dict(target, x, y, conf, view))

    c7_x, c7_y, c7_conf = neck
    landmarks.append(_landmark_dict("c7_proxy", c7_x, c7_y, c7_conf, view))

    for spine_name, (sx, sy, sconf) in _interpolate_spine(neck, hip_mid).items():
        if sconf > 0.3:
            landmarks.append(_landmark_dict(spine_name, sx, sy, sconf, view))

    if nose[2] > 0.3:
        landmarks.append(_landmark_dict("jaw_midpoint", nose[0], nose[1], nose[2] * 0.95, view))
        landmarks.append(
            _landmark_dict("facial_midline", nose[0], nose[1] - 10, nose[2] * 0.9, view)
        )

    logger.info("Pose landmarks detected", view=view, count=len(landmarks))
    return landmarks


def detect_all_frames(
    frame_paths: dict[str, str],
    weights_path: str | None = None,
    detector_name: str = "mediapipe_pose",
) -> dict:
    """Detect landmarks across all uploaded views."""
    all_landmarks: list[dict] = []
    for view, path in frame_paths.items():
        all_landmarks.extend(detect_landmarks_in_frame(path, view, weights_path))
    return {"detector": detector_name, "landmarks": all_landmarks}
