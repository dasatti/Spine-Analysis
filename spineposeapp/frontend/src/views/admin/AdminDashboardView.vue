<script setup>
import { computed, onMounted, ref } from 'vue'
import { RouterLink } from 'vue-router'
import AdminLayout from './AdminLayout.vue'
import { getAdminAnalytics } from '../../api/client'

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

onMounted(async () => {
  try {
    const { data } = await getAdminAnalytics()
    summary.value = data
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <AdminLayout title="Admin Dashboard" :subtitle="todayLabel">
    <div v-if="loading" class="p-margin-desktop text-on-surface-variant">Loading analytics...</div>
    <div v-else class="p-margin-desktop space-y-stack-lg">
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-gutter">
        <div
          class="bg-surface-container border border-outline-variant p-panel-padding hover:border-outline transition-colors group"
        >
          <p class="font-label-caps text-on-surface-variant mb-2">TOTAL DOCTORS</p>
          <span
            class="font-metric-lg text-4xl text-on-surface group-hover:text-primary transition-colors"
            >{{ summary?.total_doctors ?? 0 }}</span
          >
          <p class="font-body-sm text-on-surface-variant mt-2">
            {{ summary?.active_doctors ?? 0 }} active
          </p>
        </div>
        <div
          class="bg-surface-container border border-outline-variant p-panel-padding hover:border-outline transition-colors group"
        >
          <p class="font-label-caps text-on-surface-variant mb-2">TOTAL PATIENTS</p>
          <span
            class="font-metric-lg text-4xl text-on-surface group-hover:text-primary transition-colors"
            >{{ summary?.total_patients ?? 0 }}</span
          >
        </div>
        <div
          class="bg-surface-container border border-outline-variant p-panel-padding hover:border-outline transition-colors group"
        >
          <p class="font-label-caps text-on-surface-variant mb-2">SCANS TODAY</p>
          <span
            class="font-metric-lg text-4xl text-on-surface group-hover:text-primary transition-colors"
            >{{ summary?.scans_today ?? 0 }}</span
          >
        </div>
        <div
          class="bg-surface-container border border-outline-variant p-panel-padding hover:border-outline transition-colors group"
        >
          <p class="font-label-caps text-on-surface-variant mb-2">PENDING REPORTS</p>
          <span
            class="font-metric-lg text-4xl text-on-surface group-hover:text-primary transition-colors"
            >{{ String(summary?.pending_reports ?? 0).padStart(2, '0') }}</span
          >
        </div>
      </div>

      <div class="grid grid-cols-1 lg:grid-cols-2 gap-gutter">
        <div class="bg-surface-container border border-outline-variant p-panel-padding">
          <div class="flex items-center justify-between mb-6">
            <h2 class="font-headline-sm text-headline-sm font-bold text-on-surface">
              Recent Activity
            </h2>
          </div>
          <div v-if="!summary?.recent_activity?.length" class="text-on-surface-variant text-sm">
            No recent activity.
          </div>
          <ul v-else class="space-y-4">
            <li
              v-for="(item, idx) in summary.recent_activity"
              :key="idx"
              class="flex items-start gap-3 pb-4 border-b border-outline-variant last:border-0 last:pb-0"
            >
              <span class="material-symbols-outlined text-primary text-[20px] mt-0.5"
                >biotech</span
              >
              <div class="flex-1 min-w-0">
                <p class="text-on-surface text-sm">
                  Scan completed for
                  <span class="font-bold">{{ item.patient_name }}</span>
                  by {{ item.doctor_name }}
                </p>
                <p class="font-metric-sm text-xs text-on-surface-variant mt-1">
                  {{ formatActivityTime(item.timestamp) }}
                </p>
              </div>
            </li>
          </ul>
        </div>

        <div class="bg-surface-container border border-outline-variant p-panel-padding">
          <div class="flex items-center justify-between mb-6">
            <h2 class="font-headline-sm text-headline-sm font-bold text-on-surface">
              Recently Registered Doctors
            </h2>
            <RouterLink
              to="/admin/doctors"
              class="font-label-caps text-primary text-xs hover:underline"
              >View all</RouterLink
            >
          </div>
          <div v-if="!summary?.recent_doctors?.length" class="text-on-surface-variant text-sm">
            No doctors registered yet.
          </div>
          <ul v-else class="space-y-3">
            <li
              v-for="doctor in summary.recent_doctors"
              :key="doctor.id"
              class="flex items-center justify-between py-3 border-b border-outline-variant last:border-0"
            >
              <div>
                <p class="font-body-sm text-sm font-bold text-on-surface">
                  Dr. {{ doctor.first_name }} {{ doctor.last_name }}
                </p>
                <p class="font-metric-sm text-xs text-on-surface-variant">{{ doctor.email }}</p>
              </div>
              <span class="font-label-caps text-xs text-on-surface-variant">
                {{ doctor.patient_count }} patients
              </span>
            </li>
          </ul>
        </div>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-2 gap-gutter">
        <div class="bg-surface-container border border-outline-variant p-panel-padding">
          <p class="font-label-caps text-on-surface-variant mb-2">TOTAL SCANS</p>
          <span class="font-metric-lg text-3xl text-on-surface">{{
            summary?.total_scans ?? 0
          }}</span>
        </div>
        <div class="bg-surface-container border border-outline-variant p-panel-padding">
          <p class="font-label-caps text-on-surface-variant mb-2">SESSIONS THIS MONTH</p>
          <span class="font-metric-lg text-3xl text-on-surface">{{
            summary?.sessions_this_month ?? 0
          }}</span>
        </div>
      </div>
    </div>
  </AdminLayout>
</template>
