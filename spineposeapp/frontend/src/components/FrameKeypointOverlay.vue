<script setup>
import { computed, ref, watch } from 'vue'

const props = defineProps({
  imageUrl: { type: String, default: null },
  landmarks: { type: Array, default: () => [] },
  view: { type: String, default: 'front' },
})

const imageRef = ref(null)
const imageSize = ref({ width: 1, height: 1 })
const imageLoadFailed = ref(false)

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

function onImageLoad() {
  imageLoadFailed.value = false
  if (!imageRef.value) return
  imageSize.value = {
    width: imageRef.value.naturalWidth || 1,
    height: imageRef.value.naturalHeight || 1,
  }
}

function onImageError() {
  imageLoadFailed.value = true
}

function toPercent(kp) {
  return {
    left: `${(kp.x / imageSize.value.width) * 100}%`,
    top: `${(kp.y / imageSize.value.height) * 100}%`,
  }
}

watch(() => props.imageUrl, () => {
  imageSize.value = { width: 1, height: 1 }
  imageLoadFailed.value = false
})
</script>

<template>
  <div class="relative bg-black border border-outline-variant overflow-hidden h-[560px] min-h-[560px]">
    <img
      v-if="imageUrl && !imageLoadFailed"
      ref="imageRef"
      :src="imageUrl"
      class="w-full h-full object-contain bg-black"
      @load="onImageLoad"
      @error="onImageError"
    />
    <svg
      v-if="imageUrl && !imageLoadFailed && spineLine.length > 1"
      class="absolute inset-0 w-full h-full pointer-events-none"
      viewBox="0 0 100 100"
      preserveAspectRatio="xMidYMid meet"
    >
      <polyline
        :points="spineLine.map((kp) => `${(kp.x / imageSize.width) * 100},${(kp.y / imageSize.height) * 100}`).join(' ')"
        fill="none"
        stroke="#E8D600"
        stroke-width="0.4"
      />
    </svg>
    <div
      v-for="(kp, i) in viewLandmarks"
      :key="`${kp.name}-${i}`"
      class="absolute w-3 h-3 -ml-1.5 -mt-1.5 rounded-full bg-primary border-2 border-black pointer-events-none"
      :style="toPercent(kp)"
      :title="kp.name"
    />
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
