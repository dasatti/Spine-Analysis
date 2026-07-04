<script setup>
import { onMounted, ref, watch } from 'vue'
import { RouterLink } from 'vue-router'
import AppLayout from '../components/AppLayout.vue'
import RiskLevelBadge from '../components/RiskLevelBadge.vue'
import { deleteScan, listScans } from '../api/client'

const loading = ref(true)
const reports = ref([])
const search = ref('')
const deletingId = ref(null)
const error = ref('')

async function loadReports() {
  loading.value = true
  try {
    const params = { status: 'completed', page_size: 50 }
    if (search.value) params.search = search.value
    const { data } = await listScans(params)
    reports.value = data.items
  } finally {
    loading.value = false
  }
}

async function removeReport(report) {
  const confirmed = window.confirm(
    `Delete report ${report.id.slice(0, 8).toUpperCase()} for ${report.patient_name}? This cannot be undone.`
  )
  if (!confirmed) return
  error.value = ''
  deletingId.value = report.id
  try {
    await deleteScan(report.id)
    reports.value = reports.value.filter((item) => item.id !== report.id)
  } catch (e) {
    error.value = e.response?.data?.message || 'Failed to delete report.'
  } finally {
    deletingId.value = null
  }
}

function formatDate(iso) {
  if (!iso) return '—'
  return new Date(iso).toLocaleDateString('en-GB', {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
  })
}

watch(search, loadReports)
onMounted(loadReports)
</script>

<template>
  <AppLayout title="Reports Library" subtitle="Completed scan reports">
    <div class="p-gutter lg:px-margin-desktop">
      <div class="mb-stack-lg flex items-center gap-4">
        <div class="relative flex-1 max-w-md">
          <span
            class="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-on-surface-variant text-sm"
            >search</span
          >
          <input
            v-model="search"
            class="w-full bg-surface-container-lowest border border-outline-variant pl-10 pr-4 py-2 font-body-sm text-on-surface focus:border-primary outline-none"
            placeholder="Search reports..."
            type="text"
          />
        </div>
      </div>

      <p v-if="error" class="text-error text-sm mb-4">{{ error }}</p>
      <div v-if="loading" class="text-on-surface-variant py-12 text-center">
        Loading reports...
      </div>
      <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-gutter">
        <div
          v-for="report in reports"
          :key="report.id"
          class="clinical-card p-panel-padding border border-outline-variant bg-[#1A1A1A] hover:border-outline transition-colors"
        >
          <div class="flex justify-between items-start mb-4">
            <span class="font-metric-sm text-primary">{{ report.id.slice(0, 8).toUpperCase() }}</span>
            <RiskLevelBadge v-if="report.overall_risk" :level="report.overall_risk" />
          </div>
          <h3 class="font-headline-md text-headline-md mb-1">{{ report.patient_name }}</h3>
          <p class="text-on-surface-variant text-sm mb-4">{{ formatDate(report.completed_at || report.created_at) }}</p>
          <p class="font-label-caps text-[10px] text-on-surface-variant mb-4">
            {{ report.detector_model }}
          </p>
          <div class="flex gap-2">
            <RouterLink
              :to="`/scans/${report.id}`"
              class="flex-1 text-center py-2 border border-outline-variant font-label-caps text-[10px] hover:border-primary transition-colors"
            >
              VIEW RESULTS
            </RouterLink>
            <RouterLink
              :to="`/scans/${report.id}/export`"
              class="flex-1 text-center py-2 bg-primary-container text-on-primary-container font-label-caps text-[10px] font-bold hover:opacity-90"
            >
              EXPORT
            </RouterLink>
            <button
              class="px-3 py-2 border border-outline-variant text-on-surface-variant hover:text-error hover:border-error transition-colors disabled:opacity-40 flex items-center justify-center"
              type="button"
              title="Delete report"
              :disabled="deletingId === report.id"
              @click="removeReport(report)"
            >
              <span class="material-symbols-outlined text-[16px]">
                {{ deletingId === report.id ? 'hourglass_empty' : 'delete' }}
              </span>
            </button>
          </div>
        </div>
      </div>
      <p v-if="!loading && !reports.length" class="text-on-surface-variant text-center py-12">
        No completed reports yet.
      </p>
    </div>
  </AppLayout>
</template>

<style scoped>
.clinical-card {
  border: 1px solid #2a2a2a;
  background-color: #1a1a1a;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}
.clinical-card:hover {
  border-color: #4a4732;
  background-color: #20201f;
}
</style>
