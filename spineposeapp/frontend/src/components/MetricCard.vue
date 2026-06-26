<script setup>
import { computed } from 'vue'
import RangeBar from './RangeBar.vue'

const AVAILABILITY_MESSAGES = {
  unavailable_no_landmark: 'Landmark not detected',
  unavailable_low_confidence: 'Low keypoint confidence',
  unavailable_no_face_data: 'No face capture',
  unavailable_no_depth: 'Insufficient depth data',
  unavailable_no_sensor: 'Requires pressure sensor',
}

const props = defineProps({
  name: { type: String, required: true },
  value: { type: [Number, Boolean, null], default: null },
  unit: { type: String, default: '' },
  normalMin: { type: Number, required: true },
  normalMax: { type: Number, required: true },
  availability: { type: String, default: 'available' },
  sourceView: { type: String, default: '' },
  group: { type: String, default: '' },
})

const viewLabels = {
  front: 'Front View',
  side: 'Side View',
  back: 'Back View',
  adams: 'Adams View',
  face: 'Face View',
}

const isAvailable = computed(() => props.availability === 'available')
const displayValue = computed(() => {
  if (!isAvailable.value) return '—'
  if (typeof props.value === 'boolean') return props.value ? 'Present' : 'Absent'
  return props.value
})
const outOfRange = computed(() => {
  if (!isAvailable.value || typeof props.value !== 'number') return false
  return props.value < props.normalMin || props.value > props.normalMax
})
const reason = computed(() => AVAILABILITY_MESSAGES[props.availability] || '')
</script>

<template>
  <div class="bg-[#1A1A1A] border border-outline-variant p-4">
    <div class="flex items-start justify-between mb-3">
      <div>
        <p class="font-label-caps text-[10px] text-on-surface-variant">{{ name }}</p>
        <p
          :class="[
            'font-metric-lg text-metric-lg mt-1',
            outOfRange ? 'text-[#E8D600]' : 'text-white',
          ]"
        >
          {{ displayValue }}<span v-if="isAvailable && unit" class="text-sm ml-1">{{ unit }}</span>
        </p>
        <p v-if="!isAvailable" class="text-on-surface-variant text-xs mt-1">— {{ reason }}</p>
      </div>
      <span
        v-if="sourceView"
        class="text-[10px] font-label-caps text-on-surface-variant/60 px-2 py-1 bg-[#2A2A2A]"
      >
        {{ viewLabels[sourceView] || sourceView }}
      </span>
    </div>
    <RangeBar
      v-if="isAvailable && typeof value === 'number'"
      :value="value"
      :min="normalMin - (normalMax - normalMin)"
      :max="normalMax + (normalMax - normalMin)"
      :normal-min="normalMin"
      :normal-max="normalMax"
    />
  </div>
</template>
