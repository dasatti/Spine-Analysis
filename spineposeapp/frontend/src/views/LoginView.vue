<script setup>
import { ref } from 'vue'
import { RouterLink, useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const email = ref('')
const password = ref('')
const remember = ref(false)
const showPassword = ref(false)
const error = ref('')

async function onSubmit() {
  error.value = ''
  try {
    await authStore.login(email.value, password.value)
    router.push(authStore.isAdmin ? '/admin/dashboard' : '/dashboard')
  } catch (e) {
    error.value = e.response?.data?.detail || 'Authentication failed. Check your credentials.'
  }
}
</script>

<template>
  <div class="flex h-screen w-full overflow-hidden">
    <section
      class="relative hidden md:flex w-1/2 h-full bg-[#0A0A0A] flex-col justify-center px-margin-desktop border-r border-outline-variant"
    >
      <div
        class="absolute inset-0 opacity-10 wireframe-bg pointer-events-none overflow-hidden"
      >
        <img
          class="w-full h-full object-cover grayscale invert"
          src="https://lh3.googleusercontent.com/aida-public/AB6AXuAkdQeE0pz-0GlDkWsr8WIO5Y7Rq7LjsYEwM9pr-fYMrtwq8SSBj7YnP1FzLGiB6jTRyhqkeWVjVABYDOjWX0c_sSBzOSSRqtRqucqV7Mo24CufDmNgXeKDdYRNUMu0wIYw211Wl93NU-AQrSpTV3lthwiq0Eq_znMGNenBfN6931_zQC5Rd97N6D5pFuZ-sswpnGOgD9Ubnn_-0r21OYjRZ12kMPqyK3R46D29M1XrotMduhatrdM"
          alt=""
        />
      </div>
      <div class="relative z-10 max-w-lg">
        <div class="flex items-center gap-stack-md mb-stack-lg">
          <span
            class="font-headline-md text-headline-md font-bold text-primary uppercase tracking-tighter"
            >SpinePose</span
          >
        </div>
        <div class="flex items-center gap-3 mb-stack-md">
          <div class="spine-bar"></div>
          <h1 class="font-headline-lg text-headline-lg text-on-background">
            AI-Powered Spine &amp; Posture Analysis
          </h1>
        </div>
        <p class="text-on-surface-variant font-body-lg text-body-lg mb-10 max-w-md">
          Precision diagnostics through clinical-grade computer vision. Elevate patient outcomes
          with real-time biometric tracking.
        </p>
        <ul class="space-y-6">
          <li class="flex items-start gap-4">
            <span
              class="material-symbols-outlined text-primary-container mt-1"
              style="font-variation-settings: 'FILL' 1"
              >check_circle</span
            >
            <div>
              <span class="font-label-caps text-label-caps block text-on-surface mb-1"
                >REAL-TIME TELEMETRY</span
              >
              <p class="text-on-surface-variant">
                Instant analysis of L1-L5 spinal curvature and alignment.
              </p>
            </div>
          </li>
          <li class="flex items-start gap-4">
            <span
              class="material-symbols-outlined text-primary-container mt-1"
              style="font-variation-settings: 'FILL' 1"
              >check_circle</span
            >
            <div>
              <span class="font-label-caps text-label-caps block text-on-surface mb-1"
                >CLINICAL PRECISION</span
              >
              <p class="text-on-surface-variant">
                Validated algorithms for surgical-grade diagnostic accuracy.
              </p>
            </div>
          </li>
          <li class="flex items-start gap-4">
            <span
              class="material-symbols-outlined text-primary-container mt-1"
              style="font-variation-settings: 'FILL' 1"
              >check_circle</span
            >
            <div>
              <span class="font-label-caps text-label-caps block text-on-surface mb-1"
                >SECURE ECOSYSTEM</span
              >
              <p class="text-on-surface-variant">
                HIPAA-compliant data encryption and patient management.
              </p>
            </div>
          </li>
        </ul>
      </div>
      <div class="scanline"></div>
    </section>

    <section
      class="w-full md:w-1/2 h-full bg-[#1A1A1A] flex items-center justify-center p-margin-mobile"
    >
      <div class="w-full max-w-md">
        <div
          class="bg-[#2A2A2A] border border-outline-variant p-panel-padding shadow-2xl"
        >
          <div class="mb-stack-lg">
            <span class="font-label-caps text-label-caps text-primary block mb-2"
              >RESTRICTED ACCESS</span
            >
            <h2 class="font-headline-md text-headline-md text-on-surface">Clinical Login</h2>
          </div>
          <form class="space-y-6" @submit.prevent="onSubmit">
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
            <div class="relative">
              <label
                class="font-label-caps text-label-caps text-on-surface-variant block mb-2"
                for="password"
                >PASSWORD</label
              >
              <div class="relative">
                <input
                  id="password"
                  v-model="password"
                  class="w-full bg-[#0A0A0A] border border-outline-variant focus:border-primary-container focus:ring-0 text-on-surface font-metric-sm text-metric-sm px-4 py-3 pr-12 outline-none transition-all"
                  placeholder="••••••••"
                  required
                  :type="showPassword ? 'text' : 'password'"
                />
                <button
                  class="absolute right-4 top-1/2 -translate-y-1/2 text-on-surface-variant hover:text-on-surface transition-colors"
                  type="button"
                  @click="showPassword = !showPassword"
                >
                  <span class="material-symbols-outlined text-[20px]">{{
                    showPassword ? 'visibility_off' : 'visibility'
                  }}</span>
                </button>
              </div>
            </div>
            <div class="flex items-center justify-between">
              <label class="flex items-center gap-3 cursor-pointer group">
                <input
                  v-model="remember"
                  class="custom-checkbox w-4 h-4 bg-[#0A0A0A] border-outline-variant rounded-none focus:ring-0"
                  type="checkbox"
                />
                <span
                  class="font-body-sm text-body-sm text-on-surface-variant group-hover:text-on-surface transition-colors"
                  >Remember credentials</span
                >
              </label>
              <RouterLink
                class="font-body-sm text-body-sm text-primary hover:underline underline-offset-4"
                to="/forgot-password"
                >Forgot your password?</RouterLink
              >
            </div>
            <p v-if="error" class="text-error text-sm">{{ error }}</p>
            <button
              class="w-full bg-primary-container text-[#0A0A0A] font-bold py-4 px-6 font-label-caps text-label-caps hover:bg-primary transition-all active:scale-[0.98] duration-150 disabled:opacity-70"
              type="submit"
              :disabled="authStore.loading"
            >
              {{ authStore.loading ? 'AUTHENTICATING...' : 'SIGN IN TO PLATFORM' }}
            </button>
          </form>
          <div class="mt-stack-lg pt-stack-lg border-t border-outline-variant text-center">
            <p class="text-on-surface-variant">
              New to SpinePose?
              <RouterLink
                class="text-on-surface font-bold hover:text-primary transition-colors ml-1"
                to="/register"
                >Request access</RouterLink
              >
            </p>
          </div>
        </div>
        <div
          class="mt-8 flex justify-center gap-6 text-[10px] uppercase tracking-widest text-on-surface-variant/40 font-metric-sm"
        >
          <span>© 2026 SPINEPOSE AI</span>
          <span>SYSTEM ID: PX-901</span>
        </div>
      </div>
    </section>
  </div>
</template>
