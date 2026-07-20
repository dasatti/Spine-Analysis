"""YOLO object-detection model for back-view scoliosis screening."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import structlog

from app.config import settings

logger = structlog.get_logger(__name__)

DEFAULT_WEIGHTS = Path(__file__).resolve().parents[2] / "models" / "yolo26n-scoliosis.pt"
KEYPOINT_CLASS = "keypoint"
BACK_CLASS = "back"
SCOLIOSIS_LABEL = "scoliosis"
NORMAL_LABEL = "normal"


@dataclass(frozen=True)
class ScoliosisDetectionBox:
    class_name: str
    x1: float
    y1: float
    x2: float
    y2: float
    confidence: float


@dataclass(frozen=True)
class ScoliosisPrediction:
    class_name: str
    confidence: float
    lateral_index: float
    keypoint_count: int
    detections: tuple[ScoliosisDetectionBox, ...]
    image_width: int
    image_height: int


def resolve_weights_path(weights_path: str | None = None) -> Path:
    configured = weights_path or settings.scoliosis_detector_weights_path
    if configured:
        path = Path(configured)
        if path.exists():
            return path
    if DEFAULT_WEIGHTS.exists():
        return DEFAULT_WEIGHTS
    raise FileNotFoundError(
        "Scoliosis detector weights not found. "
        f"Expected at {DEFAULT_WEIGHTS} or SCOLIOSIS_DETECTOR_WEIGHTS_PATH."
    )


@lru_cache(maxsize=2)
def _get_model(resolved_weights: str):
    from ultralytics import YOLO

    logger.info("Loading scoliosis detector", weights=resolved_weights)
    return YOLO(resolved_weights)


def _normalize_class_name(raw: str) -> str:
    return raw.strip().lower().replace(" ", "")


def predict_scoliosis(
    image_path: str,
    weights_path: str | None = None,
    *,
    imgsz: int = 640,
) -> ScoliosisPrediction:
    """Detect back keypoints and derive a scoliosis screening label."""
    resolved = str(resolve_weights_path(weights_path))
    model = _get_model(resolved)
    results = model.predict(source=image_path, imgsz=imgsz, verbose=False)
    if not results:
        raise RuntimeError("Scoliosis detector returned no results")

    result = results[0]
    boxes = result.boxes
    if boxes is None or len(boxes) == 0:
        raise RuntimeError("Scoliosis detector found no objects")

    names = {int(k): _normalize_class_name(str(v)) for k, v in result.names.items()}
    conf_threshold = settings.scoliosis_keypoint_conf_threshold
    min_keypoints = settings.scoliosis_min_keypoints

    keypoints: list[tuple[float, float, float]] = []
    back_boxes: list[tuple[float, float, float, float, float]] = []
    detections: list[ScoliosisDetectionBox] = []

    for index in range(len(boxes)):
        cls_id = int(boxes.cls[index].item())
        conf = float(boxes.conf[index].item())
        x1, y1, x2, y2 = (float(v) for v in boxes.xyxy[index].tolist())
        label = names.get(cls_id, "")

        if label not in {KEYPOINT_CLASS, BACK_CLASS} or conf < conf_threshold:
            continue

        detections.append(
            ScoliosisDetectionBox(
                class_name=label,
                x1=x1,
                y1=y1,
                x2=x2,
                y2=y2,
                confidence=conf,
            )
        )
        if label == BACK_CLASS:
            back_boxes.append((x1, y1, x2, y2, conf))
        elif label == KEYPOINT_CLASS:
            keypoints.append(((x1 + x2) / 2.0, (y1 + y2) / 2.0, conf))

    if len(keypoints) < min_keypoints:
        raise RuntimeError(
            f"Insufficient KeyPoint detections ({len(keypoints)} < {min_keypoints})"
        )

    back_box = max(back_boxes, key=lambda item: item[4])[0:4] if back_boxes else None
    if back_box:
        midline_x = (back_box[0] + back_box[2]) / 2.0
        back_height = max(back_box[3] - back_box[1], 1.0)
    else:
        midline_x = sum(point[0] for point in keypoints) / len(keypoints)
        back_height = float(max(result.orig_shape))

    max_deviation_px = max(abs(point[0] - midline_x) for point in keypoints)
    lateral_index = max_deviation_px / back_height
    threshold = settings.scoliosis_lateral_index_threshold
    class_name = SCOLIOSIS_LABEL if lateral_index >= threshold else NORMAL_LABEL
    confidence = sum(point[2] for point in keypoints) / len(keypoints)
    orig_h, orig_w = result.orig_shape[:2]

    logger.info(
        "Scoliosis detection complete",
        class_name=class_name,
        lateral_index=round(lateral_index, 4),
        threshold=threshold,
        keypoint_count=len(keypoints),
        detection_count=len(detections),
        confidence=round(confidence, 4),
        image_path=image_path,
    )
    return ScoliosisPrediction(
        class_name=class_name,
        confidence=confidence,
        lateral_index=lateral_index,
        keypoint_count=len(keypoints),
        detections=tuple(detections),
        image_width=int(orig_w),
        image_height=int(orig_h),
    )


def is_backend_ready(weights_path: str | None = None) -> bool:
    try:
        resolve_weights_path(weights_path)
        return True
    except Exception:
        return False
