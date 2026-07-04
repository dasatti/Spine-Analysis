<script setup>
import { computed, onMounted, ref } from 'vue'
import { RouterLink, useRoute } from 'vue-router'
import AppLayout from '../components/AppLayout.vue'
import RiskLevelBadge from '../components/RiskLevelBadge.vue'
import ScanMetricsPanel from '../components/ScanMetricsPanel.vue'
import { useScansStore } from '../stores/scans'

const route = useRoute()
const scansStore = useScansStore()
const printRef = ref(null)

const scan = computed(() => scansStore.current)
const patientName = computed(() =>
  scan.value?.patient ? `${scan.value.patient.first_name} ${scan.value.patient.last_name}` : ''
)

function formatDate(iso) {
  if (!iso) return '—'
  return new Date(iso).toLocaleDateString('en-GB', {
    day: 'numeric',
    month: 'long',
    year: 'numeric',
  })
}

function printReport() {
  window.print()
}

onMounted(() => scansStore.fetchScan(route.params.id))
</script>

<template>
  <AppLayout title="Export Report — SpinePose" subtitle="Clinical report preview">
    <template #header-actions>
      <div class="flex gap-3">
        <RouterLink
          :to="`/scans/${route.params.id}`"
          class="px-4 py-2 border border-outline-variant font-label-caps text-[10px] text-on-surface hover:bg-surface-container-high"
        >
          BACK TO RESULTS
        </RouterLink>
        <button
          class="px-4 py-2 bg-primary-container text-on-primary-container font-label-caps text-[10px] font-bold hover:opacity-90"
          type="button"
          @click="printReport"
        >
          PRINT / SAVE PDF
        </button>
      </div>
    </template>

    <div v-if="scansStore.loading" class="p-margin-desktop text-on-surface-variant">
      Preparing report...
    </div>
    <div v-else-if="scan" class="p-gutter lg:px-margin-desktop pb-margin-desktop">
      <div
        ref="printRef"
        class="max-w-4xl mx-auto bg-white text-black p-12 border border-outline-variant print-report"
      >
        <div class="flex justify-between items-start border-b-2 border-black pb-6 mb-8">
          <div>
            <h1 class="text-2xl font-bold uppercase tracking-tight">SpinePose Clinical Report</h1>
            <p class="text-sm text-gray-600 mt-1">Posture &amp; Spinal Alignment Analysis</p>
          </div>
          <div class="text-right text-sm">
            <p>{{ formatDate(scan.completed_at || scan.created_at) }}</p>
            <p class="font-mono text-xs mt-1">ID: {{ scan.id.slice(0, 8).toUpperCase() }}</p>
          </div>
        </div>

        <section class="mb-8">
          <h2 class="text-xs font-bold uppercase tracking-widest mb-4 text-gray-500">
            Patient Information
          </h2>
          <p class="text-xl font-bold">{{ patientName }}</p>
          <p class="text-sm mt-2">
            Height: {{ scan.patient_height_cm }} cm · Weight: {{ scan.patient_weight_kg }} kg
          </p>
        </section>

        <section v-if="scan.keypoints_adjusted || scan.keypoints?.audit?.adjusted_at" class="mb-8">
          <h2 class="text-xs font-bold uppercase tracking-widest mb-4 text-gray-500">
            Keypoint Adjustment
          </h2>
          <p class="text-sm text-amber-800 bg-amber-50 border border-amber-200 p-3">
            This report uses manually adjusted keypoints
            <span v-if="scan.keypoints?.audit?.adjusted_at">
              (last updated {{ formatDate(scan.keypoints.audit.adjusted_at) }})
            </span>.
            Measurements reflect clinician corrections, not raw detector output alone.
          </p>
        </section>

        <section v-if="scan.overall_risk" class="mb-8">
          <h2 class="text-xs font-bold uppercase tracking-widest mb-4 text-gray-500">
            Overall Risk Assessment
          </h2>
          <RiskLevelBadge :level="scan.overall_risk" />
        </section>

        <section class="mb-8">
          <h2 class="text-xs font-bold uppercase tracking-widest mb-4 text-gray-500">
            Capture Details
          </h2>
          <table class="w-full text-sm">
            <tbody>
              <tr>
                <td class="py-1 text-gray-600">Detector Model</td>
                <td class="py-1 font-mono">{{ scan.detector_model }}</td>
              </tr>
              <tr v-if="scan.capture_device">
                <td class="py-1 text-gray-600">Capture Device</td>
                <td class="py-1">{{ scan.capture_device }}</td>
              </tr>
              <tr v-if="scan.camera_height_cm">
                <td class="py-1 text-gray-600">Camera Height</td>
                <td class="py-1">{{ scan.camera_height_cm }} cm</td>
              </tr>
            </tbody>
          </table>
        </section>

        <section>
          <h2 class="text-xs font-bold uppercase tracking-widest mb-4 text-gray-500">
            Posture Metrics Summary
          </h2>
          <div class="report-metrics">
            <ScanMetricsPanel :metrics="scan.metrics" />
          </div>
        </section>

        <footer class="mt-12 pt-6 border-t border-gray-300 text-xs text-gray-500">
          <p>
            This report was generated by SpinePose AI. For clinical use only. Not a substitute for
            professional medical diagnosis.
          </p>
        </footer>
      </div>
    </div>
  </AppLayout>
</template>

<style scoped>
@media print {
  :global(body *) {
    visibility: hidden;
  }
  .print-report,
  .print-report * {
    visibility: visible;
  }
  .print-report {
    position: absolute;
    left: 0;
    top: 0;
    width: 100%;
  }
}
.report-metrics :deep(.bg-\[\#1A1A1A\]) {
  background: #f5f5f5 !important;
  color: #111 !important;
  border-color: #ddd !important;
}
</style>
