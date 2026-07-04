"""YOLOv8 pose inference via Ultralytics."""

from __future__ import annotations

import os
from functools import lru_cache

import structlog

from app.pipeline.image_utils import read_image_bgr
from app.pipeline.landmark_mapping import build_unified_landmarks

logger = structlog.get_logger(__name__)

DEFAULT_YOLO_POSE_MODEL = "yolov8n-pose.pt"

# COCO pose keypoint indices
YOLO_KP = {
    "nose": 0,
    "left_eye": 1,
    "right_eye": 2,
    "left_ear": 3,
    "right_ear": 4,
    "left_shoulder": 5,
    "right_shoulder": 6,
    "left_elbow": 7,
    "right_elbow": 8,
    "left_wrist": 9,
    "right_wrist": 10,
    "left_hip": 11,
    "right_hip": 12,
    "left_knee": 13,
    "right_knee": 14,
    "left_ankle": 15,
    "right_ankle": 16,
}


def _resolve_weights_path(weights_path: str | None, variant: str) -> str:
    if variant == "yolo_custom":
        if weights_path and os.path.exists(weights_path):
            return weights_path
        raise FileNotFoundError(
            "yolo_custom requires MODEL_WEIGHTS_PATH pointing to an existing .pt weights file"
        )
    if weights_path and os.path.exists(weights_path):
        return weights_path
    return DEFAULT_YOLO_POSE_MODEL


@lru_cache(maxsize=4)
def _get_yolo_model(resolved_weights: str):
    from ultralytics import YOLO

    logger.info("Loading YOLO pose model", weights=resolved_weights)
    return YOLO(resolved_weights)


def _point_from_yolo(
    keypoints, idx: int, fallback_conf: float = 0.0
) -> tuple[float, float, float] | None:
    if keypoints is None or idx >= len(keypoints):
        return None
    x, y, conf = keypoints[idx]
    confidence = float(conf) if conf is not None else fallback_conf
    if confidence <= 0.0:
        return None
    return float(x), float(y), confidence


def detect_landmarks_in_frame(
    image_path: str,
    view: str,
    weights_path: str | None = None,
    variant: str = "yolo_v8",
) -> list[dict]:
    image = read_image_bgr(image_path)
    if image is None:
        return []

    resolved = _resolve_weights_path(weights_path, variant)
    model = _get_yolo_model(resolved)
    results = model.predict(image, verbose=False, conf=0.25)
    if not results:
        logger.warning("No YOLO results", path=image_path, view=view)
        return []

    result = results[0]
    if result.keypoints is None or len(result.keypoints.data) == 0:
        logger.warning("No YOLO pose detected", path=image_path, view=view)
        return []

    person_kps = result.keypoints.data[0].cpu().numpy()
    points = {name: _point_from_yolo(person_kps, idx) for name, idx in YOLO_KP.items()}

    landmarks = build_unified_landmarks(
        view,
        nose=points["nose"],
        left_ear=points["left_ear"],
        right_ear=points["right_ear"],
        left_eye=points["left_eye"],
        right_eye=points["right_eye"],
        left_shoulder=points["left_shoulder"],
        right_shoulder=points["right_shoulder"],
        left_hip=points["left_hip"],
        right_hip=points["right_hip"],
        left_knee=points["left_knee"],
        right_knee=points["right_knee"],
        left_ankle=points["left_ankle"],
        right_ankle=points["right_ankle"],
    )
    logger.info("YOLO landmarks detected", view=view, count=len(landmarks), variant=variant)
    return landmarks


def detect_all_frames(
    frame_paths: dict[str, str],
    weights_path: str | None = None,
    detector_name: str = "yolo_v8",
    variant: str = "yolo_v8",
) -> dict:
    all_landmarks: list[dict] = []
    for view, path in frame_paths.items():
        all_landmarks.extend(
            detect_landmarks_in_frame(path, view, weights_path=weights_path, variant=variant)
        )
    return {"detector": detector_name, "landmarks": all_landmarks}


def is_backend_ready(variant: str = "yolo_v8", weights_path: str | None = None) -> bool:
    try:
        import ultralytics  # noqa: F401

        resolved = _resolve_weights_path(weights_path, variant)
        if resolved == DEFAULT_YOLO_POSE_MODEL:
            return True
        return os.path.exists(resolved)
    except Exception as exc:
        logger.warning("YOLO backend not ready", variant=variant, error=str(exc))
        return False
