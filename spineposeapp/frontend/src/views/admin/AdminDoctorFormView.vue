<script setup>
import { onMounted, ref } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'
import AdminLayout from './AdminLayout.vue'
import { getAdminDoctor, updateAdminDoctor } from '../../api/client'

const route = useRoute()
const router = useRouter()

const loading = ref(true)
const saving = ref(false)
const error = ref('')

const form = ref({
  first_name: '',
  last_name: '',
  email: '',
  specialty: '',
  license_number: '',
  clinic_name: '',
  country: '',
  city: '',
  bio: '',
  is_active: true,
  role: 'doctor',
  patient_count: 0,
  scan_count: 0,
})

onMounted(async () => {
  try {
    const { data } = await getAdminDoctor(route.params.id)
    form.value = {
      first_name: data.first_name,
      last_name: data.last_name,
      email: data.email,
      specialty: data.specialty || '',
      license_number: data.license_number || '',
      clinic_name: data.clinic_name || '',
      country: data.country || '',
      city: data.city || '',
      bio: data.bio || '',
      is_active: data.is_active,
      role: data.role,
      patient_count: data.patient_count,
      scan_count: data.scan_count,
    }
  } finally {
    loading.value = false
  }
})

async function onSubmit() {
  error.value = ''
  saving.value = true
  const payload = {
    first_name: form.value.first_name,
    last_name: form.value.last_name,
    specialty: form.value.specialty || null,
    license_number: form.value.license_number || null,
    clinic_name: form.value.clinic_name || null,
    country: form.value.country || null,
    city: form.value.city || null,
    bio: form.value.bio || null,
    is_active: form.value.is_active,
  }
  try {
    await updateAdminDoctor(route.params.id, payload)
    router.push('/admin/doctors')
  } catch (e) {
    const detail = e.response?.data?.detail
    error.value =
      typeof detail === 'object' ? detail.message || 'Failed to save doctor.' : detail || 'Failed to save doctor.'
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <AdminLayout title="Edit Doctor" subtitle="Update doctor profile and account status">
    <div v-if="loading" class="p-margin-desktop text-on-surface-variant">Loading...</div>
    <form v-else class="p-gutter lg:px-margin-desktop max-w-4xl pb-8" @submit.prevent="onSubmit">
      <div
        class="bg-surface-container border border-outline-variant p-panel-padding space-y-stack-md mb-6"
      >
        <div class="grid grid-cols-1 md:grid-cols-2 gap-stack-md">
          <div class="flex flex-col gap-2">
            <label class="font-label-caps text-label-caps text-on-surface-variant"
              >FIRST NAME</label
            >
            <input
              v-model="form.first_name"
              class="bg-background border border-outline-variant focus:border-primary-container outline-none px-4 py-3 text-on-surface"
              required
              type="text"
            />
          </div>
          <div class="flex flex-col gap-2">
            <label class="font-label-caps text-label-caps text-on-surface-variant"
              >LAST NAME</label
            >
            <input
              v-model="form.last_name"
              class="bg-background border border-outline-variant focus:border-primary-container outline-none px-4 py-3 text-on-surface"
              required
              type="text"
            />
          </div>
          <div class="flex flex-col gap-2">
            <label class="font-label-caps text-label-caps text-on-surface-variant">EMAIL</label>
            <input
              v-model="form.email"
              class="bg-background border border-outline-variant outline-none px-4 py-3 text-on-surface-variant cursor-not-allowed opacity-70"
              disabled
              type="email"
            />
          </div>
          <div class="flex flex-col gap-2">
            <label class="font-label-caps text-label-caps text-on-surface-variant"
              >SPECIALTY</label
            >
            <input
              v-model="form.specialty"
              class="bg-background border border-outline-variant focus:border-primary-container outline-none px-4 py-3 text-on-surface"
              type="text"
            />
          </div>
          <div class="flex flex-col gap-2">
            <label class="font-label-caps text-label-caps text-on-surface-variant"
              >LICENSE NUMBER</label
            >
            <input
              v-model="form.license_number"
              class="bg-background border border-outline-variant focus:border-primary-container outline-none px-4 py-3 text-on-surface"
              type="text"
            />
          </div>
          <div class="flex flex-col gap-2">
            <label class="font-label-caps text-label-caps text-on-surface-variant"
              >CLINIC NAME</label
            >
            <input
              v-model="form.clinic_name"
              class="bg-background border border-outline-variant focus:border-primary-container outline-none px-4 py-3 text-on-surface"
              type="text"
            />
          </div>
          <div class="flex flex-col gap-2">
            <label class="font-label-caps text-label-caps text-on-surface-variant">COUNTRY</label>
            <input
              v-model="form.country"
              class="bg-background border border-outline-variant focus:border-primary-container outline-none px-4 py-3 text-on-surface"
              type="text"
            />
          </div>
          <div class="flex flex-col gap-2">
            <label class="font-label-caps text-label-caps text-on-surface-variant">CITY</label>
            <input
              v-model="form.city"
              class="bg-background border border-outline-variant focus:border-primary-container outline-none px-4 py-3 text-on-surface"
              type="text"
            />
          </div>
        </div>
        <div class="flex flex-col gap-2">
          <label class="font-label-caps text-label-caps text-on-surface-variant">BIO</label>
          <textarea
            v-model="form.bio"
            class="bg-background border border-outline-variant focus:border-primary-container outline-none px-4 py-3 text-on-surface min-h-[100px]"
            rows="4"
          />
        </div>
        <div class="flex items-center gap-6 pt-2">
          <label class="flex items-center gap-3 cursor-pointer">
            <input
              v-model="form.is_active"
              class="custom-checkbox w-4 h-4"
              type="checkbox"
            />
            <span class="font-body-sm text-sm text-on-surface">Account active</span>
          </label>
          <span class="font-label-caps text-xs text-on-surface-variant">
            Role: {{ form.role }}
          </span>
        </div>
        <div class="flex gap-6 pt-2 font-metric-sm text-sm text-on-surface-variant">
          <span>{{ form.patient_count }} patients</span>
          <span>{{ form.scan_count }} scans</span>
        </div>
      </div>

      <p v-if="error" class="text-error text-sm mb-4">{{ error }}</p>

      <div class="flex items-center gap-4">
        <button
          class="bg-primary-container text-on-primary-container font-bold py-3 px-8 font-label-caps hover:bg-primary transition-all disabled:opacity-70"
          type="submit"
          :disabled="saving"
        >
          {{ saving ? 'SAVING...' : 'SAVE CHANGES' }}
        </button>
        <RouterLink
          to="/admin/doctors"
          class="font-body-sm text-on-surface-variant hover:text-on-surface"
        >
          Cancel
        </RouterLink>
      </div>
    </form>
  </AdminLayout>
</template>
