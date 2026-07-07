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
  {
    path: '/admin',
    redirect: '/admin/dashboard',
    meta: { auth: true, requiresAdmin: true },
  },
  {
    path: '/admin/dashboard',
    component: () => import('../views/admin/AdminDashboardView.vue'),
    meta: { auth: true, requiresAdmin: true },
  },
  {
    path: '/admin/doctors',
    component: () => import('../views/admin/AdminDoctorsView.vue'),
    meta: { auth: true, requiresAdmin: true },
  },
  {
    path: '/admin/doctors/:id/edit',
    component: () => import('../views/admin/AdminDoctorFormView.vue'),
    meta: { auth: true, requiresAdmin: true },
  },
  {
    path: '/admin/research/dataset',
    component: () => import('../views/admin/research/DatasetListView.vue'),
    meta: { auth: true, requiresAdmin: true },
  },
  {
    path: '/admin/research/dataset/:id/adjust',
    component: () => import('../views/admin/research/DatasetAdjustView.vue'),
    meta: { auth: true, requiresAdmin: true },
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach(async (to) => {
  const authStore = useAuthStore()
  const needsAuth = to.matched.some((record) => record.meta.auth)
  const needsAdmin = to.matched.some((record) => record.meta.requiresAdmin)

  if (authStore.token && (!authStore.doctor || (needsAdmin && authStore.doctor?.role == null))) {
    try {
      await authStore.fetchMe()
    } catch {
      authStore.logout()
    }
  }
  if (needsAuth && !authStore.isAuthenticated) return '/login'
  if (needsAdmin && !authStore.isAdmin) return '/dashboard'
  if (to.meta.guest && authStore.isAuthenticated) {
    return authStore.isAdmin ? '/admin/dashboard' : '/dashboard'
  }
})

export default router
