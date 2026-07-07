<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { RouterLink, useRoute } from 'vue-router'
import AdminLayout from '../AdminLayout.vue'
import DigitalTwinViewer from '../../../components/DigitalTwinViewer.vue'
import FrameKeypointOverlay from '../../../components/FrameKeypointOverlay.vue'
import {
  getDatasetItem,
  recomputeDatasetItem,
  resetDatasetItemKeypoints,
} from '../../../api/client'
import { resolveTwinLandmarks } from '../../../utils/twinLandmarks'

const route = useRoute()

const loading = ref(true)
const item = ref(null)
const editMode = ref(false)
const workingLandmarks = ref([])
const dirty = ref(false)
const saving = ref(false)
const editError = ref('')
const undoArmed = ref(true)
const viewUndoStack = ref([])

const frameLandmarks = computed(
  () => item.value?.keypoints?.frame_landmarks || item.value?.keypoints?.landmarks || []
)
const displayLandmarks = computed(() =>
  editMode.value && workingLandmarks.value.length ? workingLandmarks.value : frameLandmarks.value
)
const adjustmentAudit = computed(() => item.value?.keypoints?.audit || null)
const twinLandmarks = computed(() => resolveTwinLandmarks(item.value?.keypoints))
const twinViewerKey = computed(
  () => `${item.value?.id || 'item'}-${adjustmentAudit.value?.adjusted_at || 'original'}`
)
const twinAdjusted = computed(() => Boolean(adjustmentAudit.value?.twin_rebuilt))
const poseView = computed(() => item.value?.pose_type || 'front')

const twinTabs = [
  { key: 'twin', label: 'Digital Twin' },
  { key: 'keypoints', label: 'Keypoints' },
]
const selectedTwinTab = ref('twin')

const keypointRows = computed(() =>
  displayLandmarks.value
    .filter((kp) => (kp.view || kp.source_view || poseView.value) === poseView.value)
    .slice()
    .sort((a, b) => a.name.localeCompare(b.name))
)

const canUndo = computed(() => viewUndoStack.value.length > 0)

function syncWorkingLandmarks() {
  workingLandmarks.value = JSON.parse(JSON.stringify(frameLandmarks.value || []))
  dirty.value = false
  viewUndoStack.value = []
  undoArmed.value = true
}

function viewOf(kp) {
  return kp.view || kp.source_view || poseView.value
}

function pushUndo() {
  const snapshot = workingLandmarks.value
    .filter((kp) => viewOf(kp) === poseView.value)
    .map((kp) => ({ ...kp }))
  viewUndoStack.value = [...viewUndoStack.value, snapshot].slice(-20)
}

function onUndoRequest() {
  if (!undoArmed.value) return
  pushUndo()
  undoArmed.value = false
}

function onDragEnd() {
  undoArmed.value = true
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

function undoView() {
  if (!viewUndoStack.value.length) return
  const snapshot = viewUndoStack.value.pop()
  const other = workingLandmarks.value.filter((kp) => viewOf(kp) !== poseView.value)
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
  if (!item.value || !dirty.value) return
  saving.value = true
  editError.value = ''
  try {
    const { data } = await recomputeDatasetItem(item.value.id, {
      frame_landmarks: workingLandmarks.value,
      preserve_manual_spine: true,
      refresh_synthetics: false,
    })
    item.value = data
    syncWorkingLandmarks()
    editMode.value = false
  } catch (e) {
    editError.value =
      e.response?.data?.message || e.response?.data?.detail?.message || 'Failed to save keypoints.'
  } finally {
    saving.value = false
  }
}

async function resetToDetected() {
  if (!item.value) return
  if (!window.confirm('Restore detector-original keypoints?')) return
  saving.value = true
  editError.value = ''
  try {
    const { data } = await resetDatasetItemKeypoints(item.value.id)
    item.value = data
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

function modelLabel(value) {
  if (value === 'spinepose_v2') return 'SpinePose'
  if (value === 'yolo_v8') return 'YOLO'
  return value
}

async function loadItem() {
  loading.value = true
  try {
    const { data } = await getDatasetItem(route.params.id)
    item.value = data
    syncWorkingLandmarks()
  } finally {
    loading.value = false
  }
}

watch(() => route.params.id, loadItem)
onMounted(loadItem)
</script>

<template>
  <AdminLayout
    :title="item ? `Adjust Keypoints — ${item.original_filename || item.id.slice(0, 8)}` : 'Adjust Keypoints'"
    subtitle="Dataset item review and manual correction"
  >
    <template #header-actions>
      <RouterLink
        to="/admin/research/dataset"
        class="px-4 py-2 border border-outline-variant text-on-surface-variant hover:text-on-surface font-label-caps text-[10px]"
      >
        BACK TO LIST
      </RouterLink>
    </template>

    <div v-if="loading" class="p-margin-desktop text-on-surface-variant">Loading dataset item...</div>
    <div v-else-if="item" class="p-gutter lg:px-margin-desktop space-y-stack-lg pb-margin-desktop">
      <div
        class="bg-surface-container border border-outline-variant p-panel-padding flex flex-wrap items-center justify-between gap-4"
      >
        <div>
          <p class="font-label-caps text-on-surface-variant text-[10px] mb-1">ITEM ID</p>
          <p class="font-metric-sm text-primary">{{ item.id.slice(0, 8).toUpperCase() }}</p>
        </div>
        <div>
          <p class="font-label-caps text-on-surface-variant text-[10px] mb-1">POSE</p>
          <p class="font-metric-sm capitalize">{{ item.pose_type }}</p>
        </div>
        <div>
          <p class="font-label-caps text-on-surface-variant text-[10px] mb-1">MODEL</p>
          <p class="font-metric-sm">{{ modelLabel(item.detector_model) }}</p>
        </div>
        <div>
          <p class="font-label-caps text-on-surface-variant text-[10px] mb-1">CREATED</p>
          <p class="font-metric-sm">{{ formatDate(item.created_at) }}</p>
        </div>
      </div>

      <div
        v-if="item.keypoints_adjusted || adjustmentAudit?.adjusted_at"
        class="bg-primary-container/20 border border-primary-container p-4 text-sm"
      >
        <p class="font-label-caps text-primary text-[10px] mb-1">MANUALLY ADJUSTED</p>
        <p class="text-on-surface-variant">
          Keypoints were corrected
          <span v-if="adjustmentAudit?.adjusted_at"> on {{ formatDate(adjustmentAudit.adjusted_at) }}</span>.
        </p>
      </div>

      <div v-if="item.status === 'failed'" class="bg-error-container/20 border border-error p-4">
        <p class="text-error font-label-caps">Processing failed</p>
        <p class="text-on-surface-variant text-sm mt-2">{{ item.inference_error }}</p>
      </div>

      <div v-if="item.status === 'ready'" class="grid grid-cols-12 gap-gutter items-start">
        <section class="col-span-12 lg:col-span-5 space-y-stack-lg">
          <div class="space-y-4">
            <div class="flex flex-wrap items-center justify-between gap-3">
              <h3 class="font-label-caps text-primary">Annotated Image — {{ item.pose_type }}</h3>
              <div class="flex flex-wrap items-center gap-2">
                <button
                  v-if="editMode && (item.keypoints_adjusted || adjustmentAudit?.original_frame_landmarks)"
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

            <div v-if="editMode && canUndo" class="flex justify-end">
              <button
                class="px-3 py-1.5 font-label-caps text-[10px] border border-outline-variant text-on-surface-variant hover:text-on-surface"
                type="button"
                @click="undoView"
              >
                UNDO
              </button>
            </div>

            <div
              v-if="editMode"
              class="flex flex-wrap items-center gap-4 p-3 bg-surface-container border border-outline-variant text-xs"
            >
              <p class="text-on-surface-variant font-label-caps text-[10px]">
                Drag keypoints to adjust — spine points show a yellow ring.
              </p>
              <button
                class="px-4 py-2 bg-primary text-on-primary font-label-caps text-[10px] font-bold hover:opacity-90 disabled:opacity-40"
                type="button"
                :disabled="!dirty || saving"
                @click="saveAndRegenerate"
              >
                {{ saving ? 'SAVING...' : 'SAVE & REGENERATE' }}
              </button>
              <span v-if="dirty" class="text-primary font-label-caps text-[10px]">Unsaved changes</span>
            </div>
            <p v-if="editError" class="text-error text-xs">{{ editError }}</p>

            <FrameKeypointOverlay
              :image-url="item.image_url"
              :landmarks="displayLandmarks"
              :view="poseView"
              :edit-mode="editMode"
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
              Digital twin rebuilt from adjusted keypoints.
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
              :view="poseView === 'side' ? 'side' : poseView === 'back' ? 'back' : 'front'"
            />

            <div v-else class="bg-surface-container border border-outline-variant max-h-[420px] overflow-y-auto">
              <table class="w-full text-sm">
                <thead class="sticky top-0 bg-surface-container">
                  <tr class="font-label-caps text-[10px] text-on-surface-variant border-b border-outline-variant">
                    <th class="text-left px-4 py-3">Keypoint</th>
                    <th class="text-right px-4 py-3">X (px)</th>
                    <th class="text-right px-4 py-3">Y (px)</th>
                    <th class="text-right px-4 py-3">Conf.</th>
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
                      {{ ((kp.confidence ?? 0) * 100).toFixed(0) }}%
                    </td>
                  </tr>
                  <tr v-if="!keypointRows.length">
                    <td colspan="4" class="px-4 py-6 text-center text-on-surface-variant">
                      No keypoints for this pose
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </section>

        <section class="col-span-12 lg:col-span-7">
          <h3 class="font-label-caps text-primary mb-4">Detected Keypoints</h3>
          <div class="bg-surface-container border border-outline-variant">
            <div class="max-h-[720px] overflow-y-auto">
              <table class="w-full text-sm">
                <thead class="sticky top-0 bg-[#1A1A1A]">
                  <tr class="font-label-caps text-[10px] text-on-surface-variant border-b border-outline-variant">
                    <th class="text-left px-4 py-3">Keypoint</th>
                    <th class="text-right px-4 py-3">X (px)</th>
                    <th class="text-right px-4 py-3">Y (px)</th>
                    <th class="text-right px-4 py-3">Confidence</th>
                  </tr>
                </thead>
                <tbody>
                  <tr
                    v-for="(kp, i) in keypointRows"
                    :key="`full-${kp.name}-${i}`"
                    class="border-b border-outline-variant/40 hover:bg-surface-container-high"
                  >
                    <td class="px-4 py-2 font-medium">{{ kp.name }}</td>
                    <td class="px-4 py-2 text-right font-mono">{{ kp.x?.toFixed(1) }}</td>
                    <td class="px-4 py-2 text-right font-mono">{{ kp.y?.toFixed(1) }}</td>
                    <td class="px-4 py-2 text-right font-mono">
                      {{ ((kp.confidence ?? 0) * 100).toFixed(1) }}%
                    </td>
                  </tr>
                  <tr v-if="!keypointRows.length">
                    <td colspan="4" class="px-4 py-8 text-center text-on-surface-variant">
                      No keypoints detected
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
              </li>
            </ul>
          </div>
        </section>
      </div>
    </div>
  </AdminLayout>
</template>
