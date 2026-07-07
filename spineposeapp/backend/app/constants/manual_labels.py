"""Clinical manual label fields aligned with posture metrics used in ScanMetricsPanel."""

MANUAL_LABEL_FIELDS: list[dict[str, str | list[dict[str, str]]]] = [
    {
        "group": "Spinal Curves",
        "fields": [
            {"key": "thoracic_kyphosis", "label": "Thoracic Kyphosis"},
            {"key": "lumbar_lordosis", "label": "Lumbar Lordosis"},
        ],
    },
    {
        "group": "Pelvis & Lower Body",
        "fields": [
            {"key": "pelvic_tilt_sagittal", "label": "Pelvic Tilt (Sagittal)"},
            {"key": "pelvic_obliquity", "label": "Pelvic Obliquity"},
            {"key": "knee_flexion_left", "label": "Knee Flexion (L)"},
            {"key": "knee_flexion_right", "label": "Knee Flexion (R)"},
            {"key": "hka_angle_left", "label": "HKA Angle (L)"},
            {"key": "hka_angle_right", "label": "HKA Angle (R)"},
        ],
    },
    {
        "group": "Head & Shoulders",
        "fields": [
            {"key": "forward_head_posture", "label": "Forward Head Posture"},
            {"key": "shoulder_height_asymmetry", "label": "Shoulder Asymmetry"},
            {"key": "jaw_deviation", "label": "Jaw Deviation"},
        ],
    },
    {
        "group": "Spine & Back",
        "fields": [
            {"key": "spine_drift", "label": "Spine Drift"},
            {"key": "scapula_asymmetry", "label": "Scapula Asymmetry"},
            {"key": "vertebral_rotation", "label": "Vertebral Rotation"},
            {"key": "adams_rib_hump", "label": "Adams Rib Hump"},
        ],
    },
]

MANUAL_LABEL_KEYS: frozenset[str] = frozenset(
    field["key"]
    for group in MANUAL_LABEL_FIELDS
    for field in group["fields"]  # type: ignore[union-attr]
)
