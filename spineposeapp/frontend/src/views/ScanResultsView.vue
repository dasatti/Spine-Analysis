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
const twinLandmarks = computed(() => scan.value?.keypoints?.landmarks || [])
const frameViews = [
  { key: 'front', label: 'Front' },
  { key: 'side', label: 'Side' },
  { key: 'back', label: 'Back' },
  { key: 'adams', label: 'Adams' },
]
const selectedFrameView = ref('front')

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
            <DigitalTwinViewer :landmarks="twinLandmarks" />
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
