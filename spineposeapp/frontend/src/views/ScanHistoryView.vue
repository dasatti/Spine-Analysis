<script setup>
import { onMounted, ref, watch } from 'vue'
import { RouterLink } from 'vue-router'
import AppLayout from '../components/AppLayout.vue'
import ScanStatusBadge from '../components/ScanStatusBadge.vue'
import { useScansStore } from '../stores/scans'

const scansStore = useScansStore()
const search = ref('')
const statusFilter = ref('')
const page = ref(1)

function formatDateTime(iso) {
  if (!iso) return '—'
  const d = new Date(iso)
  return d.toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' }) +
    ' · ' +
    d.toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' })
}

async function loadScans() {
  const params = { page: page.value, page_size: 20 }
  if (search.value) params.search = search.value
  if (statusFilter.value) params.status = statusFilter.value
  await scansStore.fetchList(params)
}

watch([search, statusFilter, page], loadScans)
onMounted(loadScans)
</script>

<template>
  <AppLayout title="Scan Sessions" subtitle="All capture sessions">
    <template #header-actions>
      <RouterLink
        to="/scans/new"
        class="bg-primary text-on-primary font-bold px-6 py-2 rounded flex items-center gap-2 hover:brightness-110 active:scale-95 transition-all"
      >
        <span class="material-symbols-outlined">add</span>
        <span>New Scan</span>
      </RouterLink>
    </template>

    <div class="p-gutter lg:px-margin-desktop">
      <div
        class="bg-surface-container border border-outline-variant p-panel-padding mb-stack-lg flex flex-wrap items-center gap-stack-md"
      >
        <div class="relative flex-1 min-w-[240px]">
          <span
            class="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-on-surface-variant text-sm"
            >search</span
          >
          <input
            v-model="search"
            class="w-full bg-surface-container-lowest border border-outline-variant text-on-surface pl-10 pr-4 py-2 font-body-sm focus:outline-none focus:border-primary transition-all"
            placeholder="Search sessions, patients, or IDs..."
            type="text"
          />
        </div>
        <div class="flex flex-col gap-unit">
          <label class="font-label-caps text-label-caps text-on-surface-variant uppercase"
            >Status Filter</label
          >
          <select
            v-model="statusFilter"
            class="bg-surface-container-lowest border border-outline-variant text-on-surface font-body-sm px-3 py-1.5 rounded focus:ring-0 focus:border-primary"
          >
            <option value="">All Statuses</option>
            <option value="completed">Complete</option>
            <option value="processing">Processing</option>
            <option value="pending">Pending</option>
            <option value="partial">Partial</option>
            <option value="failed">Failed</option>
            <option value="flagged">Flagged</option>
          </select>
        </div>
      </div>

      <div v-if="scansStore.loading" class="text-on-surface-variant py-12 text-center">
        Loading sessions...
      </div>
      <div v-else class="bg-surface-container border border-outline-variant overflow-hidden">
        <table class="w-full text-left border-collapse">
          <thead>
            <tr class="bg-surface-container-high border-b border-outline-variant">
              <th class="p-panel-padding font-label-caps text-label-caps text-on-surface-variant uppercase">
                Scan ID
              </th>
              <th class="p-panel-padding font-label-caps text-label-caps text-on-surface-variant uppercase">
                Patient Name
              </th>
              <th class="p-panel-padding font-label-caps text-label-caps text-on-surface-variant uppercase">
                Date &amp; Time
              </th>
              <th class="p-panel-padding font-label-caps text-label-caps text-on-surface-variant uppercase">
                Detection Model
              </th>
              <th class="p-panel-padding font-label-caps text-label-caps text-on-surface-variant uppercase">
                Status
              </th>
              <th class="p-panel-padding font-label-caps text-label-caps text-on-surface-variant uppercase text-right">
                Actions
              </th>
            </tr>
          </thead>
          <tbody class="divide-y divide-outline-variant/30">
            <tr
              v-for="scan in scansStore.list"
              :key="scan.id"
              class="hover:bg-surface-container-high transition-colors"
            >
              <td class="p-panel-padding font-metric-sm text-primary">
                {{ scan.id.slice(0, 8).toUpperCase() }}
              </td>
              <td class="p-panel-padding font-bold">{{ scan.patient_name }}</td>
              <td class="p-panel-padding text-on-surface-variant">
                {{ formatDateTime(scan.created_at) }}
              </td>
              <td class="p-panel-padding">
                <span
                  class="bg-surface-container-highest border border-outline-variant px-2 py-0.5 rounded text-[10px] font-bold text-on-surface-variant"
                  >{{ scan.detector_model }}</span
                >
              </td>
              <td class="p-panel-padding">
                <ScanStatusBadge :status="scan.status" />
              </td>
              <td class="p-panel-padding text-right">
                <RouterLink
                  :to="
                    scan.status === 'processing' || scan.status === 'pending'
                      ? `/scans/${scan.id}/processing`
                      : `/scans/${scan.id}`
                  "
                  class="material-symbols-outlined text-on-surface-variant hover:text-primary transition-all inline-flex"
                  >visibility</RouterLink
                >
              </td>
            </tr>
          </tbody>
        </table>
        <p v-if="!scansStore.list.length" class="p-panel-padding text-on-surface-variant text-center">
          No scan sessions found.
        </p>
      </div>
    </div>
  </AppLayout>
</template>
