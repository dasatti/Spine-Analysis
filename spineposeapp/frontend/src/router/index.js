import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const routes = [
  { path: '/login', component: () => import('../views/LoginView.vue'), meta: { guest: true } },
  { path: '/register', component: () => import('../views/RegisterView.vue'), meta: { guest: true } },
  {
    path: '/forgot-password',
    component: () => import('../views/ForgotPasswordView.vue'),
    meta: { guest: true },
  },
  { path: '/', redirect: '/dashboard' },
  { path: '/dashboard', component: () => import('../views/DashboardView.vue'), meta: { auth: true } },
  { path: '/patients', component: () => import('../views/PatientsView.vue'), meta: { auth: true } },
  { path: '/patients/new', component: () => import('../views/PatientFormView.vue'), meta: { auth: true } },
  {
    path: '/patients/:id/edit',
    component: () => import('../views/PatientFormView.vue'),
    meta: { auth: true },
  },
  {
    path: '/patients/:id',
    component: () => import('../views/PatientProfileView.vue'),
    meta: { auth: true },
  },
  { path: '/scans/new', component: () => import('../views/ScanSetupView.vue'), meta: { auth: true } },
  {
    path: '/scans/:id/capture',
    component: () => import('../views/ScanCaptureView.vue'),
    meta: { auth: true },
  },
  {
    path: '/scans/:id/processing',
    component: () => import('../views/ScanProcessingView.vue'),
    meta: { auth: true },
  },
  { path: '/scans/:id/export', component: () => import('../views/ReportExportView.vue'), meta: { auth: true } },
  { path: '/scans/:id', component: () => import('../views/ScanResultsView.vue'), meta: { auth: true } },
  { path: '/scans', component: () => import('../views/ScanHistoryView.vue'), meta: { auth: true } },
  { path: '/reports', component: () => import('../views/ReportsLibraryView.vue'), meta: { auth: true } },
  { path: '/settings', component: () => import('../views/SettingsView.vue'), meta: { auth: true } },
  { path: '/help', component: () => import('../views/HelpView.vue'), meta: { auth: true } },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach(async (to) => {
  const authStore = useAuthStore()
  if (authStore.token && !authStore.doctor) {
    try {
      await authStore.fetchMe()
    } catch {
      authStore.logout()
    }
  }
  if (to.meta.auth && !authStore.isAuthenticated) return '/login'
  if (to.meta.guest && authStore.isAuthenticated) return '/dashboard'
})

export default router
