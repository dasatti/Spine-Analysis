<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import AppLayout from '../components/AppLayout.vue'
import { usePatientsStore } from '../stores/patients'

const route = useRoute()
const router = useRouter()
const patientsStore = usePatientsStore()

const step = ref(1)
const patientId = ref(route.query.patient_id || '')
const patientSearch = ref('')
const searchError = ref('')
const hasSearched = ref(false)
const checklist = ref([false, false, false, false])
const cameraHeight = ref(115)
const cameraDistance = ref(250)
const captureDevice = ref('')
const patientReady = ref([false, false, false])

const steps = [
  'Environment Setup',
  'Camera Placement',
  'Patient Preparation',
  'Capture Poses',
  'Analysis',
]

const patient = computed(() => patientsStore.current)
const allChecked = computed(() => checklist.value.every(Boolean))
const showPatientPicker = computed(() => !patientId.value && step.value === 1)

onMounted(async () => {
  if (patientId.value) {
    await patientsStore.fetchOne(patientId.value)
    return
  }
  await loadPatients()
})

async function loadPatients() {
  searchError.value = ''
  try {
    const params = { page_size: 10, sort_by: 'last_name', sort_order: 'asc' }
    if (patientSearch.value.trim()) {
      params.search = patientSearch.value.trim()
      hasSearched.value = true
    } else {
      hasSearched.value = false
    }
    await patientsStore.fetchList(params)
  } catch (e) {
    searchError.value =
      e.response?.data?.message || e.response?.data?.detail || 'Could not load patients.'
    patientsStore.list = []
  }
}

async function selectPatient(id) {
  patientId.value = id
  searchError.value = ''
  await patientsStore.fetchOne(id)
}

function clearPatient() {
  patientId.value = ''
  patientsStore.current = null
  patientSearch.value = ''
  hasSearched.value = false
  loadPatients()
}

function nextStep() {
  if (step.value < 5) step.value++
  else finishSetup()
}

function prevStep() {
  if (step.value > 1) step.value--
}

function finishSetup() {
  if (!patientId.value) return
  sessionStorage.setItem(
    'scanSetup',
    JSON.stringify({
      patient_id: patientId.value,
      camera_height_cm: cameraHeight.value,
      camera_distance_cm: cameraDistance.value,
      capture_device: captureDevice.value,
    })
  )
  router.push(`/scans/${patientId.value}/capture`)
}

let searchTimer = null
watch(patientSearch, () => {
  if (searchTimer) clearTimeout(searchTimer)
  searchTimer = setTimeout(() => {
    loadPatients()
  }, 300)
})
</script>

<template>
  <AppLayout
    :title="patient ? `New Scan — ${patient.first_name} ${patient.last_name}` : 'New Scan Setup'"
    subtitle="5-step clinical capture wizard"
  >
    <div class="bg-surface-container-low border-b border-outline-variant px-margin-desktop py-4">
      <div class="max-w-5xl mx-auto flex items-center justify-between overflow-x-auto">
        <template v-for="(label, i) in steps" :key="label">
          <div
            :class="[
              'flex items-center gap-3 shrink-0',
              step === i + 1 ? '' : step > i + 1 ? '' : 'opacity-40',
            ]"
          >
            <div
              :class="[
                'w-8 h-8 rounded flex items-center justify-center font-bold font-metric-sm',
                step === i + 1
                  ? 'bg-primary text-on-primary'
                  : step > i + 1
                    ? 'bg-primary/20 text-primary border border-primary'
                    : 'border border-outline text-on-surface-variant',
              ]"
            >
              {{ i + 1 }}
            </div>
            <span
              :class="[
                'font-label-caps text-label-caps hidden sm:inline',
                step === i + 1 ? 'text-primary' : 'text-on-surface-variant',
              ]"
              >{{ label }}</span
            >
          </div>
          <div v-if="i < steps.length - 1" class="flex-1 mx-2 h-px bg-outline-variant relative min-w-[24px]">
            <div
              class="absolute left-0 top-0 h-full bg-primary transition-all duration-500"
              :style="{ width: step > i + 1 ? '100%' : step === i + 1 ? '50%' : '0' }"
            ></div>
          </div>
        </template>
      </div>
    </div>

    <div class="flex-1 overflow-y-auto custom-scrollbar p-margin-desktop">
      <div v-if="patientId && step === 1" class="max-w-xl mx-auto mb-8">
        <div
          class="flex items-center justify-between gap-4 px-4 py-3 bg-primary/10 border border-primary/30"
        >
          <div>
            <p class="font-label-caps text-[10px] text-on-surface-variant mb-1">SELECTED PATIENT</p>
            <p class="font-metric-sm text-primary">
              {{ patient ? `${patient.first_name} ${patient.last_name}` : 'Loading...' }}
            </p>
            <p v-if="patient?.medical_record_number" class="text-on-surface-variant text-xs mt-1">
              MRN: {{ patient.medical_record_number }}
            </p>
          </div>
          <button
            class="px-3 py-2 border border-outline-variant text-on-surface-variant font-label-caps text-[10px] hover:text-on-surface hover:border-primary-container"
            type="button"
            @click="clearPatient"
          >
            CHANGE
          </button>
        </div>
      </div>

      <div v-if="showPatientPicker" class="max-w-xl mx-auto mb-8">
        <h3 class="font-headline-md text-headline-md mb-4">Select Patient</h3>
        <div class="flex gap-2">
          <input
            v-model="patientSearch"
            class="flex-1 px-4 py-3 bg-[#0a0a0a] border border-outline-variant focus:border-primary-container outline-none font-metric-sm text-on-surface"
            placeholder="Search patient name or ID..."
            type="search"
            @keydown.enter.prevent="loadPatients"
          />
          <button
            class="px-4 py-3 bg-primary-container text-on-primary-container font-label-caps font-bold disabled:opacity-50"
            type="button"
            :disabled="patientsStore.loading"
            @click="loadPatients"
          >
            {{ patientsStore.loading ? '...' : 'SEARCH' }}
          </button>
        </div>
        <p v-if="searchError" class="text-error text-sm mt-3">{{ searchError }}</p>
        <p
          v-else-if="patientsStore.loading"
          class="text-on-surface-variant text-sm mt-3"
        >
          Searching patients...
        </p>
        <div v-else-if="patientsStore.list.length" class="mt-4 border border-outline-variant">
          <button
            v-for="p in patientsStore.list"
            :key="p.id"
            class="w-full text-left px-4 py-3 hover:bg-surface-container-high border-b border-outline-variant last:border-0"
            type="button"
            @click="selectPatient(p.id)"
          >
            <span class="font-metric-sm text-on-surface">{{ p.first_name }} {{ p.last_name }}</span>
            <span v-if="p.medical_record_number" class="text-on-surface-variant text-xs ml-2">
              · {{ p.medical_record_number }}
            </span>
          </button>
        </div>
        <p
          v-else-if="hasSearched || patientSearch.trim()"
          class="text-on-surface-variant text-sm mt-3"
        >
          No patients found. Try first name, last name, full name, or medical record number.
        </p>
        <p v-else class="text-on-surface-variant text-sm mt-3">
          No patients yet. Register a patient from the Patients screen first.
        </p>
      </div>

      <div v-if="step === 1" class="max-w-6xl mx-auto grid grid-cols-12 gap-gutter">
        <div class="col-span-12 lg:col-span-7 space-y-6">
          <div class="relative bg-surface-container border border-outline-variant overflow-hidden group">
            <div class="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-transparent z-10"></div>
            <div
              class="w-full aspect-video bg-cover bg-center"
              style="background-image: url('https://lh3.googleusercontent.com/aida-public/AB6AXuDtqme_4v9wi3XsGIpYAtun1xEF652P6RBLSsfoAeyt7JFcgtLaSrgzaMuVPWeM4XkJmumZiQueGNXoRraXKo2Xll9v-ZfndIpPSYBfLLwTJhb2R_bLvwJPZ6uas-Qjs8qgdmAMN_Rdi9ahpNMB4rb_FN8ZNL-LzU4b5irVTozn1OgGiVz3sGyB62bWryRn3O9mTCt1WfYzU85h5xa8womdqM7KotLWKpJDOpMDHZ43xZrIKytZDAg')"
            ></div>
            <div class="absolute bottom-6 left-6 z-20 max-w-sm">
              <p class="font-headline-md text-headline-md text-white mb-2">Ideal Scanning Zone</p>
              <p class="text-on-surface-variant text-body-sm">
                Ensure your diagnostic room mirrors this configuration to maintain
                <span class="text-primary font-bold">99.2% accuracy</span> for AI pose estimation.
              </p>
            </div>
          </div>
        </div>
        <div class="col-span-12 lg:col-span-5">
          <div class="bg-surface-container border border-outline-variant h-full flex flex-col">
            <div class="p-panel-padding bg-surface-container-high/50 border-b border-outline-variant">
              <h3 class="font-label-caps text-label-caps text-on-surface uppercase">
                Step 1 Checklist
              </h3>
              <h2 class="font-headline-lg text-on-surface mt-2">Environment Setup</h2>
            </div>
            <div class="flex-1 p-panel-padding space-y-4">
              <label
                v-for="(label, i) in [
                  'Room has bright, non-directional lighting',
                  'Plain, uncluttered background',
                  'No strong shadows or backlighting',
                  'Minimum 3m x 3m clear floor space',
                ]"
                :key="i"
                class="flex items-start gap-4 p-4 bg-surface-container-low border border-outline-variant cursor-pointer hover:bg-surface-container-high transition-colors"
              >
                <input v-model="checklist[i]" class="custom-checkbox mt-1" type="checkbox" />
                <span class="font-body-sm text-on-surface font-semibold">{{ label }}</span>
              </label>
            </div>
            <div class="p-panel-padding border-t border-outline-variant">
              <button
                class="w-full py-4 bg-primary text-on-primary font-bold uppercase tracking-widest text-label-caps hover:bg-primary-container transition-all disabled:opacity-30"
                :disabled="!allChecked || !patientId"
                type="button"
                @click="nextStep"
              >
                CONFIRM ENVIRONMENT
              </button>
            </div>
          </div>
        </div>
      </div>

      <div v-else-if="step === 2" class="max-w-3xl mx-auto space-y-6">
        <h2 class="font-headline-lg text-headline-lg flex items-center gap-3">
          <div class="spine-bar"></div>
          Camera Placement
        </h2>
        <div class="grid grid-cols-2 gap-stack-md">
          <div class="flex flex-col gap-2">
            <label class="font-label-caps text-label-caps text-on-surface-variant"
              >CAMERA HEIGHT (CM)</label
            >
            <input
              v-model.number="cameraHeight"
              class="w-full px-4 py-3 bg-[#0a0a0a] border border-outline-variant focus:border-primary-container outline-none font-metric-sm text-on-surface"
              type="number"
            />
          </div>
          <div class="flex flex-col gap-2">
            <label class="font-label-caps text-label-caps text-on-surface-variant"
              >DISTANCE FROM SUBJECT (CM)</label
            >
            <input
              v-model.number="cameraDistance"
              class="w-full px-4 py-3 bg-[#0a0a0a] border border-outline-variant focus:border-primary-container outline-none font-metric-sm text-on-surface"
              type="number"
            />
          </div>
          <div class="flex flex-col gap-2 col-span-2">
            <label class="font-label-caps text-label-caps text-on-surface-variant"
              >CAPTURE DEVICE</label
            >
            <input
              v-model="captureDevice"
              class="w-full px-4 py-3 bg-[#0a0a0a] border border-outline-variant focus:border-primary-container outline-none font-metric-sm text-on-surface"
              placeholder="Intel RealSense D435i"
              type="text"
            />
          </div>
        </div>
      </div>

      <div v-else-if="step === 3" class="max-w-3xl mx-auto space-y-4">
        <h2 class="font-headline-lg text-headline-lg flex items-center gap-3">
          <div class="spine-bar"></div>
          Patient Preparation
        </h2>
        <label
          v-for="(label, i) in [
            'Patient wearing form-fitting clothing',
            'Removed shoes and accessories',
            'Informed consent obtained',
          ]"
          :key="i"
          class="flex items-start gap-4 p-4 bg-surface-container border border-outline-variant cursor-pointer"
        >
          <input v-model="patientReady[i]" class="custom-checkbox mt-1" type="checkbox" />
          <span class="font-body-sm text-on-surface">{{ label }}</span>
        </label>
      </div>

      <div v-else-if="step === 4" class="max-w-3xl mx-auto text-center space-y-6">
        <h2 class="font-headline-lg text-headline-lg">Capture Poses</h2>
        <p class="text-on-surface-variant">
          You will capture Front, Side, Back, Adams, and optional Face views on the next screen.
        </p>
        <p class="font-metric-sm text-primary">
          Required views: Front · Side · Back · Adams
        </p>
      </div>

      <div v-else class="max-w-3xl mx-auto text-center space-y-6">
        <h2 class="font-headline-lg text-headline-lg">Ready for Analysis</h2>
        <p class="text-on-surface-variant">
          Proceed to capture frames. Analysis begins automatically after upload.
        </p>
        <button
          class="px-8 py-4 bg-primary-container text-on-primary-container font-bold font-label-caps"
          type="button"
          @click="finishSetup"
        >
          BEGIN CAPTURE
        </button>
      </div>

      <div v-if="step > 1 && step < 5" class="max-w-3xl mx-auto flex gap-4 mt-8">
        <button
          class="px-6 py-3 border border-outline-variant font-label-caps text-on-surface hover:bg-surface-container-high"
          type="button"
          @click="prevStep"
        >
          BACK
        </button>
        <button
          class="px-6 py-3 bg-primary text-on-primary font-bold font-label-caps hover:opacity-90"
          type="button"
          @click="nextStep"
        >
          CONTINUE
        </button>
      </div>
    </div>
  </AppLayout>
</template>

<style scoped>
.checkbox-container input:checked ~ .checkmark {
  background-color: #e8d600;
  border-color: #e8d600;
}
</style>
