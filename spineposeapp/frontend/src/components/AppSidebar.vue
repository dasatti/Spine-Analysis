<script setup>
import { computed } from 'vue'
import { useRoute, RouterLink } from 'vue-router'
import { useAuthStore } from '../stores/auth'

defineProps({
  title: { type: String, default: '' },
  subtitle: { type: String, default: '' },
})

const route = useRoute()
const authStore = useAuthStore()

const navItems = [
  { to: '/dashboard', icon: 'dashboard', label: 'Dashboard' },
  { to: '/patients', icon: 'group', label: 'Patients' },
  { to: '/scans', icon: 'biotech', label: 'Scan Sessions' },
  { to: '/reports', icon: 'description', label: 'Reports' },
]

const bottomItems = [
  { to: '/settings', icon: 'settings', label: 'Settings' },
  { to: '/help', icon: 'help', label: 'Help' },
]

function isActive(path) {
  return route.path === path || route.path.startsWith(`${path}/`)
}
</script>

<template>
  <aside
    class="fixed left-0 top-0 h-full w-[240px] bg-surface-container-lowest border-r border-outline-variant flex flex-col py-panel-padding z-50"
  >
    <div class="px-6 mb-10">
      <h1 class="font-headline-md text-headline-md font-bold text-primary uppercase tracking-tighter">
        SPINEPOSE
      </h1>
      <p class="font-label-caps text-[10px] text-on-surface-variant tracking-widest mt-1 opacity-60">
        CLINICAL AI PLATFORM
      </p>
    </div>
    <nav class="flex-1 space-y-1">
      <RouterLink
        v-for="item in navItems"
        :key="item.to"
        :to="item.to"
        :class="[
          'flex items-center gap-3 px-6 py-3 transition-all duration-150',
          isActive(item.to)
            ? 'bg-primary-container/10 text-primary border-l-4 border-primary'
            : 'text-on-surface-variant hover:bg-surface-container-high hover:text-on-surface border-l-4 border-transparent',
        ]"
      >
        <span class="material-symbols-outlined text-[20px]">{{ item.icon }}</span>
        <span class="font-body-sm text-body-sm font-medium tracking-wide">{{ item.label }}</span>
      </RouterLink>
      <div class="pt-10">
        <RouterLink
          v-for="item in bottomItems"
          :key="item.to"
          :to="item.to"
          :class="[
            'flex items-center gap-3 px-6 py-3 transition-colors',
            isActive(item.to)
              ? 'bg-primary-container/10 text-primary border-l-4 border-primary'
              : 'text-on-surface-variant hover:bg-surface-container-high hover:text-on-surface border-l-4 border-transparent',
          ]"
        >
          <span class="material-symbols-outlined text-[20px]">{{ item.icon }}</span>
          <span class="font-body-sm text-body-sm font-medium tracking-wide">{{ item.label }}</span>
        </RouterLink>
      </div>
    </nav>
    <div class="px-6 mt-auto border-t border-outline-variant pt-6">
      <div class="flex items-center gap-3">
        <div
          class="w-10 h-10 rounded bg-surface-container-high border border-outline-variant flex items-center justify-center overflow-hidden text-primary font-bold"
        >
          {{ authStore.doctorInitials }}
        </div>
        <div class="overflow-hidden">
          <p class="font-body-sm text-sm font-bold truncate">{{ authStore.doctorFullName }}</p>
          <p class="font-label-caps text-[10px] text-on-surface-variant truncate">
            {{ authStore.doctor?.specialty || 'Clinician' }}
          </p>
        </div>
      </div>
    </div>
  </aside>
</template>
