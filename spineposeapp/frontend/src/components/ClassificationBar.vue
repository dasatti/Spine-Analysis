<script setup>
import { computed } from 'vue'

const props = defineProps({
  confidence: { type: Number, default: 0 },
  positive: { type: Boolean, default: false },
})

const width = computed(() => `${Math.round(Math.min(1, Math.max(0, props.confidence)) * 100)}%`)
const fillColor = computed(() => (props.positive ? '#DC2626' : '#16A34A'))
</script>

<template>
  <div class="relative h-1.5 bg-[#2A2A2A] rounded-full overflow-hidden">
    <div
      class="absolute top-0 left-0 h-full transition-all"
      :style="{ width, backgroundColor: fillColor }"
    />
  </div>
</template>
