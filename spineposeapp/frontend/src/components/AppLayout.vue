<script setup>
import AppSidebar from './AppSidebar.vue'

defineProps({
  title: { type: String, default: '' },
  subtitle: { type: String, default: '' },
})
</script>

<template>
  <div class="min-h-screen bg-surface-container-lowest">
    <AppSidebar />
    <main class="ml-[240px] min-h-screen flex flex-col">
      <header
        v-if="title"
        class="sticky top-0 z-40 bg-surface-container-lowest/80 backdrop-blur-md border-b border-outline-variant px-gutter lg:px-margin-desktop py-6 flex items-center justify-between"
      >
        <div>
          <h1 class="font-headline-lg text-headline-lg-mobile lg:text-headline-lg font-bold text-on-surface">
            {{ title }}
          </h1>
          <p v-if="subtitle" class="font-body-sm text-on-surface-variant mt-1">{{ subtitle }}</p>
        </div>
        <slot name="header-actions" />
      </header>
      <slot />
    </main>
  </div>
</template>
