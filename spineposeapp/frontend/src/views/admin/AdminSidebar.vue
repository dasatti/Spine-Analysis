<script setup>
import { computed, ref } from 'vue'
import { useRoute, RouterLink, useRouter } from 'vue-router'
import { useAuthStore } from '../../stores/auth'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const researchOpen = ref(true)

const navItems = [
  { to: '/admin/dashboard', icon: 'dashboard', label: 'Dashboard' },
  { to: '/admin/doctors', icon: 'medical_services', label: 'Doctors' },
]

const researchItems = [
  { to: '/admin/research/dataset', icon: 'dataset', label: 'Dataset Generation' },
]

const isResearchActive = computed(() => route.path.startsWith('/admin/research'))

function isActive(path) {
  return route.path === path || route.path.startsWith(`${path}/`)
}

function logout() {
  authStore.logout()
  router.push('/login')
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
        ADMIN PANEL
      </p>
    </div>
    <nav class="flex-1 space-y-1 overflow-y-auto">
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

      <div class="pt-4">
        <button
          :class="[
            'w-full flex items-center gap-3 px-6 py-3 transition-all duration-150',
            isResearchActive
              ? 'text-primary'
              : 'text-on-surface-variant hover:bg-surface-container-high hover:text-on-surface',
          ]"
          type="button"
          @click="researchOpen = !researchOpen"
        >
          <span class="material-symbols-outlined text-[20px]">science</span>
          <span class="font-body-sm text-body-sm font-medium tracking-wide flex-1 text-left">Research</span>
          <span class="material-symbols-outlined text-[16px]">{{
            researchOpen ? 'expand_less' : 'expand_more'
          }}</span>
        </button>
        <div v-if="researchOpen" class="ml-4 border-l border-outline-variant">
          <RouterLink
            v-for="item in researchItems"
            :key="item.to"
            :to="item.to"
            :class="[
              'flex items-center gap-3 pl-8 pr-6 py-2.5 transition-all duration-150',
              isActive(item.to)
                ? 'bg-primary-container/10 text-primary'
                : 'text-on-surface-variant hover:bg-surface-container-high hover:text-on-surface',
            ]"
          >
            <span class="material-symbols-outlined text-[18px]">{{ item.icon }}</span>
            <span class="font-body-sm text-xs font-medium tracking-wide">{{ item.label }}</span>
          </RouterLink>
        </div>
      </div>
    </nav>
    <div class="px-6 mt-auto border-t border-outline-variant pt-6 space-y-4">
      <div class="flex items-center gap-3">
        <div
          class="w-10 h-10 rounded bg-surface-container-high border border-outline-variant flex items-center justify-center overflow-hidden text-primary font-bold"
        >
          {{ authStore.doctorInitials }}
        </div>
        <div class="overflow-hidden">
          <p class="font-body-sm text-sm font-bold truncate">{{ authStore.doctorFullName }}</p>
          <p class="font-label-caps text-[10px] text-on-surface-variant truncate">Administrator</p>
        </div>
      </div>
      <button
        class="w-full flex items-center gap-2 px-3 py-2 text-on-surface-variant hover:text-on-surface hover:bg-surface-container-high transition-colors font-body-sm text-sm"
        type="button"
        @click="logout"
      >
        <span class="material-symbols-outlined text-[18px]">logout</span>
        Sign out
      </button>
    </div>
  </aside>
</template>
