<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useScansStore } from '../stores/scans'

const route = useRoute()
const router = useRouter()
const scansStore = useScansStore()

const status = ref(null)
const elapsed = ref(0)
let elapsedTimer = null

const progress = computed(() => {
  const msg = status.value?.progress_message?.toLowerCase() || ''
  if (status.value?.status === 'completed') return 100
  if (msg.includes('complete')) return 95
  if (msg.includes('metric')) return 75
  if (msg.includes('3d') || msg.includes('reconstruct')) return 55
  if (msg.includes('keypoint') || msg.includes('detection')) return 35
  if (msg.includes('frame') || msg.includes('download')) return 15
  return 10
})

const pipelineSteps = computed(() => {
  const msg = status.value?.progress_message?.toLowerCase() || ''
  return [
    { label: 'Frames received', done: true },
    {
      label: 'Running keypoint detection',
      active: msg.includes('keypoint') || msg.includes('detection'),
      done: msg.includes('3d') || msg.includes('metric') || msg.includes('complete'),
    },
    {
      label: '3D reconstruction',
      active: msg.includes('3d') || msg.includes('reconstruct'),
      done: msg.includes('metric') || msg.includes('complete'),
    },
    {
      label: 'Computing posture metrics',
      active: msg.includes('metric'),
      done: msg.includes('complete'),
    },
  ]
})

function onStatusUpdate(data) {
  status.value = data
  if (data.status === 'completed') {
    router.push(`/scans/${route.params.id}`)
  } else if (data.status === 'failed') {
    router.push(`/scans/${route.params.id}`)
  }
}

onMounted(() => {
  scansStore.pollStatus(route.params.id, onStatusUpdate)
  elapsedTimer = setInterval(() => elapsed.value++, 1000)
})

onUnmounted(() => {
  scansStore.stopPolling()
  if (elapsedTimer) clearInterval(elapsedTimer)
})

const elapsedLabel = computed(() => {
  const m = Math.floor(elapsed.value / 60)
  const s = elapsed.value % 60
  return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}s`
})
</script>

<template>
  <div
    class="bg-background text-on-surface font-body-lg flex flex-col min-h-screen selection:bg-primary-container selection:text-on-primary-container overflow-hidden"
  >
    <main
      class="relative z-10 flex flex-col items-center justify-center flex-1 w-full px-margin-mobile md:px-margin-desktop"
    >
      <div class="w-full max-w-4xl flex flex-col items-center">
        <div class="mb-12 flex flex-col items-center">
          <span
            class="material-symbols-outlined text-primary text-[84px]"
            style="font-variation-settings: 'FILL' 1"
            >biotech</span
          >
          <h1 class="font-display-lg text-display-lg text-primary uppercase tracking-tighter text-center">
            SpinePose
          </h1>
          <div class="flex items-center gap-2 mt-2">
            <div class="w-1.5 h-1.5 rounded-full bg-primary-container animate-pulse"></div>
            <p class="font-label-caps text-label-caps text-on-surface-variant">
              Clinical AI Platform • Processing
            </p>
          </div>
        </div>

        <div class="w-full grid grid-cols-1 md:grid-cols-12 gap-gutter mb-stack-lg">
          <div
            class="md:col-span-8 relative aspect-video glass-panel overflow-hidden border border-outline-variant rounded-lg"
          >
            <div class="scan-line"></div>
            <img
              class="w-full h-full object-cover grayscale opacity-50 contrast-125"
              src="https://lh3.googleusercontent.com/aida-public/AB6AXuC5QEqOHuxnjiUnIU55XKmNjSWoXhuAWyvOFB_6xFdfT_LX53187YHuZKELgkExnFw88Juh7x0z1xJlbd-zNaJNuwEUXz1X0iY4uoRO6RiN30YkxSGXczqh_HgpV6zSnxmJVR8iIwiEyVRfn1no0otIzS5XStYDH8LrB93oOqyhSS1618UfhvCng8s5j1SznUo6yhQM6aR9WlwaY4NXVcmXrNWC4sWco79BC4B80rs1EyG-jwnmqQw"
              alt=""
            />
            <div class="absolute top-4 left-4 flex flex-col gap-2 z-20">
              <div
                class="flex items-center gap-2 bg-black/60 px-3 py-1.5 border border-outline-variant backdrop-blur-md"
              >
                <div class="spine-bar"></div>
                <span class="font-label-caps text-label-caps text-primary">LIVE SCAN ANALYSIS</span>
              </div>
            </div>
          </div>

          <div class="md:col-span-4 flex flex-col gap-stack-sm">
            <div class="glass-panel p-panel-padding flex-1 border border-outline-variant">
              <h2 class="font-headline-md text-headline-md mb-6 flex items-center gap-3">
                <div class="spine-bar"></div>
                Process Stack
              </h2>
              <div class="space-y-6">
                <div
                  v-for="(s, i) in pipelineSteps"
                  :key="i"
                  :class="['flex items-start gap-4', !s.done && !s.active ? 'opacity-40' : '']"
                >
                  <div
                    :class="[
                      'w-8 h-8 rounded-full border flex items-center justify-center shrink-0',
                      s.done
                        ? 'border-primary bg-primary/10 text-primary'
                        : s.active
                          ? 'border-primary bg-primary-container text-on-primary-container animate-pulse-yellow'
                          : 'border-outline-variant text-on-surface-variant',
                    ]"
                  >
                    <span class="material-symbols-outlined text-[18px]">{{
                      s.done ? 'check' : s.active ? 'sync' : 'circle'
                    }}</span>
                  </div>
                  <div class="flex flex-col">
                    <span
                      :class="[
                        'font-body-sm text-body-sm font-bold',
                        s.active ? 'text-primary' : 'text-on-surface',
                      ]"
                      >{{ s.label }}</span
                    >
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div class="w-full max-w-2xl text-center space-y-4">
          <div class="space-y-1">
            <p class="font-headline-md text-headline-md text-on-surface">
              {{ status?.progress_message || 'Initialising analysis pipeline...' }}
            </p>
            <p class="font-body-sm text-body-sm text-on-surface-variant">
              This usually takes under 30 seconds.
            </p>
          </div>
          <div class="relative pt-4">
            <div class="w-full h-1 bg-surface-container-highest rounded-full overflow-hidden">
              <div
                class="h-full bg-primary-container transition-all duration-1000 ease-out shadow-[0_0_10px_rgba(232,214,0,0.5)]"
                :style="{ width: `${progress}%` }"
              ></div>
            </div>
            <div class="flex justify-between mt-2">
              <span class="font-metric-sm text-metric-sm text-primary"
                >{{ progress }}% COMPLETE</span
              >
              <span class="font-metric-sm text-metric-sm text-on-surface-variant">{{
                elapsedLabel
              }}</span>
            </div>
          </div>
        </div>
      </div>
    </main>

    <footer class="relative z-10 w-full p-panel-padding flex justify-between items-end">
      <div class="glass-panel px-4 py-2 flex items-center gap-3">
        <span class="material-symbols-outlined text-error text-[20px]">security</span>
        <span class="font-label-caps text-label-caps text-on-surface-variant"
          >HIPAA ENCRYPTED CHANNEL</span
        >
      </div>
      <div class="text-right">
        <span class="font-label-caps text-label-caps text-on-surface-variant block mb-1"
          >SYSTEM STATE</span
        >
        <div class="flex items-center justify-end gap-2">
          <span class="font-metric-sm text-metric-sm text-primary uppercase">{{
            status?.status || 'processing'
          }}</span>
          <div class="w-2 h-2 rounded-full bg-primary-container animate-ping"></div>
        </div>
      </div>
    </footer>
  </div>
</template>

<style scoped>
@keyframes pulse-yellow {
  0%,
  100% {
    opacity: 1;
    transform: scale(1);
  }
  50% {
    opacity: 0.6;
    transform: scale(1.1);
  }
}
.animate-pulse-yellow {
  animation: pulse-yellow 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
}
.scan-line {
  height: 2px;
  background: #e8d600;
  box-shadow: 0 0 15px #e8d600;
  position: absolute;
  width: 100%;
  top: 0;
  animation: scanning 4s linear infinite;
  z-index: 20;
}
@keyframes scanning {
  0% {
    top: 0;
    opacity: 0;
  }
  5% {
    opacity: 1;
  }
  95% {
    opacity: 1;
  }
  100% {
    top: 100%;
    opacity: 0;
  }
}
.glass-panel {
  background: rgba(26, 26, 26, 0.8);
  backdrop-filter: blur(12px);
  border: 1px solid rgba(150, 145, 120, 0.2);
}
</style>
