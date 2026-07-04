<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'

const props = defineProps({
  imageUrl: { type: String, default: null },
  landmarks: { type: Array, default: () => [] },
  view: { type: String, default: 'front' },
})

const containerRef = ref(null)
const imageRef = ref(null)
const naturalSize = ref({ width: 0, height: 0 })
const containerSize = ref({ width: 0, height: 0 })
const imageLoadFailed = ref(false)

let resizeObserver = null

onMounted(() => {
  resizeObserver = new ResizeObserver((entries) => {
    for (const entry of entries) {
      containerSize.value = {
        width: entry.contentRect.width,
        height: entry.contentRect.height,
      }
    }
  })
  if (containerRef.value) resizeObserver.observe(containerRef.value)
})

onBeforeUnmount(() => {
  if (resizeObserver) resizeObserver.disconnect()
})

const viewLandmarks = computed(() =>
  (props.landmarks || []).filter(
    (kp) => (kp.source_view || kp.view) === props.view && kp.confidence >= 0.3
  )
)

const spineLine = computed(() => {
  const names = [
    'spine_c7', 'spine_t1', 'spine_t4', 'spine_t7',
    'spine_t10', 'spine_l1', 'spine_l3', 'spine_l5', 'spine_s1',
  ]
  return names
    .map((name) => viewLandmarks.value.find((kp) => kp.name === name))
    .filter(Boolean)
})

// Geometry of the letterboxed (object-contain) image inside the container.
const imageRect = computed(() => {
  const nw = naturalSize.value.width
  const nh = naturalSize.value.height
  const cw = containerSize.value.width
  const ch = containerSize.value.height
  if (!nw || !nh || !cw || !ch) return null
  const scale = Math.min(cw / nw, ch / nh)
  return {
    scale,
    offsetX: (cw - nw * scale) / 2,
    offsetY: (ch - nh * scale) / 2,
    width: nw * scale,
    height: nh * scale,
  }
})

const overlayReady = computed(() => imageRect.value !== null && !imageLoadFailed.value)

function onImageLoad() {
  imageLoadFailed.value = false
  if (!imageRef.value) return
  naturalSize.value = {
    width: imageRef.value.naturalWidth || 0,
    height: imageRef.value.naturalHeight || 0,
  }
}

function onImageError() {
  imageLoadFailed.value = true
}

function toPixelStyle(kp) {
  const rect = imageRect.value
  if (!rect) return { display: 'none' }
  return {
    left: `${rect.offsetX + kp.x * rect.scale}px`,
    top: `${rect.offsetY + kp.y * rect.scale}px`,
  }
}

const svgStyle = computed(() => {
  const rect = imageRect.value
  if (!rect) return { display: 'none' }
  return {
    left: `${rect.offsetX}px`,
    top: `${rect.offsetY}px`,
    width: `${rect.width}px`,
    height: `${rect.height}px`,
  }
})

const spineStrokeWidth = computed(() =>
  Math.max(2, naturalSize.value.width / 300)
)

watch(() => props.imageUrl, () => {
  naturalSize.value = { width: 0, height: 0 }
  imageLoadFailed.value = false
})
</script>

<template>
  <div
    ref="containerRef"
    class="relative bg-black border border-outline-variant overflow-hidden h-[560px] min-h-[560px]"
  >
    <img
      v-if="imageUrl && !imageLoadFailed"
      ref="imageRef"
      :src="imageUrl"
      class="w-full h-full object-contain bg-black"
      @load="onImageLoad"
      @error="onImageError"
    />
    <svg
      v-if="imageUrl && overlayReady && spineLine.length > 1"
      class="absolute pointer-events-none"
      :style="svgStyle"
      :viewBox="`0 0 ${naturalSize.width} ${naturalSize.height}`"
      preserveAspectRatio="none"
    >
      <polyline
        :points="spineLine.map((kp) => `${kp.x},${kp.y}`).join(' ')"
        fill="none"
        stroke="#E8D600"
        :stroke-width="spineStrokeWidth"
      />
    </svg>
    <template v-if="imageUrl && overlayReady">
      <div
        v-for="(kp, i) in viewLandmarks"
        :key="`${kp.name}-${i}`"
        class="absolute w-3 h-3 -ml-1.5 -mt-1.5 rounded-full bg-primary border-2 border-black pointer-events-none"
        :style="toPixelStyle(kp)"
        :title="kp.name"
      />
    </template>
    <div
      v-if="!imageUrl || imageLoadFailed"
      class="absolute inset-0 flex items-center justify-center text-on-surface-variant text-sm px-6 text-center"
    >
      {{ imageLoadFailed ? 'Frame image could not be loaded' : 'Frame not available' }}
    </div>
    <div
      v-else-if="!viewLandmarks.length"
      class="absolute bottom-2 left-2 text-[10px] font-label-caps bg-black/70 text-on-surface-variant px-2 py-1"
    >
      No keypoints detected for this view
    </div>
  </div>
</template>
