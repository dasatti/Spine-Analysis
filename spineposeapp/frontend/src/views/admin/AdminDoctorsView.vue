<script setup>
import { onMounted, ref, watch } from 'vue'
import { RouterLink } from 'vue-router'
import AdminLayout from './AdminLayout.vue'
import { listAdminDoctors } from '../../api/client'

const loading = ref(true)
const doctors = ref([])
const total = ref(0)
const page = ref(1)
const totalPages = ref(1)
const search = ref('')
const statusFilter = ref('')

async function loadDoctors() {
  loading.value = true
  try {
    const params = { page: page.value, page_size: 20 }
    if (search.value) params.search = search.value
    if (statusFilter.value === 'active') params.is_active = true
    if (statusFilter.value === 'inactive') params.is_active = false
    const { data } = await listAdminDoctors(params)
    doctors.value = data.items
    total.value = data.total
    totalPages.value = data.total_pages
  } finally {
    loading.value = false
  }
}

watch([search, statusFilter, page], loadDoctors)
onMounted(loadDoctors)
</script>

<template>
  <AdminLayout title="Doctors">
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
              placeholder="Search by name or email..."
              type="text"
            />
          </div>
          <select
            v-model="statusFilter"
            class="bg-background border border-outline-variant text-on-surface font-label-caps px-3 py-2 outline-none focus:border-primary-container appearance-none cursor-pointer"
          >
            <option value="">STATUS: ALL</option>
            <option value="active">ACTIVE</option>
            <option value="inactive">INACTIVE</option>
          </select>
        </div>
        <p class="font-label-caps text-on-surface-variant text-xs">{{ total }} doctors</p>
      </div>
    </section>

    <section class="p-gutter lg:px-margin-desktop flex-1 pb-8">
      <div v-if="loading" class="text-on-surface-variant py-12 text-center">Loading doctors...</div>
      <div v-else class="border border-outline-variant bg-background overflow-hidden">
        <div class="overflow-x-auto custom-scrollbar">
          <table class="w-full border-collapse">
            <thead class="bg-[#1A1A1A] border-b border-outline-variant">
              <tr>
                <th class="px-6 py-4 text-left font-label-caps text-on-surface-variant">NAME</th>
                <th class="px-6 py-4 text-left font-label-caps text-on-surface-variant">EMAIL</th>
                <th class="px-6 py-4 text-left font-label-caps text-on-surface-variant">
                  SPECIALTY
                </th>
                <th class="px-6 py-4 text-left font-label-caps text-on-surface-variant">
                  CLINIC
                </th>
                <th class="px-6 py-4 text-left font-label-caps text-on-surface-variant">
                  PATIENTS
                </th>
                <th class="px-6 py-4 text-left font-label-caps text-on-surface-variant">SCANS</th>
                <th class="px-6 py-4 text-left font-label-caps text-on-surface-variant">STATUS</th>
                <th class="px-6 py-4 text-center font-label-caps text-on-surface-variant">
                  ACTIONS
                </th>
              </tr>
            </thead>
            <tbody class="divide-y divide-outline-variant">
              <tr
                v-for="doctor in doctors"
                :key="doctor.id"
                class="hover:bg-surface-container-low transition-colors"
              >
                <td class="px-6 py-4">
                  <p class="font-body-sm text-sm font-bold text-on-surface">
                    Dr. {{ doctor.first_name }} {{ doctor.last_name }}
                  </p>
                  <p
                    v-if="doctor.role === 'admin'"
                    class="font-label-caps text-[10px] text-primary mt-0.5"
                  >
                    Admin
                  </p>
                </td>
                <td class="px-6 py-4 font-metric-sm text-sm text-on-surface-variant">
                  {{ doctor.email }}
                </td>
                <td class="px-6 py-4 font-body-sm text-sm text-on-surface-variant">
                  {{ doctor.specialty || '—' }}
                </td>
                <td class="px-6 py-4 font-body-sm text-sm text-on-surface-variant">
                  {{ doctor.clinic_name || '—' }}
                </td>
                <td class="px-6 py-4 font-metric-sm text-sm text-on-surface">
                  {{ doctor.patient_count }}
                </td>
                <td class="px-6 py-4 font-metric-sm text-sm text-on-surface">
                  {{ doctor.scan_count }}
                </td>
                <td class="px-6 py-4">
                  <span
                    :class="[
                      'font-label-caps text-[10px] px-2 py-1',
                      doctor.is_active
                        ? 'bg-primary-container/20 text-primary'
                        : 'bg-error/20 text-error',
                    ]"
                  >
                    {{ doctor.is_active ? 'Active' : 'Inactive' }}
                  </span>
                </td>
                <td class="px-6 py-4 text-center">
                  <RouterLink
                    :to="`/admin/doctors/${doctor.id}/edit`"
                    class="inline-flex items-center gap-1 text-primary hover:underline font-body-sm text-sm"
                  >
                    <span class="material-symbols-outlined text-[16px]">edit</span>
                    Edit
                  </RouterLink>
                </td>
              </tr>
              <tr v-if="!doctors.length">
                <td colspan="8" class="px-6 py-12 text-center text-on-surface-variant">
                  No doctors found.
                </td>
              </tr>
            </tbody>
          </table>
        </div>
        <div
          v-if="totalPages > 1"
          class="bg-[#1A1A1A] border-t border-outline-variant px-6 py-4 flex items-center justify-between"
        >
          <button
            class="font-label-caps text-on-surface-variant hover:text-on-surface disabled:opacity-40"
            :disabled="page <= 1"
            type="button"
            @click="page--"
          >
            Previous
          </button>
          <span class="font-metric-sm text-sm text-on-surface-variant">
            Page {{ page }} of {{ totalPages }}
          </span>
          <button
            class="font-label-caps text-on-surface-variant hover:text-on-surface disabled:opacity-40"
            :disabled="page >= totalPages"
            type="button"
            @click="page++"
          >
            Next
          </button>
        </div>
      </div>
    </section>
  </AdminLayout>
</template>
