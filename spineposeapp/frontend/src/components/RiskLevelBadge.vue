<script setup>
defineProps({
  level: {
    type: String,
    required: true,
    validator: (v) => ['normal', 'monitor', 'elevated'].includes(v),
  },
})

const labels = { normal: 'Normal', monitor: 'Monitor', elevated: 'Elevated' }
const styles = {
  normal: 'bg-status-green/20 text-status-green border-status-green/30',
  monitor: 'bg-status-amber/20 text-status-amber border-status-amber/30',
  elevated: 'bg-status-red/20 text-status-red border-status-red/30',
}
</script>

<template>
  <span
    :class="[
      'inline-flex px-3 py-1 font-label-caps text-[10px] rounded-sm border',
      styles[level],
    ]"
  >
    {{ labels[level] }}
  </span>
</template>
