/** Mirror of backend ``twin_landmarks_from_frame`` for client-side fallback. */
export function twinLandmarksFromFrame(frameLandmarks) {
  const twin = []
  for (const kp of frameLandmarks) {
    const view = kp.view || kp.source_view || ''
    if (!['front', 'side', 'back'].includes(view)) continue
    if ((kp.confidence ?? 0) <= 0.3) continue
    const x = Number(kp.x)
    const y = Number(kp.y)
    const coords =
      view === 'side'
        ? { x3d: 0, y3d: y, z3d: x }
        : { x3d: x, y3d: y, z3d: 0 }
    twin.push({
      name: kp.name,
      ...coords,
      confidence: kp.confidence,
      source_view: view,
    })
  }
  return twin
}

const CAPTURE_VIEWS = ['front', 'side', 'back']

export function resolveTwinLandmarks(keypoints) {
  const twin = keypoints?.twin_landmarks
  const frames = keypoints?.frame_landmarks

  if (Array.isArray(twin) && twin.length) {
    const views = new Set(twin.map((kp) => kp.source_view || 'front'))
    if (CAPTURE_VIEWS.every((view) => views.has(view))) return twin
  }

  if (Array.isArray(frames) && frames.length) {
    const rebuilt = twinLandmarksFromFrame(frames)
    if (rebuilt.length) return rebuilt
  }

  if (Array.isArray(twin) && twin.length) return twin
  return keypoints?.landmarks || []
}
