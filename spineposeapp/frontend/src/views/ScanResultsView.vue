<script setup>
import { computed, onMounted, ref } from 'vue'
import { RouterLink, useRoute } from 'vue-router'
import AppLayout from '../components/AppLayout.vue'
import DigitalTwinViewer from '../components/DigitalTwinViewer.vue'
import FrameKeypointOverlay from '../components/FrameKeypointOverlay.vue'
import RiskLevelBadge from '../components/RiskLevelBadge.vue'
import ScanMetricsPanel from '../components/ScanMetricsPanel.vue'
import ScanStatusBadge from '../components/ScanStatusBadge.vue'
import { useScansStore } from '../stores/scans'

const route = useRoute()
const scansStore = useScansStore()

const scan = computed(() => scansStore.current)
const patientName = computed(() =>
  scan.value?.patient ? `${scan.value.patient.first_name} ${scan.value.patient.last_name}` : ''
)

const frameLandmarks = computed(
  () => scan.value?.keypoints?.frame_landmarks || scan.value?.keypoints?.landmarks || []
)
const twinLandmarks = computed(() => {
  const twin = scan.value?.keypoints?.twin_landmarks
  if (Array.isArray(twin) && twin.length) return twin
  return scan.value?.keypoints?.landmarks || []
})
const frameViews = [
  { key: 'front', label: 'Front' },
  { key: 'side', label: 'Side' },
  { key: 'back', label: 'Back' },
  { key: 'adams', label: 'Adams' },
]
const selectedFrameView = ref('front')

const twinTabs = [
  { key: 'twin', label: 'Digital Twin' },
  { key: 'keypoints', label: 'Keypoints' },
]
const selectedTwinTab = ref('twin')
const keypointViewFilter = ref('front')

const keypointRows = computed(() =>
  frameLandmarks.value
    .filter((kp) => (kp.view || 'front') === keypointViewFilter.value)
    .slice()
    .sort((a, b) => a.name.localeCompare(b.name))
)

const currentFrameUrl = computed(
  () => scan.value?.frame_urls?.[selectedFrameView.value] || null
)

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

onMounted(() => scansStore.fetchScan(route.params.id))
</script>

<template>
  <AppLayout
    :title="scan ? `Scan Results — ${patientName}` : 'Scan Results'"
    subtitle="Posture metrics and digital twin"
  >
    <template #header-actions>
      <div v-if="scan" class="flex items-center gap-4">
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

      <div v-if="scan.status === 'failed'" class="bg-error-container/20 border border-error p-4">
        <p class="text-error font-label-caps">Analysis failed</p>
        <p class="text-on-surface-variant text-sm mt-2">{{ scan.error_message }}</p>
      </div>

      <div v-if="scan.status === 'completed'" class="grid grid-cols-12 gap-gutter items-start">
        <section class="col-span-12 lg:col-span-5 space-y-stack-lg">
          <div class="space-y-4">
            <h3 class="font-label-caps text-primary">Annotated Capture Frames</h3>
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
            <FrameKeypointOverlay
              :image-url="currentFrameUrl"
              :landmarks="frameLandmarks"
              :view="selectedFrameView"
            />
          </div>
          <div>
            <h3 class="font-label-caps text-primary mb-4">Digital Twin</h3>
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

            <DigitalTwinViewer v-if="selectedTwinTab === 'twin'" :landmarks="twinLandmarks" />

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
