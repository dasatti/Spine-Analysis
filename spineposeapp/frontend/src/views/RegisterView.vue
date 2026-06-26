<script setup>
import { ref } from 'vue'
import { RouterLink, useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const authStore = useAuthStore()
const step = ref(1)
const error = ref('')
const termsAccepted = ref(false)

const form = ref({
  email: '',
  password: '',
  confirmPassword: '',
  first_name: '',
  last_name: '',
  specialty: '',
  license_number: '',
  clinic_name: '',
  city: '',
  country: '',
})

function nextStep() {
  error.value = ''
  if (!form.value.email || !form.value.password || !form.value.first_name || !form.value.last_name) {
    error.value = 'Please complete all required fields.'
    return
  }
  if (form.value.password !== form.value.confirmPassword) {
    error.value = 'Passwords do not match.'
    return
  }
  step.value = 2
}

async function onSubmit() {
  error.value = ''
  if (!termsAccepted.value) {
    error.value = 'You must accept the terms of service.'
    return
  }
  try {
    await authStore.register({
      email: form.value.email,
      password: form.value.password,
      first_name: form.value.first_name,
      last_name: form.value.last_name,
      specialty: form.value.specialty || null,
      license_number: form.value.license_number || null,
      clinic_name: form.value.clinic_name || null,
      city: form.value.city || null,
      country: form.value.country || null,
    })
    router.push('/dashboard')
  } catch (e) {
    error.value =
      e.fieldErrors?.email ||
      e.response?.data?.detail ||
      (typeof e.response?.data?.detail === 'string' ? e.response.data.detail : 'Registration failed.')
  }
}
</script>

<template>
  <div class="min-h-screen flex flex-col md:flex-row">
    <div
      class="hidden md:flex md:w-1/2 relative flex-col justify-between p-margin-desktop bg-surface-container-lowest overflow-hidden border-r border-outline-variant"
    >
      <div class="relative z-10 flex items-center gap-3">
        <span class="material-symbols-outlined text-primary text-headline-lg">biotech</span>
        <span
          class="font-headline-md text-headline-md font-bold text-primary uppercase tracking-tighter"
          >SpinePose</span
        >
      </div>
      <div class="relative z-10 max-w-lg mb-24">
        <div class="flex items-center gap-4 mb-stack-md">
          <div class="spine-bar"></div>
          <h1 class="font-display-lg text-display-lg leading-tight">Advanced Biometric Alignment</h1>
        </div>
        <p class="font-body-lg text-body-lg text-on-surface-variant max-w-md">
          Join a global network of spinal health professionals leveraging surgical-grade AI
          diagnostics and real-time posture analysis.
        </p>
      </div>
      <div class="relative z-10 flex items-center gap-gutter">
        <div class="flex flex-col">
          <span class="font-label-caps text-label-caps text-on-surface-variant mb-1"
            >SYSTEM STATUS</span
          >
          <div class="flex items-center gap-2">
            <div class="w-2 h-2 rounded-full bg-primary animate-pulse"></div>
            <span class="font-metric-sm text-metric-sm">ENCRYPTION ACTIVE // L4 NODE</span>
          </div>
        </div>
      </div>
    </div>

    <div
      class="flex-1 flex flex-col items-center justify-center p-margin-mobile md:p-margin-desktop bg-surface-container-lowest min-h-screen"
    >
      <div class="w-full max-w-md">
        <div class="mb-stack-lg">
          <div class="flex justify-between items-end mb-stack-sm">
            <span class="font-label-caps text-label-caps text-primary tracking-widest"
              >REGISTRATION PROGRESS</span
            >
            <span class="font-metric-sm text-metric-sm text-on-surface"
              >STEP {{ String(step).padStart(2, '0') }} / 02</span
            >
          </div>
          <div class="w-full h-1 bg-surface-container-high overflow-hidden">
            <div
              class="h-full bg-primary transition-all duration-700 ease-out"
              :class="step === 1 ? 'w-1/2' : 'w-full'"
            ></div>
          </div>
        </div>

        <div v-if="step === 1">
          <div class="flex items-center gap-4 mb-stack-lg">
            <div class="spine-bar"></div>
            <h2 class="font-headline-lg text-headline-lg">Account Details</h2>
          </div>
          <form class="space-y-stack-md" @submit.prevent="nextStep">
            <div class="grid grid-cols-2 gap-stack-md">
              <div class="flex flex-col gap-2">
                <label class="font-label-caps text-label-caps text-on-surface-variant"
                  >FIRST NAME</label
                >
                <input
                  v-model="form.first_name"
                  class="w-full px-4 py-3 rounded-none focus:ring-0 bg-[#0a0a0a] border border-outline-variant focus:border-primary-container text-on-surface font-metric-sm"
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
                  class="w-full px-4 py-3 rounded-none focus:ring-0 bg-[#0a0a0a] border border-outline-variant focus:border-primary-container text-on-surface font-metric-sm"
                  required
                  type="text"
                />
              </div>
            </div>
            <div class="flex flex-col gap-2">
              <label class="font-label-caps text-label-caps text-on-surface-variant">EMAIL</label>
              <input
                v-model="form.email"
                class="w-full px-4 py-3 rounded-none focus:ring-0 bg-[#0a0a0a] border border-outline-variant focus:border-primary-container text-on-surface font-metric-sm"
                required
                type="email"
              />
            </div>
            <div class="flex flex-col gap-2">
              <label class="font-label-caps text-label-caps text-on-surface-variant"
                >PASSWORD</label
              >
              <input
                v-model="form.password"
                class="w-full px-4 py-3 rounded-none focus:ring-0 bg-[#0a0a0a] border border-outline-variant focus:border-primary-container text-on-surface font-metric-sm"
                required
                type="password"
              />
            </div>
            <div class="flex flex-col gap-2">
              <label class="font-label-caps text-label-caps text-on-surface-variant"
                >CONFIRM PASSWORD</label
              >
              <input
                v-model="form.confirmPassword"
                class="w-full px-4 py-3 rounded-none focus:ring-0 bg-[#0a0a0a] border border-outline-variant focus:border-primary-container text-on-surface font-metric-sm"
                required
                type="password"
              />
            </div>
            <p v-if="error" class="text-error text-sm">{{ error }}</p>
            <button
              class="w-full py-4 bg-primary text-on-primary font-bold font-label-caps tracking-widest hover:opacity-90 transition-opacity active:scale-[0.98]"
              type="submit"
            >
              CONTINUE TO STEP 2
            </button>
          </form>
        </div>

        <div v-else>
          <div class="flex items-center gap-4 mb-stack-lg">
            <div class="spine-bar"></div>
            <h2 class="font-headline-lg text-headline-lg">Clinical Credentials</h2>
          </div>
          <form class="space-y-stack-md" @submit.prevent="onSubmit">
            <div class="flex flex-col gap-2">
              <label class="font-label-caps text-label-caps text-on-surface-variant"
                >MEDICAL SPECIALTY</label
              >
              <div class="relative">
                <select
                  v-model="form.specialty"
                  class="w-full px-4 py-3 appearance-none rounded-none focus:ring-0 bg-[#0a0a0a] border border-outline-variant focus:border-primary-container text-on-surface font-metric-sm"
                >
                  <option disabled value="">Select Specialty</option>
                  <option value="orthopedic">Orthopedic Surgeon</option>
                  <option value="chiropractor">Chiropractor</option>
                  <option value="physical_therapist">Physical Therapist</option>
                  <option value="neurologist">Neurologist</option>
                  <option value="radiologist">Radiologist</option>
                </select>
                <span
                  class="material-symbols-outlined absolute right-4 top-1/2 -translate-y-1/2 pointer-events-none text-on-surface-variant"
                  >expand_more</span
                >
              </div>
            </div>
            <div class="flex flex-col gap-2">
              <label class="font-label-caps text-label-caps text-on-surface-variant"
                >MEDICAL LICENSE NUMBER</label
              >
              <input
                v-model="form.license_number"
                class="w-full px-4 py-3 rounded-none focus:ring-0 bg-[#0a0a0a] border border-outline-variant focus:border-primary-container text-on-surface font-metric-sm"
                placeholder="e.g. LIC-99203348"
                type="text"
              />
            </div>
            <div class="grid grid-cols-2 gap-stack-md">
              <div class="flex flex-col gap-2">
                <label class="font-label-caps text-label-caps text-on-surface-variant"
                  >CLINIC NAME</label
                >
                <input
                  v-model="form.clinic_name"
                  class="w-full px-4 py-3 rounded-none focus:ring-0 bg-[#0a0a0a] border border-outline-variant focus:border-primary-container text-on-surface font-metric-sm"
                  placeholder="Center Name"
                  type="text"
                />
              </div>
              <div class="flex flex-col gap-2">
                <label class="font-label-caps text-label-caps text-on-surface-variant">CITY</label>
                <input
                  v-model="form.city"
                  class="w-full px-4 py-3 rounded-none focus:ring-0 bg-[#0a0a0a] border border-outline-variant focus:border-primary-container text-on-surface font-metric-sm"
                  placeholder="City"
                  type="text"
                />
              </div>
            </div>
            <div class="py-stack-sm">
              <label class="flex items-start gap-3 cursor-pointer group">
                <input
                  v-model="termsAccepted"
                  class="w-4 h-4 mt-1 bg-transparent border-outline appearance-none checked:bg-primary checked:border-primary transition-all custom-checkbox"
                  type="checkbox"
                />
                <span
                  class="font-body-sm text-body-sm text-on-surface-variant group-hover:text-on-surface transition-colors"
                >
                  I certify that the provided clinical credentials are valid and agree to the
                  Practitioner Terms of Service.
                </span>
              </label>
            </div>
            <p v-if="error" class="text-error text-sm">{{ error }}</p>
            <div class="flex flex-col gap-4 pt-stack-md">
              <button
                class="w-full py-4 bg-primary text-on-primary font-bold font-label-caps tracking-widest hover:opacity-90 transition-opacity active:scale-[0.98] disabled:opacity-50"
                type="submit"
                :disabled="authStore.loading"
              >
                {{ authStore.loading ? 'REGISTERING...' : 'COMPLETE REGISTRATION' }}
              </button>
              <button
                class="w-full py-4 border border-outline-variant text-on-surface font-label-caps tracking-widest hover:bg-surface-container transition-colors flex items-center justify-center gap-2"
                type="button"
                @click="step = 1"
              >
                <span class="material-symbols-outlined text-[18px]">arrow_back</span>
                BACK TO STEP 1
              </button>
            </div>
          </form>
        </div>

        <div class="mt-stack-lg text-center">
          <p class="font-body-sm text-body-sm text-on-surface-variant">
            Already have a clinical account?
            <RouterLink class="text-primary font-bold" to="/login">Log In</RouterLink>
          </p>
        </div>
      </div>
    </div>
  </div>
</template>
