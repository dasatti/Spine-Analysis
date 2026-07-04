"""MediaPipe Pose Landmarker inference for SpinePose v2."""

from __future__ import annotations

import urllib.request
from functools import lru_cache
from pathlib import Path

import cv2
import mediapipe as mp
import structlog
from mediapipe.tasks.python import vision

from app.pipeline.image_utils import read_image_bgr
from app.pipeline.landmark_mapping import build_unified_landmarks, build_world_landmarks

logger = structlog.get_logger(__name__)

MODEL_DIR = Path(__file__).resolve().parent / "models"
MODEL_PATH = MODEL_DIR / "pose_landmarker_heavy.task"
MODEL_URL = (
    "https://storage.googleapis.com/mediapipe-models/pose_landmarker/"
    "pose_landmarker_heavy/float16/1/pose_landmarker_heavy.task"
)

MP = {
    "nose": 0,
    "left_eye": 2,
    "right_eye": 5,
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


def _point_from_mp(landmarks, idx: int, width: int, height: int) -> tuple[float, float, float]:
    lm = landmarks[idx]
    visibility = float(getattr(lm, "visibility", getattr(lm, "presence", 1.0)))
    return lm.x * width, lm.y * height, visibility


def _world_point_from_mp(world_landmarks, idx: int) -> tuple[float, float, float, float]:
    """Metric world landmark in millimetres (MediaPipe returns metres)."""
    lm = world_landmarks[idx]
    visibility = float(getattr(lm, "visibility", getattr(lm, "presence", 1.0)))
    return lm.x * 1000.0, lm.y * 1000.0, lm.z * 1000.0, visibility


def _detect_frame(image_path: str, view: str) -> tuple[list[dict], list[dict]]:
    """Run inference once, returning (2D pixel landmarks, metric world landmarks)."""
    image = read_image_bgr(image_path)
    if image is None:
        return [], []

    height, width = image.shape[:2]
    rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
    landmarker = _get_pose_detector()
    results = landmarker.detect(mp_image)
    if not results.pose_landmarks:
        logger.warning("No MediaPipe pose detected", path=image_path, view=view)
        return [], []

    lms = results.pose_landmarks[0]
    landmarks = build_unified_landmarks(
        view,
        nose=_point_from_mp(lms, MP["nose"], width, height),
        left_ear=_point_from_mp(lms, MP["left_ear"], width, height),
        right_ear=_point_from_mp(lms, MP["right_ear"], width, height),
        left_eye=_point_from_mp(lms, MP["left_eye"], width, height),
        right_eye=_point_from_mp(lms, MP["right_eye"], width, height),
        left_shoulder=_point_from_mp(lms, MP["left_shoulder"], width, height),
        right_shoulder=_point_from_mp(lms, MP["right_shoulder"], width, height),
        left_hip=_point_from_mp(lms, MP["left_hip"], width, height),
        right_hip=_point_from_mp(lms, MP["right_hip"], width, height),
        left_knee=_point_from_mp(lms, MP["left_knee"], width, height),
        right_knee=_point_from_mp(lms, MP["right_knee"], width, height),
        left_ankle=_point_from_mp(lms, MP["left_ankle"], width, height),
        right_ankle=_point_from_mp(lms, MP["right_ankle"], width, height),
    )

    world_landmarks: list[dict] = []
    if results.pose_world_landmarks:
        world = results.pose_world_landmarks[0]
        world_landmarks = build_world_landmarks(
            view,
            {name: _world_point_from_mp(world, idx) for name, idx in MP.items()},
        )

    logger.info(
        "MediaPipe landmarks detected",
        view=view,
        count=len(landmarks),
        world_count=len(world_landmarks),
    )
    return landmarks, world_landmarks


def detect_landmarks_in_frame(
    image_path: str,
    view: str,
    weights_path: str | None = None,
) -> list[dict]:
    """Run MediaPipe pose inference on a single frame (2D landmarks only)."""
    del weights_path  # reserved for future custom SpinePose v2 weights
    landmarks, _ = _detect_frame(image_path, view)
    return landmarks


def detect_all_frames(
    frame_paths: dict[str, str],
    weights_path: str | None = None,
    detector_name: str = "spinepose_v2",
) -> dict:
    del weights_path
    all_landmarks: list[dict] = []
    twin_landmarks: list[dict] = []
    # Prefer the front frame for the digital twin; fall back to any view with world data.
    ordered_views = sorted(frame_paths, key=lambda v: 0 if v == "front" else 1)
    for view in ordered_views:
        landmarks, world_landmarks = _detect_frame(frame_paths[view], view)
        all_landmarks.extend(landmarks)
        if not twin_landmarks and world_landmarks and view != "adams":
            twin_landmarks = world_landmarks
    return {
        "detector": detector_name,
        "landmarks": all_landmarks,
        "world_landmarks": twin_landmarks,
    }


def is_backend_ready() -> bool:
    try:
        _ensure_model()
        return True
    except Exception:
        return False
