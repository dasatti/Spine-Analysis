<script setup>
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'

const props = defineProps({
  landmarks: { type: Array, default: () => [] },
  view: { type: String, default: 'front' },
})

const containerRef = ref(null)
const currentView = ref(props.view)
const showSpineCurve = ref(true)
let renderer = null
let scene = null
let camera = null
let controls = null
let animationId = null
let cameraDistance = 80

const SPINE_CHAIN = [
  'spine_c7', 'spine_t1', 'spine_t4', 'spine_t7',
  'spine_t10', 'spine_l1', 'spine_l3', 'spine_l5', 'spine_s1',
]

// Bone connections approximating the human skeleton (matches 2D overlay).
const BONES = [
  ['left_ear', 'left_eye'],
  ['right_ear', 'right_eye'],
  ['left_ear', 'c7_proxy'],
  ['right_ear', 'c7_proxy'],
  ['c7_proxy', 'spine_c7'],
  ['left_shoulder', 'right_shoulder'],
  ['left_hip', 'right_hip'],
  ['left_hip', 'left_knee'],
  ['left_knee', 'left_ankle'],
  ['right_hip', 'right_knee'],
  ['right_knee', 'right_ankle'],
  ['spine_s1', 'left_hip'],
  ['spine_s1', 'right_hip'],
]

const landmarkList = computed(() => {
  if (Array.isArray(props.landmarks)) return props.landmarks
  if (props.landmarks?.landmarks) return props.landmarks.landmarks
  return []
})

const usablePoints = computed(() =>
  landmarkList.value.filter((kp) => kp.x3d != null && kp.confidence >= 0.3)
)

const hasPoints = computed(() => usablePoints.value.length > 0)

// Normalise: centre the cloud at the origin and scale body height to 100 units.
const normalizedPoints = computed(() => {
  const pts = usablePoints.value
  if (!pts.length) return []
  const xs = pts.map((kp) => kp.x3d)
  const ys = pts.map((kp) => kp.y3d)
  const zs = pts.map((kp) => kp.z3d ?? 0)
  const center = {
    x: (Math.min(...xs) + Math.max(...xs)) / 2,
    y: (Math.min(...ys) + Math.max(...ys)) / 2,
    z: (Math.min(...zs) + Math.max(...zs)) / 2,
  }
  const spanY = Math.max(...ys) - Math.min(...ys)
  const spanX = Math.max(...xs) - Math.min(...xs)
  const scale = 100 / Math.max(spanY, spanX, 1)
  return pts.map((kp) => ({
    name: kp.name,
    // y is down in landmark space; flip so the head is up in the scene.
    x: (kp.x3d - center.x) * scale,
    y: -(kp.y3d - center.y) * scale,
    z: ((kp.z3d ?? 0) - center.z) * scale,
  }))
})

function initThree() {
  if (!containerRef.value || !hasPoints.value) return

  const THREE = window.THREE
  if (!THREE) return

  const width = containerRef.value.clientWidth
  const height = containerRef.value.clientHeight || 400

  scene = new THREE.Scene()
  scene.background = new THREE.Color(0x0a0a0a)

  camera = new THREE.PerspectiveCamera(50, width / height, 0.1, 2000)
  cameraDistance = 140
  setCameraPreset(currentView.value)

  renderer = new THREE.WebGLRenderer({ antialias: true })
  renderer.setSize(width, height)
  containerRef.value.innerHTML = ''
  containerRef.value.appendChild(renderer.domElement)

  if (window.THREE.OrbitControls) {
    controls = new window.THREE.OrbitControls(camera, renderer.domElement)
    controls.enableDamping = true
  }

  const byName = {}
  for (const p of normalizedPoints.value) byName[p.name] = p

  // Small red spheres with a white outline shell, matching the 2D overlay.
  const dotMaterial = new THREE.MeshBasicMaterial({ color: 0xff3b30 })
  const outlineMaterial = new THREE.MeshBasicMaterial({
    color: 0xffffff,
    side: THREE.BackSide,
  })
  for (const p of normalizedPoints.value) {
    const isSpine = p.name.startsWith('spine_') || p.name === 'c7_proxy'
    const radius = isSpine ? 0.45 : 0.6
    const dot = new THREE.Mesh(new THREE.SphereGeometry(radius, 12, 12), dotMaterial)
    dot.position.set(p.x, p.y, p.z)
    scene.add(dot)
    const outline = new THREE.Mesh(
      new THREE.SphereGeometry(radius * 1.35, 12, 12),
      outlineMaterial
    )
    outline.position.set(p.x, p.y, p.z)
    scene.add(outline)
  }

  const boneMaterial = new THREE.LineBasicMaterial({ color: 0x2f80ed })
  for (const [a, b] of BONES) {
    const pa = byName[a]
    const pb = byName[b]
    if (!pa || !pb) continue
    const geometry = new THREE.BufferGeometry().setFromPoints([
      new THREE.Vector3(pa.x, pa.y, pa.z),
      new THREE.Vector3(pb.x, pb.y, pb.z),
    ])
    scene.add(new THREE.Line(geometry, boneMaterial))
  }

  if (showSpineCurve.value) {
    const spinePoints = SPINE_CHAIN.map((name) => byName[name]).filter(Boolean)
    if (spinePoints.length > 1) {
      const curvePoints = spinePoints.map((p) => new THREE.Vector3(p.x, p.y, p.z))
      const geometry = new THREE.BufferGeometry().setFromPoints(curvePoints)
      const material = new THREE.LineBasicMaterial({ color: 0x2f80ed })
      scene.add(new THREE.Line(geometry, material))
    }
  }

  const grid = new THREE.GridHelper(160, 16, 0x2a2a2a, 0x1f1f1f)
  grid.position.y = -55
  scene.add(grid)

  const animate = () => {
    animationId = requestAnimationFrame(animate)
    controls?.update()
    renderer.render(scene, camera)
  }
  animate()
}

function setCameraPreset(view) {
  if (!camera) return
  const d = cameraDistance
  const presets = {
    front: { x: 0, y: 0, z: d },
    side: { x: d, y: 0, z: 0 },
    back: { x: 0, y: 0, z: -d },
  }
  const p = presets[view] || presets.front
  camera.position.set(p.x, p.y, p.z)
  camera.lookAt(0, 0, 0)
}

function cleanup() {
  if (animationId) cancelAnimationFrame(animationId)
  renderer?.dispose()
  renderer = null
  scene = null
  camera = null
  controls = null
}

function loadScripts() {
  return new Promise((resolve) => {
    if (window.THREE) {
      resolve()
      return
    }
    const three = document.createElement('script')
    three.src = 'https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js'
    three.onload = () => {
      const controlsScript = document.createElement('script')
      controlsScript.src =
        'https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js'
      controlsScript.onload = resolve
      document.head.appendChild(controlsScript)
    }
    document.head.appendChild(three)
  })
}

watch([landmarkList, showSpineCurve], async () => {
  cleanup()
  await loadScripts()
  initThree()
})

onMounted(async () => {
  await loadScripts()
  initThree()
})

onUnmounted(cleanup)

function switchView(view) {
  currentView.value = view
  setCameraPreset(view)
}
</script>

<template>
  <div class="bg-[#1A1A1A] border border-outline-variant">
    <div ref="containerRef" class="w-full h-[400px] relative">
      <div
        v-if="!hasPoints"
        class="absolute inset-0 flex items-center justify-center text-on-surface-variant"
      >
        3D twin not available for this scan
      </div>
    </div>
    <div class="flex items-center justify-between p-4 border-t border-outline-variant">
      <div class="flex gap-2">
        <button
          v-for="v in ['front', 'side', 'back']"
          :key="v"
          :class="[
            'px-4 py-2 font-label-caps text-[10px] border transition-colors',
            currentView === v
              ? 'bg-primary-container text-[#0A0A0A] border-primary-container'
              : 'border-outline-variant text-on-surface-variant hover:text-on-surface',
          ]"
          type="button"
          @click="switchView(v)"
        >
          {{ v }}
        </button>
      </div>
      <label class="flex items-center gap-2 text-on-surface-variant text-sm cursor-pointer">
        <input v-model="showSpineCurve" type="checkbox" class="custom-checkbox" />
        Spine curve overlay
      </label>
    </div>
  </div>
</template>
