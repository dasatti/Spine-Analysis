<script setup>
import { onMounted, ref, watch } from 'vue'
import { RouterLink } from 'vue-router'
import AdminLayout from '../AdminLayout.vue'
import { createDatasetItems, exportDatasetItemsCsv, listDatasetItems } from '../../../api/client'

const loading = ref(true)
const creating = ref(false)
const exporting = ref(false)
const exportError = ref('')
const items = ref([])
const total = ref(0)
const page = ref(1)
const totalPages = ref(1)

const poseFilter = ref('')
const modelFilter = ref('')
const statusFilter = ref('')

const showCreate = ref(false)
const createPose = ref('front')
const createModel = ref('spinepose_v2')
const createFiles = ref([])
const createError = ref('')

const poseOptions = [
  { value: 'front', label: 'Front' },
  { value: 'back', label: 'Back' },
  { value: 'side', label: 'Side' },
  { value: 'adams', label: 'Adams' },
  { value: 'face', label: 'Face' },
]

const modelOptions = [
  { value: 'spinepose_v2', label: 'SpinePose' },
  { value: 'yolo_v8', label: 'YOLO' },
]

const statusOptions = [
  { value: '', label: 'All' },
  { value: 'ready', label: 'Ready' },
  { value: 'processing', label: 'Processing' },
  { value: 'pending', label: 'Pending' },
  { value: 'failed', label: 'Failed' },
]

function modelLabel(value) {
  return modelOptions.find((m) => m.value === value)?.label || value
}

function statusClass(status) {
  const map = {
    ready: 'bg-primary-container/20 text-primary',
    processing: 'bg-yellow-500/20 text-yellow-400',
    pending: 'bg-on-surface-variant/20 text-on-surface-variant',
    failed: 'bg-error/20 text-error',
  }
  return map[status] || 'bg-on-surface-variant/20 text-on-surface-variant'
}

function keypointPreview(item) {
  if (!item.keypoint_count) return '—'
  return `${item.keypoint_count} keypoints`
}

async function exportCsv() {
  exportError.value = ''
  exporting.value = true
  try {
    const params = {}
    if (poseFilter.value) params.pose_type = poseFilter.value
    if (modelFilter.value) params.detector_model = modelFilter.value
    if (statusFilter.value) params.status = statusFilter.value
    const { data } = await exportDatasetItemsCsv(params)
    const url = URL.createObjectURL(data)
    const link = document.createElement('a')
    link.href = url
    link.download = `dataset_export_${Date.now()}.csv`
    document.body.appendChild(link)
    link.click()
    link.remove()
    URL.revokeObjectURL(url)
  } catch (e) {
    exportError.value =
      e.response?.data?.message ||
      (typeof e.response?.data?.detail === 'object' ? e.response?.data?.detail?.message : null) ||
      'Failed to export CSV.'
  } finally {
    exporting.value = false
  }
}

async function loadItems() {
  loading.value = true
  try {
    const params = { page: page.value, page_size: 20 }
    if (poseFilter.value) params.pose_type = poseFilter.value
    if (modelFilter.value) params.detector_model = modelFilter.value
    if (statusFilter.value) params.status = statusFilter.value
    const { data } = await listDatasetItems(params)
    items.value = data.items
    total.value = data.total
    totalPages.value = data.total_pages
  } finally {
    loading.value = false
  }
}

function onFileChange(event) {
  createFiles.value = Array.from(event.target.files || [])
}

async function submitCreate() {
  createError.value = ''
  if (!createFiles.value.length) {
    createError.value = 'Select at least one image.'
    return
  }
  creating.value = true
  try {
    const formData = new FormData()
    formData.append('pose_type', createPose.value)
    formData.append('detector_model', createModel.value)
    for (const file of createFiles.value) {
      formData.append('images', file)
    }
    await createDatasetItems(formData)
    showCreate.value = false
    createFiles.value = []
    page.value = 1
    await loadItems()
  } catch (e) {
    const data = e.response?.data
    createError.value =
      data?.message ||
      (typeof data?.detail === 'object' ? data.detail.message : data?.detail) ||
      'Failed to create items.'
  } finally {
    creating.value = false
  }
}

watch([poseFilter, modelFilter, statusFilter, page], loadItems)
onMounted(loadItems)
</script>

<template>
  <AdminLayout title="Dataset Generation" subtitle="Research — training data with detected keypoints">
    <section class="p-gutter lg:px-margin-desktop lg:pt-8 space-y-6 pb-8">
      <div
        class="flex flex-wrap gap-4 items-center justify-between bg-surface-container-low p-4 border border-outline-variant"
      >
        <div class="flex flex-wrap flex-1 gap-3 items-center">
          <select
            v-model="poseFilter"
            class="bg-background border border-outline-variant text-on-surface font-label-caps px-3 py-2 outline-none focus:border-primary-container"
          >
            <option value="">POSE: ALL</option>
            <option v-for="p in poseOptions" :key="p.value" :value="p.value">{{ p.label.toUpperCase() }}</option>
          </select>
          <select
            v-model="modelFilter"
            class="bg-background border border-outline-variant text-on-surface font-label-caps px-3 py-2 outline-none focus:border-primary-container"
          >
            <option value="">MODEL: ALL</option>
            <option v-for="m in modelOptions" :key="m.value" :value="m.value">{{ m.label.toUpperCase() }}</option>
          </select>
          <select
            v-model="statusFilter"
            class="bg-background border border-outline-variant text-on-surface font-label-caps px-3 py-2 outline-none focus:border-primary-container"
          >
            <option v-for="s in statusOptions" :key="s.value" :value="s.value">
              STATUS: {{ s.label.toUpperCase() }}
            </option>
          </select>
        </div>
        <div class="flex flex-wrap items-center gap-3">
          <button
            class="border border-outline-variant text-on-surface-variant hover:text-on-surface px-5 py-2.5 font-label-caps text-[10px] font-bold flex items-center gap-2 transition-all disabled:opacity-50"
            type="button"
            :disabled="exporting || loading"
            @click="exportCsv"
          >
            <span class="material-symbols-outlined text-[18px]">download</span>
            {{ exporting ? 'EXPORTING...' : 'EXPORT TO CSV' }}
          </button>
          <button
            class="bg-primary-container hover:bg-primary text-on-primary-container px-6 py-2.5 font-bold flex items-center gap-2 transition-all active:scale-[0.98]"
            type="button"
            @click="showCreate = !showCreate"
          >
            <span class="material-symbols-outlined">add_photo_alternate</span>
            CREATE NEW
          </button>
        </div>
      </div>
      <p v-if="exportError" class="text-error text-sm">{{ exportError }}</p>

      <div
        v-if="showCreate"
        class="bg-surface-container border border-outline-variant p-panel-padding space-y-4"
      >
        <h3 class="font-label-caps text-primary">Upload Dataset Images</h3>
        <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div class="flex flex-col gap-2">
            <label class="font-label-caps text-on-surface-variant text-xs">POSE</label>
            <select
              v-model="createPose"
              class="bg-background border border-outline-variant text-on-surface px-3 py-2 outline-none focus:border-primary-container"
            >
              <option v-for="p in poseOptions" :key="p.value" :value="p.value">{{ p.label }}</option>
            </select>
          </div>
          <div class="flex flex-col gap-2">
            <label class="font-label-caps text-on-surface-variant text-xs">MODEL</label>
            <select
              v-model="createModel"
              class="bg-background border border-outline-variant text-on-surface px-3 py-2 outline-none focus:border-primary-container"
            >
              <option v-for="m in modelOptions" :key="m.value" :value="m.value">{{ m.label }}</option>
            </select>
          </div>
          <div class="flex flex-col gap-2">
            <label class="font-label-caps text-on-surface-variant text-xs">IMAGES</label>
            <input
              class="bg-background border border-outline-variant text-on-surface px-3 py-2 file:mr-3 file:bg-primary-container file:text-on-primary-container file:border-0 file:px-3 file:py-1"
              accept="image/png,image/jpeg,image/tiff"
              multiple
              type="file"
              @change="onFileChange"
            />
          </div>
        </div>
        <p v-if="createFiles.length" class="text-sm text-on-surface-variant">
          {{ createFiles.length }} file(s) selected
        </p>
        <p v-if="createError" class="text-error text-sm">{{ createError }}</p>
        <div class="flex gap-3">
          <button
            class="bg-primary text-on-primary font-label-caps px-6 py-2 font-bold disabled:opacity-60"
            type="button"
            :disabled="creating"
            @click="submitCreate"
          >
            {{ creating ? 'PROCESSING...' : 'UPLOAD & DETECT KEYPOINTS' }}
          </button>
          <button
            class="font-body-sm text-on-surface-variant hover:text-on-surface"
            type="button"
            @click="showCreate = false"
          >
            Cancel
          </button>
        </div>
      </div>

      <div v-if="loading" class="text-on-surface-variant py-12 text-center">Loading dataset items...</div>
      <div v-else class="border border-outline-variant bg-background overflow-hidden">
        <div class="overflow-x-auto">
          <table class="w-full border-collapse">
            <thead class="bg-[#1A1A1A] border-b border-outline-variant">
              <tr>
                <th class="px-4 py-4 text-left font-label-caps text-on-surface-variant text-xs">PREVIEW</th>
                <th class="px-4 py-4 text-left font-label-caps text-on-surface-variant text-xs">FILE</th>
                <th class="px-4 py-4 text-left font-label-caps text-on-surface-variant text-xs">POSE</th>
                <th class="px-4 py-4 text-left font-label-caps text-on-surface-variant text-xs">MODEL</th>
                <th class="px-4 py-4 text-left font-label-caps text-on-surface-variant text-xs">KEYPOINTS</th>
                <th class="px-4 py-4 text-left font-label-caps text-on-surface-variant text-xs">STATUS</th>
                <th class="px-4 py-4 text-center font-label-caps text-on-surface-variant text-xs">ACTIONS</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-outline-variant">
              <tr v-for="item in items" :key="item.id" class="hover:bg-surface-container-low transition-colors">
                <td class="px-4 py-3">
                  <div
                    class="w-16 h-16 bg-surface-container border border-outline-variant overflow-hidden flex items-center justify-center"
                  >
                    <img
                      v-if="item.image_url"
                      :src="item.image_url"
                      :alt="item.original_filename || 'Dataset image'"
                      class="w-full h-full object-cover"
                    />
                    <span v-else class="material-symbols-outlined text-on-surface-variant">image</span>
                  </div>
                </td>
                <td class="px-4 py-3">
                  <p class="font-body-sm text-sm text-on-surface max-w-[180px] truncate">
                    {{ item.original_filename || item.id.slice(0, 8) }}
                  </p>
                  <p v-if="item.keypoints_adjusted" class="font-label-caps text-[10px] text-primary mt-0.5">
                    Adjusted
                  </p>
                </td>
                <td class="px-4 py-3 font-label-caps text-xs text-on-surface">{{ item.pose_type }}</td>
                <td class="px-4 py-3 font-body-sm text-sm text-on-surface-variant">
                  {{ modelLabel(item.detector_model) }}
                </td>
                <td class="px-4 py-3 font-metric-sm text-sm text-on-surface">
                  {{ keypointPreview(item) }}
                </td>
                <td class="px-4 py-3">
                  <span :class="['font-label-caps text-[10px] px-2 py-1', statusClass(item.status)]">
                    {{ item.status }}
                  </span>
                </td>
                <td class="px-4 py-3 text-center">
                  <RouterLink
                    v-if="item.status === 'ready'"
                    :to="`/admin/research/dataset/${item.id}/adjust`"
                    class="inline-flex items-center gap-1 text-primary hover:underline font-body-sm text-sm"
                  >
                    <span class="material-symbols-outlined text-[16px]">tune</span>
                    Adjust Keypoints
                  </RouterLink>
                  <span v-else class="text-on-surface-variant text-xs">—</span>
                </td>
              </tr>
              <tr v-if="!items.length">
                <td colspan="7" class="px-6 py-12 text-center text-on-surface-variant">
                  No dataset items yet. Create new items to get started.
                </td>
              </tr>
            </tbody>
          </table>
        </div>
        <div
          v-if="totalPages > 1"
          class="bg-[#1A1A1A] border-t border-outline-variant px-6 py-4 flex items-center justify-between"
        >
          <button
            class="font-label-caps text-on-surface-variant hover:text-on-surface disabled:opacity-40"
            :disabled="page <= 1"
            type="button"
            @click="page--"
          >
            Previous
          </button>
          <span class="font-metric-sm text-sm text-on-surface-variant">
            Page {{ page }} of {{ totalPages }} ({{ total }} items)
          </span>
          <button
            class="font-label-caps text-on-surface-variant hover:text-on-surface disabled:opacity-40"
            :disabled="page >= totalPages"
            type="button"
            @click="page++"
          >
            Next
          </button>
        </div>
      </div>
    </section>
  </AdminLayout>
</template>
