<script setup>
import { computed, onMounted, ref } from 'vue'
import { RouterLink } from 'vue-router'
import AppLayout from '../components/AppLayout.vue'
import PatientRow from '../components/PatientRow.vue'
import { getDashboardSummary } from '../api/client'

const loading = ref(true)
const summary = ref(null)

const todayLabel = computed(() =>
  new Date().toLocaleDateString('en-US', {
    weekday: 'long',
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  })
)

function formatActivityTime(iso) {
  if (!iso) return ''
  return new Date(iso).toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' })
}

function activityMessage(item) {
  const map = {
    scan_completed: `Scan completed for`,
    patient_registered: `New patient registered:`,
    scan_started: `Scan session started for`,
    report_approved: `Report approved for`,
  }
  return map[item.type] || item.type?.replace(/_/g, ' ')
}

onMounted(async () => {
  try {
    const { data } = await getDashboardSummary()
    summary.value = data
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <AppLayout title="Dashboard" :subtitle="todayLabel">
    <div v-if="loading" class="p-margin-desktop text-on-surface-variant">Loading dashboard...</div>
    <div v-else class="p-margin-desktop space-y-stack-lg">
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-gutter">
        <div
          class="bg-surface-container border border-outline-variant p-panel-padding hover:border-outline transition-colors group"
        >
          <p class="font-label-caps text-on-surface-variant mb-2">TOTAL PATIENTS</p>
          <div class="flex items-end justify-between">
            <span
              class="font-metric-lg text-4xl text-on-surface group-hover:text-primary transition-colors"
              >{{ summary?.total_patients ?? 0 }}</span
            >
          </div>
        </div>
        <div
          class="bg-surface-container border border-outline-variant p-panel-padding hover:border-outline transition-colors group"
        >
          <p class="font-label-caps text-on-surface-variant mb-2">SCANS TODAY</p>
          <div class="flex items-end justify-between">
            <span
              class="font-metric-lg text-4xl text-on-surface group-hover:text-primary transition-colors"
              >{{ summary?.scans_today ?? 0 }}</span
            >
            <span class="font-metric-sm text-xs text-on-surface-variant mb-1">Target: 50</span>
          </div>
        </div>
        <div
          class="bg-surface-container border border-outline-variant p-panel-padding hover:border-outline transition-colors group relative overflow-hidden"
        >
          <p class="font-label-caps text-on-surface-variant mb-2">PENDING REPORTS</p>
          <div class="flex items-end justify-between">
            <span
              class="font-metric-lg text-4xl text-on-surface group-hover:text-primary transition-colors"
              >{{ String(summary?.pending_reports ?? 0).padStart(2, '0') }}</span
            >
            <span
              v-if="(summary?.pending_reports ?? 0) > 0"
              class="bg-[#E8D600]/20 text-[#E8D600] px-2 py-0.5 rounded text-[10px] font-bold font-label-caps border border-[#E8D600]/30"
              >URGENT</span
            >
          </div>
        </div>
        <div
          class="bg-surface-container border border-outline-variant p-panel-padding hover:border-outline transition-colors group"
        >
          <p class="font-label-caps text-on-surface-variant mb-2">SESSIONS THIS MONTH</p>
          <div class="flex items-end justify-between">
            <span
              class="font-metric-lg text-4xl text-on-surface group-hover:text-primary transition-colors"
              >{{ summary?.sessions_this_month ?? 0 }}</span
            >
          </div>
        </div>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-2 gap-gutter">
        <RouterLink
          to="/patients/new"
          class="bg-surface-container border-2 border-primary-container p-6 flex items-center justify-between group hover:bg-primary-container/5 transition-all"
        >
          <div class="text-left">
            <h3 class="font-headline-md text-primary-container uppercase tracking-tight">
              Add New Patient
            </h3>
            <p class="text-on-surface-variant text-sm mt-1">
              Register new clinical record and history
            </p>
          </div>
          <span
            class="material-symbols-outlined text-4xl text-primary-container group-hover:translate-x-1 transition-transform"
            >person_add</span
          >
        </RouterLink>
        <RouterLink
          to="/scans/new"
          class="bg-primary-container p-6 flex items-center justify-between group hover:opacity-90 transition-all"
        >
          <div class="text-left">
            <h3 class="font-headline-md text-on-primary uppercase tracking-tight">Start New Scan</h3>
            <p class="text-on-primary/70 text-sm mt-1">
              Initialize real-time biometric spine analysis
            </p>
          </div>
          <span
            class="material-symbols-outlined text-4xl text-on-primary group-hover:scale-110 transition-transform"
            >biotech</span
          >
        </RouterLink>
      </div>

      <div class="grid grid-cols-12 gap-gutter">
        <section
          class="col-span-12 lg:col-span-4 bg-surface-container border border-outline-variant flex flex-col"
        >
          <div
            class="p-6 border-b border-outline-variant bg-surface-container-high flex justify-between items-center"
          >
            <h3 class="font-label-caps text-on-surface">RECENT ACTIVITY</h3>
            <RouterLink
              to="/scans"
              class="text-[10px] font-label-caps text-primary hover:underline"
              >VIEW ALL</RouterLink
            >
          </div>
          <div class="p-6 flex-1 overflow-y-auto max-h-[500px] custom-scrollbar">
            <div
              class="space-y-6 relative before:absolute before:left-[7px] before:top-2 before:bottom-2 before:w-[1px] before:bg-outline-variant"
            >
              <div
                v-for="(item, i) in summary?.recent_activity ?? []"
                :key="i"
                class="relative pl-6 group"
              >
                <div
                  class="absolute left-0 top-1.5 w-3.5 h-3.5 rounded-full bg-[#E8D600] border-4 border-surface-container z-10"
                ></div>
                <p class="text-sm text-on-surface-variant font-body-sm">
                  {{ activityMessage(item) }}
                  <span v-if="item.patient_name" class="text-on-surface font-bold">{{
                    item.patient_name
                  }}</span>
                </p>
                <p
                  class="text-[11px] font-metric-sm text-on-surface-variant opacity-50 mt-1"
                >
                  {{ formatActivityTime(item.timestamp) }}
                </p>
              </div>
              <p
                v-if="!(summary?.recent_activity?.length)"
                class="text-on-surface-variant text-sm"
              >
                No recent activity
              </p>
            </div>
          </div>
        </section>

        <section
          class="col-span-12 lg:col-span-8 bg-surface-container border border-outline-variant overflow-hidden flex flex-col"
        >
          <div
            class="p-6 border-b border-outline-variant bg-surface-container-high flex justify-between items-center"
          >
            <h3 class="font-label-caps text-on-surface">RECENT PATIENTS</h3>
            <RouterLink to="/patients" class="text-[10px] font-label-caps text-primary hover:underline"
              >VIEW ALL</RouterLink
            >
          </div>
          <div class="overflow-x-auto flex-1">
            <table class="w-full text-left border-collapse">
              <thead>
                <tr class="bg-surface-container-low border-b border-outline-variant">
                  <th class="p-4 font-label-caps text-[11px] text-on-surface-variant">PATIENT</th>
                  <th class="p-4 font-label-caps text-[11px] text-on-surface-variant">AGE</th>
                  <th class="p-4 font-label-caps text-[11px] text-on-surface-variant">LAST SCAN</th>
                  <th class="p-4 font-label-caps text-[11px] text-on-surface-variant">
                    RISK LEVEL
                  </th>
                  <th class="p-4"></th>
                </tr>
              </thead>
              <tbody class="divide-y divide-outline-variant/30">
                <PatientRow
                  v-for="patient in summary?.recent_patients ?? []"
                  :key="patient.id"
                  :patient="patient"
                  compact
                />
              </tbody>
            </table>
          </div>
        </section>
      </div>
    </div>
  </AppLayout>
</template>
