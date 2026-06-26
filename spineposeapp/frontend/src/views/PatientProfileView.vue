<script setup>
import { computed, onMounted, ref } from 'vue'
import { RouterLink, useRoute } from 'vue-router'
import AppLayout from '../components/AppLayout.vue'
import RiskLevelBadge from '../components/RiskLevelBadge.vue'
import ScanStatusBadge from '../components/ScanStatusBadge.vue'
import { usePatientsStore } from '../stores/patients'

const route = useRoute()
const patientsStore = usePatientsStore()
const activeTab = ref('overview')

const patient = computed(() => patientsStore.current)

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

onMounted(() => patientsStore.fetchOne(route.params.id))
</script>

<template>
  <AppLayout title="Patient Profile">
    <div v-if="patientsStore.loading" class="p-margin-desktop text-on-surface-variant">
      Loading patient profile...
    </div>
    <template v-else-if="patient">
      <div class="p-gutter lg:px-margin-desktop">
        <section class="mb-stack-lg">
          <div class="flex items-start justify-between flex-wrap gap-4">
            <div>
              <div class="flex items-center mb-1">
                <div class="spine-bar"></div>
                <h2
                  class="font-headline-lg text-headline-lg text-on-background uppercase tracking-tight"
                >
                  {{ patient.first_name }} {{ patient.last_name }}
                </h2>
              </div>
              <p
                class="font-metric-sm text-metric-sm text-on-surface-variant ml-4 uppercase tracking-widest"
              >
                ID: {{ patient.medical_record_number || patient.id.slice(0, 8).toUpperCase() }}
              </p>
            </div>
            <div class="flex gap-2 flex-wrap">
              <span
                class="px-3 py-1 bg-surface-container-high border border-outline-variant font-label-caps text-[10px] text-on-surface-variant"
                >AGE: {{ calcAge(patient.date_of_birth) }}</span
              >
              <span
                class="px-3 py-1 bg-surface-container-high border border-outline-variant font-label-caps text-[10px] text-on-surface-variant uppercase"
                >{{ patient.gender }}</span
              >
              <span
                class="px-3 py-1 bg-surface-container-high border border-outline-variant font-label-caps text-[10px] text-on-surface-variant"
                >{{ patient.height_cm }}CM / {{ patient.weight_kg }}KG</span
              >
              <span
                class="px-3 py-1 bg-surface-container-high border border-outline-variant font-label-caps text-[10px] text-on-surface-variant"
                >ADDED: {{ formatDate(patient.created_at) }}</span
              >
            </div>
          </div>
          <div
            class="mt-8 border-b border-outline-variant flex gap-8 overflow-x-auto"
          >
            <button
              v-for="tab in ['overview', 'scans', 'notes']"
              :key="tab"
              :class="[
                'pb-4 font-label-caps text-label-caps uppercase transition-colors',
                activeTab === tab
                  ? 'text-primary border-b-2 border-primary'
                  : 'text-on-surface-variant hover:text-on-surface',
              ]"
              @click="activeTab = tab"
            >
              {{ tab === 'scans' ? 'SCAN HISTORY' : tab }}
            </button>
          </div>
        </section>

        <section v-if="activeTab === 'overview'" class="grid grid-cols-12 gap-gutter">
          <div class="col-span-12 lg:col-span-4 space-y-gutter">
            <div class="bg-surface-container-low border border-outline-variant p-panel-padding">
              <h3 class="font-label-caps text-label-caps text-on-surface-variant mb-6">
                RISK ASSESSMENT
              </h3>
              <RiskLevelBadge :level="patient.risk_level" />
              <p class="text-on-surface-variant text-sm mt-4">
                {{ patient.scan_count }} total scans · Last:
                {{ formatDate(patient.last_scan_at) }}
              </p>
            </div>
            <div class="bg-surface-container-low border border-outline-variant p-panel-padding">
              <h3 class="font-label-caps text-label-caps text-on-surface-variant mb-4">
                CONTACT
              </h3>
              <p class="text-on-surface text-sm">{{ patient.phone || '—' }}</p>
              <p class="text-on-surface-variant text-sm mt-2">{{ patient.email || '—' }}</p>
            </div>
          </div>
          <div class="col-span-12 lg:col-span-8 space-y-gutter">
            <div class="bg-surface-container-low border border-outline-variant p-panel-padding">
              <h3 class="font-label-caps text-label-caps text-on-surface-variant mb-4">
                CLINICAL SUMMARY
              </h3>
              <p class="text-on-surface">
                {{ patient.primary_diagnosis || 'No primary diagnosis recorded.' }}
              </p>
              <p v-if="patient.medical_notes" class="text-on-surface-variant text-sm mt-4">
                {{ patient.medical_notes }}
              </p>
            </div>
            <div class="flex gap-4">
              <RouterLink
                :to="`/scans/new?patient_id=${patient.id}`"
                class="bg-primary-container text-on-primary-container px-6 py-3 font-bold font-label-caps hover:opacity-90"
              >
                START NEW SCAN
              </RouterLink>
              <RouterLink
                :to="`/patients/${patient.id}/edit`"
                class="border border-outline-variant px-6 py-3 font-label-caps text-on-surface hover:bg-surface-container-high"
              >
                EDIT PATIENT
              </RouterLink>
            </div>
          </div>
        </section>

        <section v-else-if="activeTab === 'scans'" class="border border-outline-variant">
          <table class="w-full">
            <thead class="bg-surface-container-high border-b border-outline-variant">
              <tr>
                <th class="p-4 font-label-caps text-[11px] text-on-surface-variant text-left">
                  DATE
                </th>
                <th class="p-4 font-label-caps text-[11px] text-on-surface-variant text-left">
                  STATUS
                </th>
                <th class="p-4 font-label-caps text-[11px] text-on-surface-variant text-left">
                  MODEL
                </th>
                <th class="p-4 font-label-caps text-[11px] text-on-surface-variant text-left">
                  RISK
                </th>
                <th class="p-4"></th>
              </tr>
            </thead>
            <tbody class="divide-y divide-outline-variant">
              <tr
                v-for="scan in patient.recent_scans"
                :key="scan.id"
                class="hover:bg-surface-container-high"
              >
                <td class="p-4 font-metric-sm">{{ formatDate(scan.created_at) }}</td>
                <td class="p-4"><ScanStatusBadge :status="scan.status" /></td>
                <td class="p-4 text-on-surface-variant text-sm">{{ scan.detector_model }}</td>
                <td class="p-4">
                  <RiskLevelBadge v-if="scan.overall_risk" :level="scan.overall_risk" />
                  <span v-else class="text-on-surface-variant">—</span>
                </td>
                <td class="p-4 text-right">
                  <RouterLink
                    :to="`/scans/${scan.id}`"
                    class="text-primary font-label-caps text-[10px] hover:underline"
                    >VIEW</RouterLink
                  >
                </td>
              </tr>
            </tbody>
          </table>
        </section>

        <section v-else class="bg-surface-container-low border border-outline-variant p-panel-padding">
          <h3 class="font-label-caps text-label-caps text-on-surface-variant mb-4">NOTES</h3>
          <p class="text-on-surface-variant whitespace-pre-wrap">
            {{ patient.medical_notes || 'No clinical notes on file.' }}
          </p>
        </section>
      </div>
    </template>
  </AppLayout>
</template>

<style scoped>
.border-default {
  border: 1px solid #353535;
}
</style>
