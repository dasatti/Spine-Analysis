<script setup>
import { ref } from 'vue'
import AppLayout from '../components/AppLayout.vue'

const expanded = ref('getting-started')

const sections = [
  {
    id: 'getting-started',
    title: 'Getting Started',
    icon: 'rocket_launch',
    content: `Welcome to SpinePose AI. After logging in, register patients from the Patients screen, then start a new scan from the Dashboard or patient profile. The 5-step setup wizard guides you through environment preparation, camera placement, and capture.`,
  },
  {
    id: 'scan-capture',
    title: 'Scan Capture Protocol',
    icon: 'biotech',
    content: `Capture five poses: Front, Side, Back, Adams forward bend, and optional Face view. Upload RGBD frames (PNG, JPEG, or TIFF). Ensure 3m clearance, even lighting (500–750 lux), and plain background. Minimum required views: Front, Side, Back, Adams.`,
  },
  {
    id: 'metrics',
    title: 'Understanding Metrics',
    icon: 'analytics',
    content: `SpinePose computes spinal curves (thoracic kyphosis, lumbar lordosis), pelvis alignment, head/shoulder posture, and back asymmetry indices. Values outside the normal range are highlighted in yellow. Unavailable metrics indicate missing landmarks or low confidence.`,
  },
  {
    id: 'reports',
    title: 'Reports & Export',
    icon: 'description',
    content: `Completed scans appear in the Reports Library. Export clinical PDF reports from the scan results page. Use Print / Save PDF to generate a printable document for patient records.`,
  },
  {
    id: 'support',
    title: 'Support',
    icon: 'support_agent',
    content: `For technical issues contact your clinic administrator. System device settings (detector model, confidence threshold) are configured in Settings under Device & Camera tab.`,
  },
]
</script>

<template>
  <AppLayout title="Help & Documentation" subtitle="Clinical platform guide">
    <div class="p-gutter lg:px-margin-desktop max-w-5xl mx-auto">
      <div class="flex items-center gap-stack-md mb-stack-lg">
        <div class="spine-bar"></div>
        <h2 class="font-headline-lg text-headline-lg text-on-surface">Help Center</h2>
      </div>

      <div class="grid grid-cols-12 gap-gutter">
        <nav class="col-span-12 md:col-span-4 space-y-2">
          <button
            v-for="section in sections"
            :key="section.id"
            :class="[
              'w-full text-left p-4 border transition-colors flex items-center gap-3',
              expanded === section.id
                ? 'border-primary bg-primary/10 text-primary'
                : 'border-outline-variant text-on-surface-variant hover:bg-surface-container-high hover:text-on-surface',
            ]"
            type="button"
            @click="expanded = section.id"
          >
            <span class="material-symbols-outlined">{{ section.icon }}</span>
            <span class="font-label-caps text-[11px]">{{ section.title.toUpperCase() }}</span>
          </button>
        </nav>

        <div class="col-span-12 md:col-span-8">
          <div
            v-for="section in sections"
            v-show="expanded === section.id"
            :key="section.id"
            class="bg-surface-container border border-outline-variant p-panel-padding"
          >
            <div class="flex items-center gap-3 mb-6">
              <span class="material-symbols-outlined text-primary text-2xl">{{
                section.icon
              }}</span>
              <h3 class="font-headline-md text-headline-md">{{ section.title }}</h3>
            </div>
            <p class="text-on-surface-variant font-body-lg leading-relaxed whitespace-pre-line">
              {{ section.content }}
            </p>
          </div>
        </div>
      </div>

      <div
        class="mt-stack-lg bg-surface-container-low border border-outline-variant p-panel-padding flex items-center gap-4"
      >
        <span class="material-symbols-outlined text-primary">verified_user</span>
        <div>
          <p class="font-label-caps text-on-surface text-[11px]">HIPAA COMPLIANT PLATFORM</p>
          <p class="text-on-surface-variant text-sm mt-1">
            All patient data is encrypted in transit and at rest.
          </p>
        </div>
      </div>
    </div>
  </AppLayout>
</template>

<style scoped>
.spine-bar {
  width: 6px;
  height: 22px;
  background-color: #e8d600;
  display: inline-block;
  margin-right: 12px;
  vertical-align: middle;
}
</style>
