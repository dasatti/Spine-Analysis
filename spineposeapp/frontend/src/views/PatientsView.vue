<script setup>
import { onMounted, ref, watch } from 'vue'
import { RouterLink } from 'vue-router'
import AppLayout from '../components/AppLayout.vue'
import PatientRow from '../components/PatientRow.vue'
import { usePatientsStore } from '../stores/patients'

const patientsStore = usePatientsStore()
const search = ref('')
const riskFilter = ref('')
const sortOrder = ref('recent')
const page = ref(1)

async function loadPatients() {
  const params = { page: page.value, page_size: 20 }
  if (search.value) params.search = search.value
  if (riskFilter.value) params.risk_level = riskFilter.value.toLowerCase()
  if (sortOrder.value === 'oldest') params.sort = 'created_at'
  await patientsStore.fetchList(params)
}

watch([search, riskFilter, sortOrder, page], loadPatients)

onMounted(loadPatients)
</script>

<template>
  <AppLayout title="Patient Management">
    <section class="p-gutter lg:px-margin-desktop lg:pt-8">
      <div
        class="flex flex-wrap gap-4 items-center justify-between bg-surface-container-low p-4 border border-outline-variant"
      >
        <div class="flex flex-1 min-w-[300px] items-center gap-4">
          <div class="relative flex-1 max-w-md">
            <span
              class="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-on-surface-variant text-sm"
              >search</span
            >
            <input
              v-model="search"
              class="w-full bg-background border border-outline-variant focus:border-primary-container outline-none px-10 py-2 font-metric-sm text-metric-sm text-on-surface placeholder:text-on-surface-variant/50"
              placeholder="Search by ID or Patient Name..."
              type="text"
            />
          </div>
          <div class="flex items-center gap-2">
            <select
              v-model="riskFilter"
              class="bg-background border border-outline-variant text-on-surface font-label-caps px-3 py-2 outline-none focus:border-primary-container appearance-none cursor-pointer"
            >
              <option value="">RISK: ALL</option>
              <option value="elevated">ELEVATED</option>
              <option value="monitor">MONITOR</option>
              <option value="normal">NORMAL</option>
            </select>
            <select
              v-model="sortOrder"
              class="bg-background border border-outline-variant text-on-surface font-label-caps px-3 py-2 outline-none focus:border-primary-container appearance-none cursor-pointer"
            >
              <option value="recent">DATE: RECENT</option>
              <option value="oldest">DATE: OLDEST</option>
            </select>
          </div>
        </div>
        <RouterLink
          to="/patients/new"
          class="bg-primary-container hover:bg-primary-fixed-dim text-on-primary-container px-6 py-2.5 font-bold flex items-center gap-2 transition-all active:scale-[0.98]"
        >
          <span class="material-symbols-outlined">person_add</span>
          <span>ADD NEW PATIENT</span>
        </RouterLink>
      </div>
    </section>

    <section class="p-gutter lg:px-margin-desktop flex-1">
      <div v-if="patientsStore.loading" class="text-on-surface-variant py-12 text-center">
        Loading patients...
      </div>
      <div v-else class="border border-outline-variant bg-background overflow-hidden">
        <div class="overflow-x-auto custom-scrollbar">
          <table class="w-full border-collapse">
            <thead class="bg-[#1A1A1A] border-b border-outline-variant">
              <tr>
                <th class="px-6 py-4 text-left font-label-caps text-on-surface-variant">
                  PATIENT NAME
                </th>
                <th class="px-6 py-4 text-left font-label-caps text-on-surface-variant">
                  IDENTIFIER
                </th>
                <th class="px-6 py-4 text-left font-label-caps text-on-surface-variant">
                  AGE/GENDER
                </th>
                <th class="px-6 py-4 text-left font-label-caps text-on-surface-variant">
                  DIAGNOSIS
                </th>
                <th class="px-6 py-4 text-left font-label-caps text-on-surface-variant">
                  LAST SCAN
                </th>
                <th class="px-6 py-4 text-left font-label-caps text-on-surface-variant">
                  TOTAL SCANS
                </th>
                <th class="px-6 py-4 text-left font-label-caps text-on-surface-variant">
                  RISK LEVEL
                </th>
                <th class="px-6 py-4 text-center font-label-caps text-on-surface-variant">
                  ACTIONS
                </th>
              </tr>
            </thead>
            <tbody class="divide-y divide-outline-variant">
              <PatientRow
                v-for="patient in patientsStore.list"
                :key="patient.id"
                :patient="patient"
              />
            </tbody>
          </table>
        </div>
        <div
          class="bg-[#1A1A1A] border-t border-outline-variant px-6 py-4 flex items-center justify-between"
        >
          <p class="text-on-surface-variant font-metric-sm">
            Showing page {{ patientsStore.pagination.page }} of
            {{ patientsStore.pagination.pages }} ({{ patientsStore.pagination.total }} patients)
          </p>
          <div class="flex items-center gap-2">
            <button
              class="w-10 h-10 flex items-center justify-center border border-outline-variant text-on-surface-variant hover:border-primary transition-all disabled:opacity-30"
              :disabled="page <= 1"
              @click="page--"
            >
              <span class="material-symbols-outlined">chevron_left</span>
            </button>
            <button
              class="w-10 h-10 flex items-center justify-center border border-outline-variant text-on-surface-variant hover:border-primary transition-all disabled:opacity-30"
              :disabled="page >= patientsStore.pagination.pages"
              @click="page++"
            >
              <span class="material-symbols-outlined">chevron_right</span>
            </button>
          </div>
        </div>
      </div>
    </section>
  </AppLayout>
</template>
