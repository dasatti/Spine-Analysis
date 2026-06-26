<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'
import { usePatientsStore } from '../stores/patients'
import { useScansStore } from '../stores/scans'

const route = useRoute()
const router = useRouter()
const patientsStore = usePatientsStore()
const scansStore = useScansStore()

const patientId = computed(() => route.params.id)
const patient = computed(() => patientsStore.current)
const currentPose = ref(0)
const submitting = ref(false)
const error = ref('')

const poses = [
  { key: 'front', label: 'Front View', field: 'frame_front' },
  { key: 'side', label: 'Side View', field: 'frame_side' },
  { key: 'back', label: 'Back View', field: 'frame_back' },
  { key: 'adams', label: 'Adams View', field: 'frame_adams' },
  { key: 'face', label: 'Face View (optional)', field: 'frame_face', optional: true },
]

const files = ref({})
const previewUrls = ref({})
const setup = ref(null)

const initials = computed(() => {
  if (!patient.value) return '??'
  return `${patient.value.first_name[0]}${patient.value.last_name[0]}`.toUpperCase()
})

const ALLOWED_TYPES = new Set([
  'image/png',
  'image/jpeg',
  'image/pjpeg',
  'image/tiff',
  'image/tif',
  'image/x-tiff',
])
const ALLOWED_EXTENSIONS = ['.png', '.jpg', '.jpeg', '.jpe', '.tif', '.tiff']

function isAllowedFrame(file) {
  const ext = file.name.includes('.') ? `.${file.name.split('.').pop().toLowerCase()}` : ''
  const type = (file.type || '').toLowerCase()
  if (ALLOWED_EXTENSIONS.includes(ext)) return true
  if (type && ALLOWED_TYPES.has(type)) return true
  // Some Windows builds leave type empty for JPEG — trust extension only
  return Boolean(ext) && ALLOWED_EXTENSIONS.includes(ext)
}

const currentField = computed(() => poses[currentPose.value].field)
const currentPreviewUrl = computed(() => previewUrls.value[currentField.value] || null)
const currentFile = computed(() => files.value[currentField.value] || null)

function setPreviewUrl(field, file) {
  if (previewUrls.value[field]) {
    URL.revokeObjectURL(previewUrls.value[field])
  }
  if (file) {
    previewUrls.value = { ...previewUrls.value, [field]: URL.createObjectURL(file) }
  } else {
    const next = { ...previewUrls.value }
    delete next[field]
    previewUrls.value = next
  }
}

function revokeAllPreviewUrls() {
  Object.values(previewUrls.value).forEach((url) => URL.revokeObjectURL(url))
  previewUrls.value = {}
}

function onFileChange(field, event) {
  const file = event.target.files?.[0]
  if (!file) return
  if (!isAllowedFrame(file)) {
    error.value = 'Please upload a PNG, JPEG, or TIFF image.'
    event.target.value = ''
    return
  }
  error.value = ''
  files.value[field] = file
  setPreviewUrl(field, file)
}

const canSubmit = computed(() =>
  ['frame_front', 'frame_side', 'frame_back', 'frame_adams'].every((f) => files.value[f])
)

async function submitScan() {
  if (!canSubmit.value || !patient.value) return
  error.value = ''
  submitting.value = true
  const formData = new FormData()
  formData.append('patient_id', patientId.value)
  formData.append('patient_height_cm', patient.value.height_cm)
  formData.append('patient_weight_kg', patient.value.weight_kg)
  if (setup.value?.camera_height_cm)
    formData.append('camera_height_cm', setup.value.camera_height_cm)
  if (setup.value?.camera_distance_cm)
    formData.append('camera_distance_cm', setup.value.camera_distance_cm)
  if (setup.value?.capture_device) formData.append('capture_device', setup.value.capture_device)
  for (const pose of poses) {
    if (files.value[pose.field]) formData.append(pose.field, files.value[pose.field])
  }
  try {
    const scan = await scansStore.createScan(formData)
    sessionStorage.removeItem('scanSetup')
    router.push(`/scans/${scan.id}/processing`)
  } catch (e) {
    error.value = e.response?.data?.detail || 'Failed to create scan.'
  } finally {
    submitting.value = false
  }
}

onMounted(async () => {
  const raw = sessionStorage.getItem('scanSetup')
  if (raw) setup.value = JSON.parse(raw)
  await patientsStore.fetchOne(patientId.value)
})

onUnmounted(revokeAllPreviewUrls)
</script>

<template>
  <div class="bg-surface-container-lowest text-on-surface font-body-sm overflow-hidden h-screen flex flex-col">
    <header
      class="h-16 flex items-center justify-between px-8 bg-surface-container-lowest border-b border-outline-variant z-50"
    >
      <div class="flex items-center gap-6">
        <div class="flex items-center gap-3">
          <div
            class="w-8 h-8 rounded-full bg-primary-container flex items-center justify-center text-on-primary-container font-bold"
          >
            {{ initials }}
          </div>
          <div v-if="patient">
            <h1 class="font-headline-md text-[16px] leading-tight uppercase tracking-tight">
              {{ patient.first_name }} {{ patient.last_name }}
            </h1>
            <p class="font-label-caps text-[10px] text-on-surface-variant">
              {{ patient.medical_record_number || patientId.slice(0, 8) }}
            </p>
          </div>
        </div>
        <div class="h-8 w-px bg-outline-variant"></div>
        <div class="flex items-center gap-2">
          <div class="w-1.5 h-5 bg-primary-container"></div>
          <span class="font-label-caps text-on-surface">
            Pose {{ currentPose + 1 }} of {{ poses.length }} —
            {{ poses[currentPose].label }}
          </span>
        </div>
      </div>
      <RouterLink
        to="/scans/new"
        class="w-10 h-10 flex items-center justify-center rounded border border-outline-variant hover:bg-surface-container-high transition-colors"
      >
        <span class="material-symbols-outlined text-on-surface">close</span>
      </RouterLink>
    </header>

    <main class="flex-1 flex overflow-hidden">
      <section
        class="flex-1 relative bg-black overflow-hidden flex items-center justify-center border-r border-outline-variant"
      >
        <img
          v-if="currentPreviewUrl"
          :src="currentPreviewUrl"
          :alt="`${poses[currentPose].label} preview`"
          class="absolute inset-0 w-full h-full object-contain bg-black"
        />
        <div class="absolute inset-0 scan-overlay-grid pointer-events-none opacity-20"></div>
        <div
          v-if="!currentPreviewUrl"
          class="relative z-10 text-center p-8 max-w-lg"
        >
          <span class="material-symbols-outlined text-primary text-6xl mb-4">upload_file</span>
          <p class="font-headline-md text-headline-md mb-2">{{ poses[currentPose].label }}</p>
          <p class="text-on-surface-variant text-sm mb-6">
            Upload RGBD frame (PNG, JPEG, or TIFF) for this pose
          </p>
          <label
            class="inline-flex items-center gap-2 px-6 py-3 bg-primary-container text-on-primary-container font-label-caps cursor-pointer hover:opacity-90"
          >
            <span class="material-symbols-outlined">folder_open</span>
            SELECT FILE
            <input
              :key="poses[currentPose].field"
              class="hidden"
              type="file"
              @change="onFileChange(poses[currentPose].field, $event)"
            />
          </label>
        </div>
        <div
          v-else
          class="absolute bottom-6 left-1/2 -translate-x-1/2 z-20 flex flex-col items-center gap-3"
        >
          <p class="font-metric-sm text-primary bg-black/70 px-4 py-2 border border-primary/30">
            ✓ {{ currentFile?.name }}
          </p>
          <label
            class="inline-flex items-center gap-2 px-4 py-2 bg-surface-container-high/90 border border-outline-variant text-on-surface font-label-caps text-[11px] cursor-pointer hover:border-primary-container"
          >
            <span class="material-symbols-outlined text-sm">swap_horiz</span>
            CHANGE FILE
            <input
              :key="`${poses[currentPose].field}-replace`"
              class="hidden"
              type="file"
              @change="onFileChange(poses[currentPose].field, $event)"
            />
          </label>
        </div>
        <div class="absolute top-4 left-4 w-12 h-12 border-t-2 border-l-2 border-primary/40 z-10"></div>
        <div class="absolute top-4 right-4 w-12 h-12 border-t-2 border-r-2 border-primary/40 z-10"></div>
        <div class="absolute bottom-4 left-4 w-12 h-12 border-b-2 border-l-2 border-primary/40 z-10"></div>
        <div class="absolute bottom-4 right-4 w-12 h-12 border-b-2 border-r-2 border-primary/40 z-10"></div>
      </section>

      <aside class="w-[320px] bg-surface border-l border-outline-variant flex flex-col">
        <div class="p-6 border-b border-outline-variant bg-surface-container">
          <h2 class="font-label-caps text-on-surface-variant mb-1">SCAN PROGRESS</h2>
          <div class="flex items-center justify-between">
            <span class="font-metric-lg text-primary"
              >{{ Object.keys(files).length }}/{{ poses.length }}</span
            >
            <span class="font-label-caps text-[10px] text-on-surface-variant">POSES</span>
          </div>
        </div>
        <div class="flex-1 p-4 space-y-2 overflow-y-auto">
          <button
            v-for="(pose, i) in poses"
            :key="pose.key"
            :class="[
              'w-full text-left p-3 border transition-colors flex items-center gap-3',
              currentPose === i
                ? 'border-primary bg-primary/10 active-scan-border'
                : 'border-outline-variant hover:bg-surface-container-high',
              files[pose.field] ? 'text-primary' : 'text-on-surface-variant',
            ]"
            type="button"
            @click="currentPose = i"
          >
            <img
              v-if="previewUrls[pose.field]"
              :src="previewUrls[pose.field]"
              :alt="pose.label"
              class="w-10 h-10 object-cover border border-outline-variant shrink-0"
            />
            <div
              v-else
              class="w-10 h-10 border border-dashed border-outline-variant shrink-0 flex items-center justify-center"
            >
              <span class="material-symbols-outlined text-sm opacity-40">image</span>
            </div>
            <span class="font-label-caps text-[11px] flex-1">{{ pose.label }}</span>
            <span v-if="files[pose.field]" class="material-symbols-outlined text-sm">check_circle</span>
          </button>
        </div>
        <div class="p-4 border-t border-outline-variant space-y-3">
          <p v-if="error" class="text-error text-xs">{{ error }}</p>
          <button
            class="w-full py-4 bg-primary text-on-primary font-bold font-label-caps tracking-widest hover:opacity-90 disabled:opacity-30"
            :disabled="!canSubmit || submitting"
            type="button"
            @click="submitScan"
          >
            {{ submitting ? 'UPLOADING...' : 'SUBMIT & ANALYSE' }}
          </button>
        </div>
      </aside>
    </main>
  </div>
</template>

<style scoped>
.scan-overlay-grid {
  background-image: radial-gradient(circle, rgba(232, 214, 0, 0.1) 1px, transparent 1px);
  background-size: 40px 40px;
}
@keyframes pulse-border {
  0% {
    border-color: rgba(232, 214, 0, 0.4);
  }
  50% {
    border-color: rgba(232, 214, 0, 1);
  }
  100% {
    border-color: rgba(232, 214, 0, 0.4);
  }
}
.active-scan-border {
  animation: pulse-border 2s infinite;
}
</style>
