<script setup>
import { computed } from 'vue'

const props = defineProps({
  value: { type: Number, default: 0 },
  min: { type: Number, required: true },
  max: { type: Number, required: true },
  normalMin: { type: Number, required: true },
  normalMax: { type: Number, required: true },
})

const position = computed(() => {
  const range = props.max - props.min || 1
  return Math.min(100, Math.max(0, ((props.value - props.min) / range) * 100))
})

const fillColor = computed(() => {
  if (props.value >= props.normalMin && props.value <= props.normalMax) return '#16A34A'
  const lowerBound = props.normalMin - (props.normalMax - props.normalMin) * 0.2
  const upperBound = props.normalMax + (props.normalMax - props.normalMin) * 0.2
  if (props.value >= lowerBound && props.value <= upperBound) return '#D97706'
  return '#DC2626'
})
</script>

<template>
  <div class="relative h-1.5 bg-[#2A2A2A] rounded-full overflow-hidden">
    <div
      class="absolute top-0 left-0 h-full transition-all"
      :style="{ width: `${position}%`, backgroundColor: fillColor }"
    />
  </div>
</template>
