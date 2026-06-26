<script setup>
defineProps({
  status: {
    type: String,
    required: true,
    validator: (v) =>
      ['pending', 'processing', 'completed', 'failed', 'partial', 'flagged'].includes(v),
  },
})

const labels = {
  pending: 'Pending',
  processing: 'Processing',
  completed: 'Complete',
  failed: 'Failed',
  partial: 'Partial',
  flagged: 'Flagged',
}

const styles = {
  pending: 'bg-white/5 text-on-surface-variant border-white/10',
  processing: 'bg-status-blue/20 text-status-blue border-status-blue/30 pulse-processing',
  completed: 'bg-status-green/20 text-status-green border-status-green/30',
  failed: 'bg-status-red/20 text-status-red border-status-red/30',
  partial: 'bg-status-amber/20 text-status-amber border-status-amber/30',
  flagged: 'bg-status-red/20 text-status-red border-status-red/30',
}
</script>

<template>
  <span
    :class="[
      'inline-flex px-3 py-1 font-label-caps text-[10px] rounded-sm border',
      styles[status],
    ]"
  >
    {{ labels[status] }}
  </span>
</template>
