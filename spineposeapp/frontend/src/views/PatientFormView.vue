<script setup>
import { computed, onMounted, ref } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'
import AppLayout from '../components/AppLayout.vue'
import { usePatientsStore } from '../stores/patients'

const route = useRoute()
const router = useRouter()
const patientsStore = usePatientsStore()

const isEdit = computed(() => Boolean(route.params.id) && route.path.includes('/edit'))
const loading = ref(false)
const saving = ref(false)
const error = ref('')

const form = ref({
  first_name: '',
  last_name: '',
  date_of_birth: '',
  gender: 'male',
  height_cm: '',
  weight_kg: '',
  medical_record_number: '',
  phone: '',
  email: '',
  emergency_contact_name: '',
  emergency_contact_phone: '',
  referring_physician: '',
  primary_diagnosis: '',
  medical_notes: '',
})

onMounted(async () => {
  if (isEdit.value) {
    loading.value = true
    try {
      const patient = await patientsStore.fetchOne(route.params.id)
      form.value = {
        first_name: patient.first_name,
        last_name: patient.last_name,
        date_of_birth: patient.date_of_birth,
        gender: patient.gender,
        height_cm: patient.height_cm,
        weight_kg: patient.weight_kg,
        medical_record_number: patient.medical_record_number || '',
        phone: patient.phone || '',
        email: patient.email || '',
        emergency_contact_name: patient.emergency_contact_name || '',
        emergency_contact_phone: patient.emergency_contact_phone || '',
        referring_physician: patient.referring_physician || '',
        primary_diagnosis: patient.primary_diagnosis || '',
        medical_notes: patient.medical_notes || '',
      }
    } finally {
      loading.value = false
    }
  }
})

async function onSubmit() {
  error.value = ''
  saving.value = true
  const payload = {
    ...form.value,
    height_cm: parseFloat(form.value.height_cm),
    weight_kg: parseFloat(form.value.weight_kg),
  }
  try {
    if (isEdit.value) {
      await patientsStore.update(route.params.id, payload)
      router.push(`/patients/${route.params.id}`)
    } else {
      const created = await patientsStore.create(payload)
      router.push(`/patients/${created.id}`)
    }
  } catch (e) {
    error.value = e.response?.data?.detail || 'Failed to save patient.'
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <AppLayout
    :title="isEdit ? 'Edit Patient' : 'Add New Patient'"
    subtitle="Clinical record registration"
  >
    <div v-if="loading" class="p-margin-desktop text-on-surface-variant">Loading...</div>
    <form v-else class="p-gutter lg:px-margin-desktop max-w-4xl" @submit.prevent="onSubmit">
      <div
        class="bg-surface-container border border-outline-variant p-panel-padding space-y-stack-md"
      >
        <div class="grid grid-cols-1 md:grid-cols-2 gap-stack-md">
          <div class="flex flex-col gap-2">
            <label class="font-label-caps text-label-caps text-on-surface-variant"
              >FIRST NAME</label
            >
            <input
              v-model="form.first_name"
              class="w-full px-4 py-3 bg-[#0a0a0a] border border-outline-variant focus:border-primary-container outline-none font-metric-sm text-on-surface"
              required
              type="text"
            />
          </div>
          <div class="flex flex-col gap-2">
            <label class="font-label-caps text-label-caps text-on-surface-variant">LAST NAME</label>
            <input
              v-model="form.last_name"
              class="w-full px-4 py-3 bg-[#0a0a0a] border border-outline-variant focus:border-primary-container outline-none font-metric-sm text-on-surface"
              required
              type="text"
            />
          </div>
          <div class="flex flex-col gap-2">
            <label class="font-label-caps text-label-caps text-on-surface-variant"
              >DATE OF BIRTH</label
            >
            <input
              v-model="form.date_of_birth"
              class="w-full px-4 py-3 bg-[#0a0a0a] border border-outline-variant focus:border-primary-container outline-none font-metric-sm text-on-surface"
              required
              type="date"
            />
          </div>
          <div class="flex flex-col gap-2">
            <label class="font-label-caps text-label-caps text-on-surface-variant">GENDER</label>
            <select
              v-model="form.gender"
              class="w-full px-4 py-3 bg-[#0a0a0a] border border-outline-variant focus:border-primary-container outline-none font-metric-sm text-on-surface"
            >
              <option value="male">Male</option>
              <option value="female">Female</option>
              <option value="other">Other</option>
            </select>
          </div>
          <div class="flex flex-col gap-2">
            <label class="font-label-caps text-label-caps text-on-surface-variant"
              >HEIGHT (CM)</label
            >
            <input
              v-model="form.height_cm"
              class="w-full px-4 py-3 bg-[#0a0a0a] border border-outline-variant focus:border-primary-container outline-none font-metric-sm text-on-surface"
              required
              type="number"
              step="0.1"
            />
          </div>
          <div class="flex flex-col gap-2">
            <label class="font-label-caps text-label-caps text-on-surface-variant"
              >WEIGHT (KG)</label
            >
            <input
              v-model="form.weight_kg"
              class="w-full px-4 py-3 bg-[#0a0a0a] border border-outline-variant focus:border-primary-container outline-none font-metric-sm text-on-surface"
              required
              type="number"
              step="0.1"
            />
          </div>
          <div class="flex flex-col gap-2">
            <label class="font-label-caps text-label-caps text-on-surface-variant"
              >MEDICAL RECORD #</label
            >
            <input
              v-model="form.medical_record_number"
              class="w-full px-4 py-3 bg-[#0a0a0a] border border-outline-variant focus:border-primary-container outline-none font-metric-sm text-on-surface"
              type="text"
            />
          </div>
          <div class="flex flex-col gap-2">
            <label class="font-label-caps text-label-caps text-on-surface-variant"
              >PRIMARY DIAGNOSIS</label
            >
            <input
              v-model="form.primary_diagnosis"
              class="w-full px-4 py-3 bg-[#0a0a0a] border border-outline-variant focus:border-primary-container outline-none font-metric-sm text-on-surface"
              type="text"
            />
          </div>
          <div class="flex flex-col gap-2">
            <label class="font-label-caps text-label-caps text-on-surface-variant">PHONE</label>
            <input
              v-model="form.phone"
              class="w-full px-4 py-3 bg-[#0a0a0a] border border-outline-variant focus:border-primary-container outline-none font-metric-sm text-on-surface"
              type="tel"
            />
          </div>
          <div class="flex flex-col gap-2">
            <label class="font-label-caps text-label-caps text-on-surface-variant">EMAIL</label>
            <input
              v-model="form.email"
              class="w-full px-4 py-3 bg-[#0a0a0a] border border-outline-variant focus:border-primary-container outline-none font-metric-sm text-on-surface"
              type="email"
            />
          </div>
        </div>
        <div class="flex flex-col gap-2">
          <label class="font-label-caps text-label-caps text-on-surface-variant"
            >MEDICAL NOTES</label
          >
          <textarea
            v-model="form.medical_notes"
            class="w-full px-4 py-3 bg-[#0a0a0a] border border-outline-variant focus:border-primary-container outline-none font-metric-sm text-on-surface min-h-[120px]"
            rows="4"
          ></textarea>
        </div>
        <p v-if="error" class="text-error text-sm">{{ error }}</p>
        <div class="flex gap-4 pt-stack-md">
          <button
            class="px-6 py-3 bg-primary text-on-primary font-bold font-label-caps tracking-widest hover:opacity-90 disabled:opacity-50"
            type="submit"
            :disabled="saving"
          >
            {{ saving ? 'SAVING...' : isEdit ? 'UPDATE PATIENT' : 'CREATE PATIENT' }}
          </button>
          <RouterLink
            :to="isEdit ? `/patients/${route.params.id}` : '/patients'"
            class="px-6 py-3 border border-outline-variant text-on-surface font-label-caps tracking-widest hover:bg-surface-container transition-colors"
          >
            CANCEL
          </RouterLink>
        </div>
      </div>
    </form>
  </AppLayout>
</template>
