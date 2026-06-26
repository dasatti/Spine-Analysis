<script setup>
import { onMounted, onUnmounted, ref, watch } from 'vue'

const props = defineProps({
  keypointsJson: { type: Object, default: null },
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

const SPINE_CHAIN = [
  'spine_c7', 'spine_t1', 'spine_t4', 'spine_t7',
  'spine_t10', 'spine_l1', 'spine_l3', 'spine_l5', 'spine_s1',
]

async function initThree() {
  if (!containerRef.value || !props.keypointsJson?.length) return

  const THREE = window.THREE
  if (!THREE) return

  const width = containerRef.value.clientWidth
  const height = containerRef.value.clientHeight || 400

  scene = new THREE.Scene()
  scene.background = new THREE.Color(0x0a0a0a)

  camera = new THREE.PerspectiveCamera(50, width / height, 0.1, 1000)
  setCameraPreset(currentView.value)

  renderer = new THREE.WebGLRenderer({ antialias: true })
  renderer.setSize(width, height)
  containerRef.value.innerHTML = ''
  containerRef.value.appendChild(renderer.domElement)

  if (window.THREE.OrbitControls) {
    controls = new window.THREE.OrbitControls(camera, renderer.domElement)
    controls.enableDamping = true
  }

  const points = props.keypointsJson.filter((kp) => kp.x3d != null)
  for (const kp of points) {
    const geometry = new THREE.SphereGeometry(3, 8, 8)
    const material = new THREE.MeshBasicMaterial({ color: 0xffffff })
    const sphere = new THREE.Mesh(geometry, material)
    sphere.position.set(kp.x3d / 10, -kp.y3d / 10, kp.z3d / 10)
    scene.add(sphere)
  }

  if (showSpineCurve.value) {
    const spinePoints = SPINE_CHAIN.map((name) =>
      props.keypointsJson.find((kp) => kp.name === name && kp.x3d != null)
    ).filter(Boolean)
    if (spinePoints.length > 1) {
      const curvePoints = spinePoints.map(
        (kp) => new THREE.Vector3(kp.x3d / 10, -kp.y3d / 10, kp.z3d / 10)
      )
      const geometry = new THREE.BufferGeometry().setFromPoints(curvePoints)
      const material = new THREE.LineBasicMaterial({ color: 0xe8d600 })
      scene.add(new THREE.Line(geometry, material))
    }
  }

  const animate = () => {
    animationId = requestAnimationFrame(animate)
    controls?.update()
    renderer.render(scene, camera)
  }
  animate()
}

function setCameraPreset(view) {
  if (!camera) return
  const presets = {
    front: { x: 0, y: 0, z: 80 },
    side: { x: 80, y: 0, z: 0 },
    back: { x: 0, y: 0, z: -80 },
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
      const controls = document.createElement('script')
      controls.src =
        'https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js'
      controls.onload = resolve
      document.head.appendChild(controls)
    }
    document.head.appendChild(three)
  })
}

watch([() => props.keypointsJson, currentView, showSpineCurve], async () => {
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
    <div
      ref="containerRef"
      class="w-full h-[400px] relative"
    >
      <div
        v-if="!keypointsJson?.length"
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
