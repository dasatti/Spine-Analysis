"""Re-derive synthetic spine/face landmarks from edited body joints."""

from __future__ import annotations

from app.pipeline.landmark_mapping import SPINE_CHAIN, build_unified_landmarks

BODY_LANDMARK_NAMES = frozenset(
    {
        "left_ear",
        "right_ear",
        "left_eye",
        "right_eye",
        "left_shoulder",
        "right_shoulder",
        "left_hip",
        "right_hip",
        "left_knee",
        "right_knee",
        "left_ankle",
        "right_ankle",
        "jaw_midpoint",
    }
)

SYNTHETIC_LANDMARK_NAMES = frozenset(
    {
        "c7_proxy",
        "jaw_midpoint",
        "facial_midline",
        *SPINE_CHAIN,
    }
)

SPINE_LANDMARK_NAMES = frozenset(SPINE_CHAIN) | {"c7_proxy"}


def _point_from_landmark(kp: dict | None) -> tuple[float, float, float] | None:
    if not kp:
        return None
    confidence = float(kp.get("confidence", 0.0))
    if confidence <= 0.3:
        return None
    return float(kp["x"]), float(kp["y"]), confidence


def refresh_synthetic_landmarks_for_view(
    view: str,
    view_landmarks: list[dict],
    *,
    preserve_manual_spine: bool = False,
) -> list[dict]:
    """Replace synthetic landmarks using current body-joint positions for one view."""
    by_name = {kp["name"]: kp for kp in view_landmarks if kp.get("name")}

    refreshed = build_unified_landmarks(
        view,
        nose=_point_from_landmark(by_name.get("jaw_midpoint")),
        left_ear=_point_from_landmark(by_name.get("left_ear")),
        right_ear=_point_from_landmark(by_name.get("right_ear")),
        left_eye=_point_from_landmark(by_name.get("left_eye")),
        right_eye=_point_from_landmark(by_name.get("right_eye")),
        left_shoulder=_point_from_landmark(by_name.get("left_shoulder")),
        right_shoulder=_point_from_landmark(by_name.get("right_shoulder")),
        left_hip=_point_from_landmark(by_name.get("left_hip")),
        right_hip=_point_from_landmark(by_name.get("right_hip")),
        left_knee=_point_from_landmark(by_name.get("left_knee")),
        right_knee=_point_from_landmark(by_name.get("right_knee")),
        left_ankle=_point_from_landmark(by_name.get("left_ankle")),
        right_ankle=_point_from_landmark(by_name.get("right_ankle")),
    )
    refreshed_by_name = {kp["name"]: kp for kp in refreshed}

    merged: list[dict] = []
    seen: set[str] = set()

    for kp in view_landmarks:
        name = kp.get("name")
        if not name or name in seen:
            continue
        if name in BODY_LANDMARK_NAMES:
            merged.append(kp)
        elif name in SYNTHETIC_LANDMARK_NAMES:
            if preserve_manual_spine and name in SPINE_LANDMARK_NAMES:
                merged.append(kp)
            elif name in refreshed_by_name:
                merged.append(refreshed_by_name[name])
        else:
            merged.append(kp)
        seen.add(name)

    for name, kp in refreshed_by_name.items():
        if name not in seen:
            merged.append(kp)
            seen.add(name)

    return merged


def refresh_frame_landmarks(
    frame_landmarks: list[dict],
    *,
    views: list[str] | None = None,
    preserve_manual_spine: bool = False,
) -> list[dict]:
    """Refresh synthetic landmarks for selected views (or all views present)."""
    grouped: dict[str, list[dict]] = {}
    for kp in frame_landmarks:
        view = str(kp.get("view") or kp.get("source_view") or "front")
        grouped.setdefault(view, []).append(kp)

    target_views = views or sorted(grouped.keys())
    refreshed: list[dict] = []
    for view in sorted(grouped.keys()):
        view_landmarks = grouped[view]
        if view in target_views:
            refreshed.extend(
                refresh_synthetic_landmarks_for_view(
                    view,
                    view_landmarks,
                    preserve_manual_spine=preserve_manual_spine,
                )
            )
        else:
            refreshed.extend(view_landmarks)
    return refreshed
