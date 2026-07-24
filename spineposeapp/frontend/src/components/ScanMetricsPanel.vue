<script setup>
import { computed } from 'vue'
import MetricCard from './MetricCard.vue'

const props = defineProps({
  metrics: { type: Object, default: null },
  compact: { type: Boolean, default: false },
  /** 'stacked' = category sections full width; 'columns' = one column per category */
  layout: {
    type: String,
    default: 'stacked',
    validator: (value) => ['stacked', 'columns'].includes(value),
  },
})

const groups = computed(() => {
  if (!props.metrics) return []
  const nr = props.metrics.normal_ranges || {}
  const mk = (group, key, label, sourceView = 'side') => {
    const m = props.metrics[group]?.[key]
    if (!m) return null
    const range = nr[key] || { min: 0, max: 100 }
    return {
      key,
      label,
      value: m.value,
      unit: m.unit,
      availability: m.availability,
      normalMin: range.min,
      normalMax: range.max,
      sourceView,
      metricType: 'numeric',
      confidence: null,
    }
  }
  const mkCls = (group, key, label, sourceView = 'side') => {
    const m = props.metrics[group]?.[key]
    if (!m) return null
    return {
      key,
      label,
      value: m.value,
      unit: m.unit,
      availability: m.availability,
      confidence: m.confidence ?? null,
      lateralIndex: m.lateral_index ?? null,
      keypointCount: m.keypoint_count ?? null,
      metricType: m.metric_type || 'classification',
      normalMin: 0,
      normalMax: 100,
      sourceView,
    }
  }
  return [
    {
      title: 'AI Classification',
      items: [
        mkCls('ai_classification', 'kyphosis', 'Kyphosis', 'side'),
        mkCls('ai_classification', 'lordosis', 'Lordosis', 'side'),
        mkCls('ai_classification', 'scoliosis', 'Scoliosis', 'back'),
      ].filter(Boolean),
    },
    {
      title: 'Spinal Curves',
      items: [
        mk('spinal_curves', 'thoracic_kyphosis_deg', 'Thoracic Kyphosis'),
        mk('spinal_curves', 'lumbar_lordosis_deg', 'Lumbar Lordosis'),
      ].filter(Boolean),
    },
    {
      title: 'Pelvis & Lower Body',
      items: [
        mk('pelvis_lower_body', 'pelvic_tilt_sagittal_deg', 'Pelvic Tilt (Sagittal)', 'side'),
        mk('pelvis_lower_body', 'pelvic_obliquity_mm', 'Pelvic Obliquity', 'front'),
        mk('pelvis_lower_body', 'knee_flexion_left_deg', 'Knee Flexion (L)', 'front'),
        mk('pelvis_lower_body', 'knee_flexion_right_deg', 'Knee Flexion (R)', 'front'),
        mk('pelvis_lower_body', 'hka_angle_left_deg', 'HKA Angle (L)', 'front'),
        mk('pelvis_lower_body', 'hka_angle_right_deg', 'HKA Angle (R)', 'front'),
      ].filter(Boolean),
    },
    {
      title: 'Head & Shoulders',
      items: [
        mk('head_shoulders', 'forward_head_posture_mm', 'Forward Head Posture', 'side'),
        mk('head_shoulders', 'shoulder_height_asymmetry_mm', 'Shoulder Asymmetry', 'front'),
        mk('head_shoulders', 'jaw_deviation_mm', 'Jaw Deviation', 'face'),
      ].filter(Boolean),
    },
    {
      title: 'Spine & Back',
      items: [
        mk('spine_back', 'spine_drift_mm', 'Spine Drift', 'back'),
        mk('spine_back', 'scapula_asymmetry_index', 'Scapula Asymmetry', 'back'),
        mk('spine_back', 'vertebral_rotation_index', 'Vertebral Rotation', 'back'),
        mk('spine_back', 'adams_rib_hump_present', 'Adams Rib Hump', 'adams'),
      ].filter(Boolean),
    },
  ].filter((group) => group.items.length > 0)
})
</script>

<template>
  <div v-if="!metrics" class="text-on-surface-variant text-center py-12">No metrics available</div>
  <div
    v-else-if="layout === 'columns'"
    class="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4"
  >
    <section v-for="group in groups" :key="group.title" class="min-w-0">
      <h3 class="font-label-caps text-xs text-primary mb-2">{{ group.title }}</h3>
      <div class="grid grid-cols-2 gap-2">
        <MetricCard
          v-for="item in group.items"
          :key="item.key"
          compact
          :name="item.label"
          :value="item.value"
          :unit="item.unit"
          :normal-min="item.normalMin"
          :normal-max="item.normalMax"
          :availability="item.availability"
          :source-view="item.sourceView"
          :metric-type="item.metricType"
          :confidence="item.confidence"
          :lateral-index="item.lateralIndex"
          :keypoint-count="item.keypointCount"
        />
      </div>
    </section>
  </div>
  <div v-else :class="compact ? 'space-y-4' : 'space-y-8'">
    <section v-for="group in groups" :key="group.title">
      <h3
        :class="[
          'font-label-caps text-label-caps text-primary',
          compact ? 'text-xs mb-2' : 'mb-4',
        ]"
      >
        {{ group.title }}
      </h3>
      <div
        :class="
          compact
            ? 'grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 xl:grid-cols-8 gap-2'
            : 'grid grid-cols-1 md:grid-cols-2 gap-4'
        "
      >
        <MetricCard
          v-for="item in group.items"
          :key="item.key"
          :compact="compact"
          :name="item.label"
          :value="item.value"
          :unit="item.unit"
          :normal-min="item.normalMin"
          :normal-max="item.normalMax"
          :availability="item.availability"
          :source-view="item.sourceView"
          :metric-type="item.metricType"
          :confidence="item.confidence"
          :lateral-index="item.lateralIndex"
          :keypoint-count="item.keypointCount"
        />
      </div>
    </section>
  </div>
</template>
