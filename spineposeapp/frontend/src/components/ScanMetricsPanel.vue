<script setup>
import { computed } from 'vue'
import MetricCard from './MetricCard.vue'

const props = defineProps({
  metrics: { type: Object, default: null },
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
    }
  }
  return [
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
  ]
})
</script>

<template>
  <div v-if="!metrics" class="text-on-surface-variant text-center py-12">No metrics available</div>
  <div v-else class="space-y-8">
    <section v-for="group in groups" :key="group.title">
      <h3 class="font-label-caps text-label-caps text-primary mb-4">{{ group.title }}</h3>
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <MetricCard
          v-for="item in group.items"
          :key="item.key"
          :name="item.label"
          :value="item.value"
          :unit="item.unit"
          :normal-min="item.normalMin"
          :normal-max="item.normalMax"
          :availability="item.availability"
          :source-view="item.sourceView"
        />
      </div>
    </section>
  </div>
</template>
