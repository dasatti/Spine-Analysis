<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { RouterLink, useRoute } from 'vue-router'
import AppLayout from '../components/AppLayout.vue'
import DigitalTwinViewer from '../components/DigitalTwinViewer.vue'
import FrameKeypointOverlay from '../components/FrameKeypointOverlay.vue'
import RiskLevelBadge from '../components/RiskLevelBadge.vue'
import ScanMetricsPanel from '../components/ScanMetricsPanel.vue'
import ScanStatusBadge from '../components/ScanStatusBadge.vue'
import { useScansStore } from '../stores/scans'
import { resolveTwinLandmarks } from '../utils/twinLandmarks'

const route = useRoute()
const scansStore = useScansStore()

const scan = computed(() => scansStore.current)
const patientName = computed(() =>
  scan.value?.patient ? `${scan.value.patient.first_name} ${scan.value.patient.last_name}` : ''
)

const editMode = ref(false)
const workingLandmarks = ref([])
const dirty = ref(false)
const saving = ref(false)
const editError = ref('')
const undoArmed = ref({
  front: true,
  side: true,
  back: true,
  upper_body: true,
  adams: true,
  face: true,
})
const viewUndoStacks = ref({
  front: [],
  side: [],
  back: [],
  upper_body: [],
  adams: [],
  face: [],
})

const ALL_FRAME_VIEWS = [
  { key: 'front', label: 'Front' },
  { key: 'side', label: 'Side' },
  { key: 'back', label: 'Back' },
  { key: 'upper_body', label: 'Upper Body (Side View)' },
  { key: 'adams', label: 'Adams' },
  { key: 'face', label: 'Face' },
]
const selectedFrameView = ref('front')

const frameViews = computed(() => {
  const urls = scan.value?.frame_urls || {}
  return ALL_FRAME_VIEWS.filter((view) => urls[view.key])
})

const frameLandmarks = computed(
  () => scan.value?.keypoints?.frame_landmarks || scan.value?.keypoints?.landmarks || []
)
const displayLandmarks = computed(() =>
  editMode.value && workingLandmarks.value.length ? workingLandmarks.value : frameLandmarks.value
)
const adjustmentAudit = computed(() => scan.value?.keypoints?.audit || null)
const twinLandmarks = computed(() => resolveTwinLandmarks(scan.value?.keypoints))
const twinViewerKey = computed(
  () => `${scan.value?.id || 'scan'}-${adjustmentAudit.value?.adjusted_at || 'original'}`
)
const twinAdjusted = computed(() => Boolean(adjustmentAudit.value?.twin_rebuilt))

const twinTabs = [
  { key: 'twin', label: 'Digital Twin' },
  { key: 'keypoints', label: 'Keypoints' },
]
const selectedTwinTab = ref('twin')
const keypointViewFilter = ref('front')

const keypointRows = computed(() =>
  displayLandmarks.value
    .filter((kp) => (kp.view || kp.source_view || 'front') === keypointViewFilter.value)
    .slice()
    .sort((a, b) => a.name.localeCompare(b.name))
)

const currentFrameUrl = computed(
  () => scan.value?.frame_urls?.[selectedFrameView.value] || null
)

const scoliosisDetectionOverlay = computed(() => {
  const metric = scan.value?.metrics?.ai_classification?.scoliosis
  if (!metric?.detections?.length) return null
  return {
    boxes: metric.detections,
    imageWidth: metric.image_width,
    imageHeight: metric.image_height,
  }
})

const activeDetectionBoxes = computed(() =>
  selectedFrameView.value === 'back' ? scoliosisDetectionOverlay.value?.boxes || [] : []
)

const activeDetectionImageSize = computed(() =>
  selectedFrameView.value === 'back' ? scoliosisDetectionOverlay.value : null
)

const canUndoView = computed(
  () => (viewUndoStacks.value[selectedFrameView.value] || []).length > 0
)

function syncWorkingLandmarks() {
  workingLandmarks.value = JSON.parse(JSON.stringify(frameLandmarks.value || []))
  dirty.value = false
  for (const view of Object.keys(viewUndoStacks.value)) {
    viewUndoStacks.value[view] = []
    undoArmed.value[view] = true
  }
}

function viewOf(kp) {
  return kp.view || kp.source_view || 'front'
}

function pushViewUndo(view) {
  const snapshot = workingLandmarks.value
    .filter((kp) => viewOf(kp) === view)
    .map((kp) => ({ ...kp }))
  viewUndoStacks.value[view] = [...(viewUndoStacks.value[view] || []), snapshot].slice(-20)
}

function onUndoRequest(view) {
  if (!undoArmed.value[view]) return
  pushViewUndo(view)
  undoArmed.value[view] = false
}

function onDragEnd(view) {
  undoArmed.value[view] = true
}

function onLandmarkMove({ name, x, y, view }) {
  const idx = workingLandmarks.value.findIndex(
    (kp) => kp.name === name && viewOf(kp) === view
  )
  if (idx === -1) return
  workingLandmarks.value[idx] = {
    ...workingLandmarks.value[idx],
    x,
    y,
    confidence: Math.max(workingLandmarks.value[idx].confidence ?? 0.9, 0.9),
  }
  workingLandmarks.value = [...workingLandmarks.value]
  dirty.value = true
  editError.value = ''
}

function undoCurrentView() {
  const view = selectedFrameView.value
  const stack = viewUndoStacks.value[view] || []
  if (!stack.length) return
  const snapshot = stack.pop()
  const other = workingLandmarks.value.filter((kp) => viewOf(kp) !== view)
  workingLandmarks.value = [...other, ...snapshot.map((kp) => ({ ...kp }))]
  dirty.value = true
}

function toggleEditMode() {
  if (editMode.value) {
    if (dirty.value && !window.confirm('Discard unsaved keypoint changes?')) return
    editMode.value = false
    syncWorkingLandmarks()
    return
  }
  syncWorkingLandmarks()
  editMode.value = true
}

async function saveAndRegenerate() {
  if (!scan.value || !dirty.value) return
  saving.value = true
  editError.value = ''
  try {
    await scansStore.recomputeScan(scan.value.id, {
      frame_landmarks: workingLandmarks.value,
      preserve_manual_spine: true,
      refresh_synthetics: false,
    })
    syncWorkingLandmarks()
    editMode.value = false
  } catch (e) {
    editError.value = e.response?.data?.message || e.response?.data?.detail?.message || 'Failed to regenerate metrics.'
  } finally {
    saving.value = false
  }
}

async function resetToDetected() {
  if (!scan.value) return
  if (!window.confirm('Restore detector-original keypoints and regenerate metrics?')) return
  saving.value = true
  editError.value = ''
  try {
    await scansStore.resetScanKeypoints(scan.value.id)
    syncWorkingLandmarks()
    editMode.value = false
  } catch (e) {
    editError.value = e.response?.data?.message || 'Failed to reset keypoints.'
  } finally {
    saving.value = false
  }
}

function formatDate(iso) {
  if (!iso) return '—'
  return new Date(iso).toLocaleString('en-GB', {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

watch(
  frameViews,
  (views) => {
    if (!views.length) return
    if (!views.some((view) => view.key === selectedFrameView.value)) {
      selectedFrameView.value = views[0].key
      keypointViewFilter.value = views[0].key
    }
  },
  { immediate: true }
)

watch(
  () => scan.value?.id,
  () => {
    if (scan.value?.status === 'completed') syncWorkingLandmarks()
  }
)

onMounted(async () => {
  await scansStore.fetchScan(route.params.id)
  syncWorkingLandmarks()
})
</script>

<template>
  <AppLayout
    :title="scan ? `Scan Results — ${patientName}` : 'Scan Results'"
    subtitle="Posture metrics and digital twin"
  >
    <template #header-actions>
      <div v-if="scan" class="flex items-center gap-4 flex-wrap">
        <ScanStatusBadge :status="scan.status" />
        <RouterLink
          v-if="scan.status === 'completed'"
          :to="`/scans/${scan.id}/export`"
          class="px-4 py-2 bg-primary-container text-on-primary-container font-label-caps text-[10px] font-bold hover:opacity-90"
        >
          EXPORT REPORT
        </RouterLink>
      </div>
    </template>

    <div v-if="scansStore.loading" class="p-margin-desktop text-on-surface-variant">
      Loading scan results...
    </div>
    <div v-else-if="scan" class="p-gutter lg:px-margin-desktop space-y-stack-lg pb-margin-desktop">
      <div
        class="bg-surface-container border border-outline-variant p-panel-padding flex flex-wrap items-center justify-between gap-4"
      >
        <div>
          <p class="font-label-caps text-on-surface-variant text-[10px] mb-1">SCAN ID</p>
          <p class="font-metric-sm text-primary">{{ scan.id.slice(0, 8).toUpperCase() }}</p>
        </div>
        <div>
          <p class="font-label-caps text-on-surface-variant text-[10px] mb-1">CAPTURED</p>
          <p class="font-metric-sm">{{ formatDate(scan.created_at) }}</p>
        </div>
        <div>
          <p class="font-label-caps text-on-surface-variant text-[10px] mb-1">DETECTOR</p>
          <p class="font-metric-sm">{{ scan.detector_model }}</p>
        </div>
        <div v-if="scan.overall_risk">
          <p class="font-label-caps text-on-surface-variant text-[10px] mb-1">OVERALL RISK</p>
          <RiskLevelBadge :level="scan.overall_risk" />
        </div>
      </div>

      <div
        v-if="scan.keypoints_adjusted || adjustmentAudit?.adjusted_at"
        class="bg-primary-container/20 border border-primary-container p-4 text-sm"
      >
        <p class="font-label-caps text-primary text-[10px] mb-1">MANUALLY ADJUSTED</p>
        <p class="text-on-surface-variant">
          Keypoints were corrected by a clinician
          <span v-if="adjustmentAudit?.adjusted_at">
            on {{ formatDate(adjustmentAudit.adjusted_at) }}
          </span>.
          Exported reports reflect the adjusted measurements.
        </p>
      </div>

      <div v-if="scan.status === 'failed'" class="bg-error-container/20 border border-error p-4">
        <p class="text-error font-label-caps">Analysis failed</p>
        <p class="text-on-surface-variant text-sm mt-2">{{ scan.error_message }}</p>
      </div>

      <div v-if="scan.status === 'completed'" class="grid grid-cols-12 gap-gutter items-start">
        <section class="col-span-12 lg:col-span-5 space-y-stack-lg">
          <div class="space-y-4">
            <h3 class="font-label-caps text-primary">Annotated Capture Frames</h3>

            <div class="flex flex-wrap items-center justify-between gap-3">
              <div class="flex flex-wrap gap-2">
                <button
                  v-for="view in frameViews"
                  :key="view.key"
                  :class="[
                    'px-4 py-2 font-label-caps text-[10px] border transition-colors',
                    selectedFrameView === view.key
                      ? 'bg-primary-container text-on-primary-container border-primary-container'
                      : 'border-outline-variant text-on-surface-variant hover:text-on-surface',
                  ]"
                  type="button"
                  @click="selectedFrameView = view.key"
                >
                  {{ view.label }}
                </button>
              </div>
              <div class="flex flex-wrap items-center gap-2 shrink-0">
                <button
                  v-if="editMode && (scan.keypoints_adjusted || adjustmentAudit?.original_frame_landmarks)"
                  class="px-3 py-1.5 font-label-caps text-[10px] border border-outline-variant text-on-surface-variant hover:text-on-surface"
                  type="button"
                  :disabled="saving"
                  @click="resetToDetected"
                >
                  RESET ALL
                </button>
                <button
                  :class="[
                    'px-4 py-2 font-label-caps text-[10px] font-bold border transition-colors',
                    editMode
                      ? 'bg-primary text-on-primary border-primary'
                      : 'bg-surface-container-high text-on-surface border-outline-variant hover:border-primary-container',
                  ]"
                  type="button"
                  @click="toggleEditMode"
                >
                  {{ editMode ? 'EXIT EDIT MODE' : 'ADJUST KEYPOINTS' }}
                </button>
              </div>
            </div>

            <div v-if="editMode && canUndoView" class="flex flex-wrap items-center justify-end gap-2">
              <button
                class="px-3 py-1.5 font-label-caps text-[10px] border border-outline-variant text-on-surface-variant hover:text-on-surface"
                type="button"
                @click="undoCurrentView"
              >
                UNDO VIEW
              </button>
            </div>

            <div
              v-if="editMode"
              class="flex flex-wrap items-center gap-4 p-3 bg-surface-container border border-outline-variant text-xs"
            >
              <p class="text-on-surface-variant font-label-caps text-[10px]">
                Drag any keypoint — body joints and spine vertebrae (yellow ring).
              </p>
              <button
                class="px-4 py-2 bg-primary text-on-primary font-label-caps text-[10px] font-bold hover:opacity-90 disabled:opacity-40"
                type="button"
                :disabled="!dirty || saving"
                @click="saveAndRegenerate"
              >
                {{ saving ? 'REGENERATING...' : 'SAVE & REGENERATE' }}
              </button>
              <span v-if="dirty" class="text-primary font-label-caps text-[10px]">Unsaved changes</span>
            </div>
            <p v-if="editError" class="text-error text-xs">{{ editError }}</p>

            <FrameKeypointOverlay
              :image-url="currentFrameUrl"
              :landmarks="displayLandmarks"
              :view="selectedFrameView"
              :edit-mode="editMode"
              :detection-boxes="activeDetectionBoxes"
              :detection-image-size="activeDetectionImageSize"
              @landmark-move="onLandmarkMove"
              @undo-request="onUndoRequest"
              @drag-end="onDragEnd"
            />
          </div>
          <div>
            <h3 class="font-label-caps text-primary mb-4">Digital Twin</h3>
            <div
              v-if="twinAdjusted"
              class="mb-3 text-xs text-on-surface-variant border border-outline-variant p-3"
            >
              Digital twin rebuilt from adjusted keypoints after manual correction.
            </div>
            <div class="flex gap-2 mb-4">
              <button
                v-for="tab in twinTabs"
                :key="tab.key"
                :class="[
                  'px-4 py-2 font-label-caps text-[10px] border transition-colors',
                  selectedTwinTab === tab.key
                    ? 'bg-primary-container text-on-primary-container border-primary-container'
                    : 'border-outline-variant text-on-surface-variant hover:text-on-surface',
                ]"
                type="button"
                @click="selectedTwinTab = tab.key"
              >
                {{ tab.label }}
              </button>
            </div>

            <DigitalTwinViewer
              v-if="selectedTwinTab === 'twin'"
              :key="twinViewerKey"
              :landmarks="twinLandmarks"
            />

            <div v-else class="bg-surface-container border border-outline-variant">
              <div class="flex flex-wrap gap-2 p-4 border-b border-outline-variant">
                <button
                  v-for="view in frameViews"
                  :key="view.key"
                  :class="[
                    'px-3 py-1.5 font-label-caps text-[10px] border transition-colors',
                    keypointViewFilter === view.key
                      ? 'bg-primary-container text-on-primary-container border-primary-container'
                      : 'border-outline-variant text-on-surface-variant hover:text-on-surface',
                  ]"
                  type="button"
                  @click="keypointViewFilter = view.key"
                >
                  {{ view.label }}
                </button>
              </div>
              <div class="max-h-[420px] overflow-y-auto">
                <table class="w-full text-sm">
                  <thead class="sticky top-0 bg-surface-container">
                    <tr
                      class="font-label-caps text-[10px] text-on-surface-variant border-b border-outline-variant"
                    >
                      <th class="text-left px-4 py-3">Keypoint</th>
                      <th class="text-right px-4 py-3">X (px)</th>
                      <th class="text-right px-4 py-3">Y (px)</th>
                      <th class="text-right px-4 py-3">Confidence</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr
                      v-for="(kp, i) in keypointRows"
                      :key="`${kp.name}-${i}`"
                      class="border-b border-outline-variant/40"
                    >
                      <td class="px-4 py-2">{{ kp.name }}</td>
                      <td class="px-4 py-2 text-right font-mono">{{ kp.x?.toFixed(1) }}</td>
                      <td class="px-4 py-2 text-right font-mono">{{ kp.y?.toFixed(1) }}</td>
                      <td class="px-4 py-2 text-right font-mono">
                        {{ ((kp.confidence ?? 0) * 100).toFixed(1) }}%
                      </td>
                    </tr>
                    <tr v-if="!keypointRows.length">
                      <td colspan="4" class="px-4 py-6 text-center text-on-surface-variant">
                        No keypoints detected for this view
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>

            <div
              v-if="adjustmentAudit?.history?.length"
              class="mt-4 bg-surface-container border border-outline-variant p-4"
            >
              <h4 class="font-label-caps text-[10px] text-on-surface-variant mb-2">Adjustment history</h4>
              <ul class="space-y-1 text-xs text-on-surface-variant max-h-32 overflow-y-auto">
                <li v-for="(entry, i) in [...adjustmentAudit.history].reverse()" :key="i">
                  {{ entry.action }} — {{ formatDate(entry.at) }}
                  <span v-if="entry.note"> ({{ entry.note }})</span>
                </li>
              </ul>
            </div>
          </div>
        </section>
        <section class="col-span-12 lg:col-span-7">
          <h3 class="font-label-caps text-primary mb-4">Posture Metrics</h3>
          <ScanMetricsPanel :metrics="scan.metrics" />
        </section>
      </div>
    </div>
  </AppLayout>
</template>
