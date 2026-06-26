<script setup>
import { ref } from 'vue'
import { RouterLink } from 'vue-router'
import { forgotPassword } from '../api/client'

const email = ref('')
const loading = ref(false)
const sent = ref(false)
const error = ref('')

async function onSubmit() {
  error.value = ''
  loading.value = true
  try {
    await forgotPassword(email.value)
    sent.value = true
  } catch (e) {
    error.value = e.response?.data?.detail || 'Unable to send reset link.'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="flex h-screen w-full overflow-hidden">
    <section
      class="relative hidden md:flex w-1/2 h-full bg-[#0A0A0A] flex-col justify-center px-margin-desktop border-r border-outline-variant"
    >
      <div class="relative z-10 max-w-lg">
        <div class="flex items-center gap-stack-md mb-stack-lg">
          <span
            class="font-headline-md text-headline-md font-bold text-primary uppercase tracking-tighter"
            >SpinePose</span
          >
        </div>
        <div class="flex items-center gap-3 mb-stack-md">
          <div class="spine-bar"></div>
          <h1 class="font-headline-lg text-headline-lg text-on-background">Password Recovery</h1>
        </div>
        <p class="text-on-surface-variant font-body-lg text-body-lg max-w-md">
          Secure credential reset for authorized clinical personnel only.
        </p>
      </div>
      <div class="scanline"></div>
    </section>

    <section
      class="w-full md:w-1/2 h-full bg-[#1A1A1A] flex items-center justify-center p-margin-mobile"
    >
      <div class="w-full max-w-md">
        <div class="bg-[#2A2A2A] border border-outline-variant p-panel-padding shadow-2xl">
          <div class="mb-stack-lg">
            <span class="font-label-caps text-label-caps text-primary block mb-2"
              >ACCOUNT RECOVERY</span
            >
            <h2 class="font-headline-md text-headline-md text-on-surface">Forgot Password</h2>
          </div>
          <form v-if="!sent" class="space-y-6" @submit.prevent="onSubmit">
            <div>
              <label
                class="font-label-caps text-label-caps text-on-surface-variant block mb-2"
                for="email"
                >PROFESSIONAL EMAIL</label
              >
              <input
                id="email"
                v-model="email"
                class="w-full bg-[#0A0A0A] border border-outline-variant focus:border-primary-container focus:ring-0 text-on-surface font-metric-sm text-metric-sm px-4 py-3 outline-none transition-all"
                placeholder="dr.smith@clinic.com"
                required
                type="email"
              />
            </div>
            <p v-if="error" class="text-error text-sm">{{ error }}</p>
            <button
              class="w-full bg-primary-container text-[#0A0A0A] font-bold py-4 px-6 font-label-caps text-label-caps hover:bg-primary transition-all active:scale-[0.98] duration-150 disabled:opacity-70"
              type="submit"
              :disabled="loading"
            >
              {{ loading ? 'SENDING...' : 'SEND RESET LINK' }}
            </button>
          </form>
          <div v-else class="space-y-4">
            <p class="text-on-surface-variant font-body-lg">
              If an account exists for <strong class="text-on-surface">{{ email }}</strong>, a
              recovery link has been sent.
            </p>
          </div>
          <div class="mt-stack-lg pt-stack-lg border-t border-outline-variant text-center">
            <RouterLink
              class="font-body-sm text-body-sm text-primary hover:underline underline-offset-4"
              to="/login"
              >Back to login</RouterLink
            >
          </div>
        </div>
      </div>
    </section>
  </div>
</template>
