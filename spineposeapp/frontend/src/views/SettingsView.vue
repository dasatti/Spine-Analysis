<script setup>
import { onMounted, ref } from 'vue'
import AppLayout from '../components/AppLayout.vue'
import { getSettings, updateDetectorSettings } from '../api/client'
import { useAuthStore } from '../stores/auth'

const authStore = useAuthStore()
const activeTab = ref('profile')
const settingsLoading = ref(false)
const saving = ref(false)
const message = ref('')
const error = ref('')

const deviceSettings = ref(null)
const selectedDetector = ref('spinepose_v2')

const profileForm = ref({
  first_name: '',
  last_name: '',
  specialty: '',
  clinic_name: '',
  city: '',
  country: '',
  bio: '',
})

const passwordForm = ref({
  current: '',
  next: '',
  confirm: '',
})

const tabs = [
  { id: 'profile', label: 'PROFILE' },
  { id: 'security', label: 'SECURITY' },
  { id: 'device', label: 'DEVICE & CAMERA' },
]

onMounted(async () => {
  if (authStore.doctor) {
    profileForm.value = {
      first_name: authStore.doctor.first_name,
      last_name: authStore.doctor.last_name,
      specialty: authStore.doctor.specialty || '',
      clinic_name: authStore.doctor.clinic_name || '',
      city: authStore.doctor.city || '',
      country: authStore.doctor.country || '',
      bio: authStore.doctor.bio || '',
    }
  } else {
    await authStore.fetchMe()
    if (authStore.doctor) {
      profileForm.value.first_name = authStore.doctor.first_name
      profileForm.value.last_name = authStore.doctor.last_name
    }
  }
})

async function loadDeviceSettings() {
  settingsLoading.value = true
  error.value = ''
  try {
    const { data } = await getSettings()
    deviceSettings.value = data
    selectedDetector.value = data.detector_model
  } catch (e) {
    error.value = e.response?.data?.message || 'Failed to load device settings.'
  } finally {
    settingsLoading.value = false
  }
}

function selectTab(id) {
  activeTab.value = id
  if (id === 'device') loadDeviceSettings()
}

async function saveProfile() {
  error.value = ''
  message.value = ''
  saving.value = true
  try {
    await authStore.updateProfile(profileForm.value)
    message.value = 'Profile updated successfully.'
  } catch (e) {
    error.value = e.response?.data?.detail || 'Failed to update profile.'
  } finally {
    saving.value = false
  }
}

async function savePassword() {
  error.value = ''
  message.value = ''
  if (passwordForm.value.next !== passwordForm.value.confirm) {
    error.value = 'New passwords do not match.'
    return
  }
  saving.value = true
  try {
    await authStore.changePassword(passwordForm.value.current, passwordForm.value.next)
    message.value = 'Password changed successfully.'
    passwordForm.value = { current: '', next: '', confirm: '' }
  } catch (e) {
    error.value = e.response?.data?.detail || 'Failed to change password.'
  } finally {
    saving.value = false
  }
}

async function saveDetectorSettings() {
  error.value = ''
  message.value = ''
  saving.value = true
  try {
    const { data } = await updateDetectorSettings({ detector_model: selectedDetector.value })
    deviceSettings.value = data
    selectedDetector.value = data.detector_model
    message.value = 'Detector preference saved. New scans will use this model.'
  } catch (e) {
    error.value = e.response?.data?.message || 'Failed to update detector settings.'
  } finally {
    saving.value = false
  }
}

function detectorLabel(id) {
  const match = deviceSettings.value?.available_detectors?.find((item) => item.id === id)
  return match?.label || id
}
</script>

<template>
  <AppLayout title="Settings — SpinePose" subtitle="Account and device configuration">
    <div class="p-gutter lg:px-margin-desktop max-w-6xl mx-auto">
      <div class="grid grid-cols-12 gap-gutter">
        <nav class="col-span-3 flex flex-col gap-unit">
          <button
            v-for="tab in tabs"
            :key="tab.id"
            :class="[
              'px-panel-padding py-3 font-label-caps text-left transition-colors flex items-center justify-between border-l-2',
              activeTab === tab.id
                ? 'text-primary bg-surface-container-high border-primary'
                : 'text-on-surface-variant hover:bg-surface-container-low border-transparent',
            ]"
            type="button"
            @click="selectTab(tab.id)"
          >
            {{ tab.label }}
            <span
              v-if="activeTab === tab.id"
              class="material-symbols-outlined text-[16px]"
              >chevron_right</span
            >
          </button>
        </nav>

        <div class="col-span-9 flex flex-col gap-stack-lg">
          <p v-if="message" class="text-primary text-sm">{{ message }}</p>
          <p v-if="error" class="text-error text-sm">{{ error }}</p>

          <section
            v-if="activeTab === 'profile'"
            class="bg-surface-container p-panel-padding border border-outline-variant rounded-lg"
          >
            <h3 class="font-headline-md text-headline-md text-on-surface mb-6">Profile</h3>
            <form class="grid grid-cols-2 gap-stack-md" @submit.prevent="saveProfile">
              <div class="flex flex-col gap-unit">
                <label class="font-label-caps text-[11px] text-on-surface-variant">FIRST NAME</label>
                <input
                  v-model="profileForm.first_name"
                  class="bg-surface-container-lowest border border-outline-variant focus:border-primary text-on-surface p-2 font-metric-sm rounded focus:outline-none"
                  required
                  type="text"
                />
              </div>
              <div class="flex flex-col gap-unit">
                <label class="font-label-caps text-[11px] text-on-surface-variant">LAST NAME</label>
                <input
                  v-model="profileForm.last_name"
                  class="bg-surface-container-lowest border border-outline-variant focus:border-primary text-on-surface p-2 font-metric-sm rounded focus:outline-none"
                  required
                  type="text"
                />
              </div>
              <div class="flex flex-col gap-unit">
                <label class="font-label-caps text-[11px] text-on-surface-variant">SPECIALTY</label>
                <input
                  v-model="profileForm.specialty"
                  class="bg-surface-container-lowest border border-outline-variant focus:border-primary text-on-surface p-2 font-metric-sm rounded focus:outline-none"
                  type="text"
                />
              </div>
              <div class="flex flex-col gap-unit">
                <label class="font-label-caps text-[11px] text-on-surface-variant">CLINIC</label>
                <input
                  v-model="profileForm.clinic_name"
                  class="bg-surface-container-lowest border border-outline-variant focus:border-primary text-on-surface p-2 font-metric-sm rounded focus:outline-none"
                  type="text"
                />
              </div>
              <div class="flex flex-col gap-unit col-span-2">
                <label class="font-label-caps text-[11px] text-on-surface-variant">BIO</label>
                <textarea
                  v-model="profileForm.bio"
                  class="bg-surface-container-lowest border border-outline-variant focus:border-primary text-on-surface p-2 font-metric-sm rounded focus:outline-none min-h-[80px]"
                  rows="3"
                ></textarea>
              </div>
              <button
                class="col-span-2 mt-4 px-6 py-3 bg-primary text-on-primary font-label-caps font-bold hover:opacity-90 disabled:opacity-50 w-fit"
                type="submit"
                :disabled="saving"
              >
                {{ saving ? 'SAVING...' : 'SAVE PROFILE' }}
              </button>
            </form>
          </section>

          <section
            v-else-if="activeTab === 'security'"
            class="bg-surface-container p-panel-padding border border-outline-variant rounded-lg"
          >
            <h3 class="font-headline-md text-headline-md text-on-surface mb-6">Security</h3>
            <form class="max-w-md space-y-stack-md" @submit.prevent="savePassword">
              <div class="flex flex-col gap-unit">
                <label class="font-label-caps text-[11px] text-on-surface-variant"
                  >CURRENT PASSWORD</label
                >
                <input
                  v-model="passwordForm.current"
                  class="bg-surface-container-lowest border border-outline-variant focus:border-primary text-on-surface p-2 font-metric-sm rounded focus:outline-none"
                  required
                  type="password"
                />
              </div>
              <div class="flex flex-col gap-unit">
                <label class="font-label-caps text-[11px] text-on-surface-variant"
                  >NEW PASSWORD</label
                >
                <input
                  v-model="passwordForm.next"
                  class="bg-surface-container-lowest border border-outline-variant focus:border-primary text-on-surface p-2 font-metric-sm rounded focus:outline-none"
                  required
                  type="password"
                />
              </div>
              <div class="flex flex-col gap-unit">
                <label class="font-label-caps text-[11px] text-on-surface-variant"
                  >CONFIRM NEW PASSWORD</label
                >
                <input
                  v-model="passwordForm.confirm"
                  class="bg-surface-container-lowest border border-outline-variant focus:border-primary text-on-surface p-2 font-metric-sm rounded focus:outline-none"
                  required
                  type="password"
                />
              </div>
              <button
                class="px-6 py-3 bg-primary text-on-primary font-label-caps font-bold hover:opacity-90 disabled:opacity-50"
                type="submit"
                :disabled="saving"
              >
                {{ saving ? 'UPDATING...' : 'CHANGE PASSWORD' }}
              </button>
            </form>
          </section>

          <section
            v-else
            class="bg-surface-container p-panel-padding border border-outline-variant rounded-lg space-y-stack-lg"
          >
            <div class="flex items-center gap-stack-sm">
              <span class="material-symbols-outlined text-primary">psychology</span>
              <h3 class="font-headline-md text-headline-md text-on-surface">Inference Engine</h3>
            </div>
            <div v-if="settingsLoading" class="text-on-surface-variant">Loading device settings...</div>
            <template v-else-if="deviceSettings">
              <form class="space-y-stack-lg" @submit.prevent="saveDetectorSettings">
                <div class="grid grid-cols-2 gap-gutter">
                  <div class="col-span-2 flex flex-col gap-unit">
                    <label class="font-label-caps text-[11px] text-on-surface-variant"
                      >POSE DETECTOR</label
                    >
                    <select
                      v-model="selectedDetector"
                      class="bg-surface-container-lowest border border-outline-variant focus:border-primary text-on-surface p-2 font-metric-sm rounded focus:outline-none"
                    >
                      <option
                        v-for="option in deviceSettings.available_detectors"
                        :key="option.id"
                        :value="option.id"
                        :disabled="!option.ready"
                      >
                        {{ option.label }}{{ option.ready ? '' : ' (unavailable)' }}
                      </option>
                    </select>
                    <p class="text-[11px] text-on-surface-variant">
                      Active: {{ detectorLabel(deviceSettings.detector_model) }}. New scans use
                      your saved preference.
                    </p>
                  </div>
                  <div class="bg-surface-container-low p-4 border border-outline-variant/30 rounded">
                    <span class="font-label-caps text-[11px] text-on-surface-variant block mb-2"
                      >KEYPOINT CONFIDENCE THRESHOLD</span
                    >
                    <span class="font-metric-sm text-primary">{{
                      deviceSettings.keypoint_confidence_threshold
                    }}</span>
                  </div>
                  <div class="bg-surface-container-low p-4 border border-outline-variant/30 rounded">
                    <span class="font-label-caps text-[11px] text-on-surface-variant block mb-2"
                      >MODEL STATUS</span
                    >
                    <div class="flex items-center gap-2">
                      <span
                        :class="[
                          'w-2 h-2 rounded-full',
                          deviceSettings.model_weights_loaded ? 'bg-primary' : 'bg-error',
                        ]"
                      ></span>
                      <span class="font-metric-sm">{{
                        deviceSettings.model_weights_loaded ? 'READY' : 'NOT READY'
                      }}</span>
                    </div>
                  </div>
                </div>
                <button
                  class="px-6 py-3 bg-primary text-on-primary font-label-caps font-bold hover:opacity-90 disabled:opacity-50 w-fit"
                  type="submit"
                  :disabled="saving || selectedDetector === deviceSettings.detector_model"
                >
                  {{ saving ? 'SAVING...' : 'SAVE DETECTOR' }}
                </button>
              </form>
              <p class="text-[10px] text-on-surface-variant leading-tight">
                SpinePose v2 uses MediaPipe for clinical spine landmarks. YOLOv8 Pose uses
                Ultralytics COCO keypoints mapped into the same analysis pipeline.
              </p>
            </template>
          </section>
        </div>
      </div>
    </div>
  </AppLayout>
</template>
