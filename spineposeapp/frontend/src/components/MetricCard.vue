<script setup>
import { computed } from 'vue'
import ClassificationBar from './ClassificationBar.vue'
import RangeBar from './RangeBar.vue'

const AVAILABILITY_MESSAGES = {
  unavailable_no_landmark: 'Landmark not detected',
  unavailable_low_confidence: 'Low keypoint confidence',
  unavailable_no_face_data: 'No face capture',
  unavailable_no_depth: 'Insufficient depth data',
  unavailable_no_sensor: 'Requires pressure sensor',
  unavailable_no_side_frame: 'No side view frame',
  unavailable_no_back_frame: 'No back view frame',
  unavailable_no_scoliosis_views: 'No back or Adams view',
}

const props = defineProps({
  name: { type: String, required: true },
  value: { type: [Number, Boolean, String, null], default: null },
  unit: { type: String, default: '' },
  normalMin: { type: Number, default: 0 },
  normalMax: { type: Number, default: 100 },
  availability: { type: String, default: 'available' },
  sourceView: { type: String, default: '' },
  group: { type: String, default: '' },
  compact: { type: Boolean, default: false },
  metricType: { type: String, default: 'numeric' },
  confidence: { type: Number, default: null },
  lateralIndex: { type: Number, default: null },
  keypointCount: { type: Number, default: null },
})

const viewLabels = {
  front: 'Front View',
  side: 'Side View',
  back: 'Back View',
  adams: 'Adams View',
  face: 'Face View',
  upper_body: 'Upper Body (Side View)',
}

const POSITIVE_CLASS_LABELS = new Set(['kyphosis', 'lordosis', 'scoliosis'])

const isClassification = computed(() => props.metricType === 'classification')
const isAvailable = computed(() => props.availability === 'available')
const classLabel = computed(() => String(props.value || '').toLowerCase())
const isPositiveClassification = computed(
  () => isClassification.value && POSITIVE_CLASS_LABELS.has(classLabel.value)
)
const displayValue = computed(() => {
  if (!isAvailable.value) return '—'
  if (isClassification.value) {
    if (classLabel.value === 'kyphosis') return 'Kyphosis'
    if (classLabel.value === 'lordosis') return 'Lordosis'
    if (classLabel.value === 'scoliosis') return 'Scoliosis'
    if (classLabel.value === 'normal') return 'Normal'
    return props.value
  }
  if (typeof props.value === 'boolean') return props.value ? 'Present' : 'Absent'
  return props.value
})
const displayConfidence = computed(() => {
  if (!isAvailable.value || props.confidence == null) return null
  return `${Math.round(props.confidence * 100)}%`
})
const outOfRange = computed(() => {
  if (!isAvailable.value || typeof props.value !== 'number') return false
  return props.value < props.normalMin || props.value > props.normalMax
})
const reason = computed(() => AVAILABILITY_MESSAGES[props.availability] || '')
</script>

<template>
  <div
    :class="[
      'bg-[#1A1A1A] border border-outline-variant',
      compact ? 'p-2 min-w-0' : 'p-4',
    ]"
  >
    <div :class="['flex items-start justify-between', compact ? 'mb-1.5 gap-1' : 'mb-3']">
      <div class="min-w-0 flex-1">
        <p
          :class="[
            'font-label-caps text-on-surface-variant truncate',
            compact ? 'text-[9px] leading-tight' : 'text-[10px]',
          ]"
          :title="name"
        >
          {{ name }}
        </p>
        <p
          :class="[
            'mt-0.5',
            compact ? 'text-sm font-metric-sm leading-tight' : 'font-metric-lg text-metric-lg mt-1',
            isClassification
              ? isPositiveClassification
                ? 'text-[#DC2626]'
                : 'text-[#16A34A]'
              : outOfRange
                ? 'text-[#E8D600]'
                : 'text-white',
          ]"
        >
          {{ displayValue }}<span v-if="isAvailable && unit && !isClassification" :class="compact ? 'text-[10px] ml-0.5' : 'text-sm ml-1'">{{ unit }}</span>
        </p>
        <p
          v-if="isAvailable && displayConfidence"
          :class="compact ? 'text-[10px] text-on-surface-variant mt-0.5' : 'text-on-surface-variant text-xs mt-1'"
        >
          {{ displayConfidence }} confidence
        </p>
        <p
          v-if="isAvailable && lateralIndex != null"
          :class="compact ? 'text-[10px] text-on-surface-variant/80 mt-0.5' : 'text-on-surface-variant/80 text-[10px] mt-1'"
        >
          Lateral index {{ lateralIndex.toFixed(3) }}<span v-if="keypointCount != null"> · {{ keypointCount }} keypoints</span>
        </p>
        <p v-if="!isAvailable" :class="compact ? 'text-[10px] text-on-surface-variant mt-0.5 line-clamp-2' : 'text-on-surface-variant text-xs mt-1'">
          — {{ reason }}
        </p>
      </div>
      <span
        v-if="sourceView && !compact"
        class="text-[10px] font-label-caps text-on-surface-variant/60 px-2 py-1 bg-[#2A2A2A] shrink-0"
      >
        {{ viewLabels[sourceView] || sourceView }}
      </span>
    </div>
    <ClassificationBar
      v-if="isAvailable && isClassification && confidence != null"
      :confidence="confidence"
      :positive="isPositiveClassification"
    />
    <RangeBar
      v-else-if="isAvailable && typeof value === 'number'"
      :value="value"
      :min="normalMin - (normalMax - normalMin)"
      :max="normalMax + (normalMax - normalMin)"
      :normal-min="normalMin"
      :normal-max="normalMax"
    />
  </div>
</template>
