from app.config import settings
from app.pipeline.base import Keypoint

REQUIRED_LANDMARKS: list[str] = [
    "left_ear",
    "right_ear",
    "c7_proxy",
    "left_shoulder",
    "right_shoulder",
    "left_hip",
    "right_hip",
    "left_knee",
    "right_knee",
    "left_ankle",
    "right_ankle",
    "spine_c7",
    "spine_t1",
    "spine_t4",
    "spine_t7",
    "spine_t10",
    "spine_l1",
    "spine_l3",
    "spine_l5",
    "spine_s1",
    "jaw_midpoint",
    "facial_midline",
]


class KeypointNormalizer:
    """Map detector-specific raw output to unified Keypoint objects."""

    @staticmethod
    def normalize(raw_keypoints: dict, detector_model: str) -> list[Keypoint]:
        entries = KeypointNormalizer._extract_entries(raw_keypoints)
        best: dict[str, Keypoint] = {}
        for entry in entries:
            name = str(entry.get("name", ""))
            if not name:
                continue
            confidence = float(entry.get("confidence", 0.0))
            view = str(entry.get("view") or entry.get("source_view") or "front")
            candidate = Keypoint(
                name=name,
                x=float(entry.get("x", 0.0)),
                y=float(entry.get("y", 0.0)),
                confidence=confidence,
                source_view=view,
            )
            existing = best.get(name)
            if existing is None or candidate.confidence > existing.confidence:
                best[name] = candidate

        normalized: list[Keypoint] = []
        for name in REQUIRED_LANDMARKS:
            if name in best:
                normalized.append(best[name])
            else:
                normalized.append(
                    Keypoint(
                        name=name,
                        x=0.0,
                        y=0.0,
                        confidence=0.0,
                        source_view="front",
                    )
                )

        threshold = settings.keypoint_confidence_threshold
        for kp in normalized:
            if kp.confidence < threshold:
                continue
        return normalized

    @staticmethod
    def _extract_entries(raw_keypoints: dict) -> list[dict]:
        if "landmarks" in raw_keypoints and isinstance(raw_keypoints["landmarks"], list):
            return raw_keypoints["landmarks"]
        entries: list[dict] = []
        for view, value in raw_keypoints.items():
            if view in {"detector", "model"}:
                continue
            if isinstance(value, list):
                for item in value:
                    if isinstance(item, dict):
                        item.setdefault("view", view)
                        entries.append(item)
            elif isinstance(value, dict):
                for name, coords in value.items():
                    if isinstance(coords, dict):
                        entries.append({"name": name, "view": view, **coords})
        return entries
