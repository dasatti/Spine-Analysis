<script setup>
import { computed } from 'vue'
import { RouterLink } from 'vue-router'
import RiskLevelBadge from './RiskLevelBadge.vue'

const props = defineProps({
  patient: { type: Object, required: true },
  compact: { type: Boolean, default: false },
})

const fullName = computed(() => `${props.patient.first_name} ${props.patient.last_name}`)

function calcAge(dob) {
  if (!dob) return '—'
  const birth = new Date(dob)
  const today = new Date()
  let age = today.getFullYear() - birth.getFullYear()
  const m = today.getMonth() - birth.getMonth()
  if (m < 0 || (m === 0 && today.getDate() < birth.getDate())) age--
  return age
}

function formatDate(iso) {
  if (!iso) return '—'
  return new Date(iso).toLocaleDateString('en-GB', {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
  })
}
</script>

<template>
  <tr class="hover:bg-surface-container-high transition-colors">
    <td class="p-4">
      <div class="flex items-center gap-3">
        <div
          class="w-8 h-8 rounded bg-outline-variant overflow-hidden flex items-center justify-center text-[10px] font-bold text-on-surface-variant"
        >
          {{ patient.first_name[0] }}{{ patient.last_name[0] }}
        </div>
        <RouterLink
          :to="`/patients/${patient.id}`"
          class="font-body-sm font-bold hover:text-primary transition-colors"
        >
          {{ fullName }}
        </RouterLink>
      </div>
    </td>
    <td class="p-4 font-metric-sm">{{ calcAge(patient.date_of_birth) }}</td>
    <td v-if="!compact" class="p-4 font-metric-sm text-primary">
      {{ patient.medical_record_number || '—' }}
    </td>
    <td v-if="!compact" class="p-4 text-on-surface-variant capitalize">
      {{ calcAge(patient.date_of_birth) }} / {{ patient.gender }}
    </td>
    <td v-if="!compact" class="p-4">
      <span class="text-on-surface">{{ patient.primary_diagnosis || '—' }}</span>
    </td>
    <td class="p-4 font-metric-sm text-on-surface-variant">
      {{ formatDate(patient.last_scan_at) }}
    </td>
    <td v-if="!compact" class="p-4 text-center text-on-surface">{{ patient.scan_count ?? 0 }}</td>
    <td class="p-4">
      <RiskLevelBadge :level="patient.risk_level" />
    </td>
    <td class="p-4 text-right">
      <RouterLink
        :to="`/patients/${patient.id}`"
        class="text-on-surface-variant hover:text-primary transition-colors inline-flex p-2"
      >
        <span class="material-symbols-outlined">{{ compact ? 'more_vert' : 'monitoring' }}</span>
      </RouterLink>
    </td>
  </tr>
</template>
