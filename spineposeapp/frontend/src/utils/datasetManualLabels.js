export const MANUAL_LABEL_OPTIONS = [
  { value: '', label: '—' },
  { value: 'yes', label: 'Yes' },
  { value: 'no', label: 'No' },
  { value: 'na', label: 'N/A' },
]

export const MANUAL_LABEL_GROUPS = [
  {
    title: 'Spinal Curves',
    fields: [
      { key: 'thoracic_kyphosis', label: 'Thoracic Kyphosis' },
      { key: 'lumbar_lordosis', label: 'Lumbar Lordosis' },
    ],
  },
  {
    title: 'Pelvis & Lower Body',
    fields: [
      { key: 'pelvic_tilt_sagittal', label: 'Pelvic Tilt' },
      { key: 'pelvic_obliquity', label: 'Pelvic Obliquity' },
      { key: 'knee_flexion_left', label: 'Knee Flex (L)' },
      { key: 'knee_flexion_right', label: 'Knee Flex (R)' },
      { key: 'hka_angle_left', label: 'HKA (L)' },
      { key: 'hka_angle_right', label: 'HKA (R)' },
    ],
  },
  {
    title: 'Head & Shoulders',
    fields: [
      { key: 'forward_head_posture', label: 'Forward Head' },
      { key: 'shoulder_height_asymmetry', label: 'Shoulder Asymmetry' },
      { key: 'jaw_deviation', label: 'Jaw Deviation' },
    ],
  },
  {
    title: 'Spine & Back',
    fields: [
      { key: 'spine_drift', label: 'Spine Drift' },
      { key: 'scapula_asymmetry', label: 'Scapula Asymmetry' },
      { key: 'vertebral_rotation', label: 'Vertebral Rotation' },
      { key: 'adams_rib_hump', label: 'Adams Rib Hump' },
    ],
  },
]

export function emptyManualLabelForm() {
  const form = {}
  for (const group of MANUAL_LABEL_GROUPS) {
    for (const field of group.fields) {
      form[field.key] = ''
    }
  }
  return form
}

export function manualLabelsFromKeypoints(keypoints) {
  const form = emptyManualLabelForm()
  const saved = keypoints?.manual_labels || {}
  for (const key of Object.keys(form)) {
    if (saved[key]) form[key] = saved[key]
  }
  return form
}

export function manualLabelsPayload(form) {
  const payload = {}
  for (const [key, value] of Object.entries(form)) {
    payload[key] = value || null
  }
  return payload
}
