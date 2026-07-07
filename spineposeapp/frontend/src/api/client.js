import axios from 'axios'
import router from '../router'

const baseURL = import.meta.env.VITE_API_URL ?? '/api/v1'

export const api = axios.create({ baseURL })

export function setupApiClient(authStore) {
  api.interceptors.request.use((config) => {
    if (authStore.token) {
      config.headers.Authorization = `Bearer ${authStore.token}`
    }
    return config
  })

  api.interceptors.response.use(
    (response) => response,
    (error) => {
      if (error.response?.status === 401) {
        authStore.logout()
        router.push('/login')
      }
      if (error.response?.status === 403 && router.currentRoute.value.path.startsWith('/admin')) {
        router.push('/dashboard')
      }
      if (error.response?.status === 422) {
        const fieldErrors = {}
        for (const item of error.response.data.detail || []) {
          const field = item.loc?.[item.loc.length - 1]
          if (field) fieldErrors[field] = item.msg
        }
        error.fieldErrors = fieldErrors
      }
      return Promise.reject(error)
    }
  )
}

export const registerDoctor = (payload) => api.post('/auth/register', payload)
export const loginDoctor = (email, password) => {
  const form = new URLSearchParams()
  form.append('username', email)
  form.append('password', password)
  return api.post('/auth/login', form, {
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
  })
}
export const getMe = () => api.get('/auth/me')
export const updateMe = (payload) => api.put('/auth/me', payload)
export const changePassword = (payload) => api.post('/auth/change-password', payload)
export const forgotPassword = (email) => api.post('/auth/forgot-password', { email })

export const createPatient = (payload) => api.post('/patients', payload)
export const listPatients = (params) => api.get('/patients', { params })
export const getPatient = (id) => api.get(`/patients/${id}`)
export const updatePatient = (id, payload) => api.put(`/patients/${id}`, payload)
export const deletePatient = (id) => api.delete(`/patients/${id}`)

export const createScan = (formData) =>
  api.post('/scans', formData, { headers: { 'Content-Type': 'multipart/form-data' } })
export const getScan = (id) => api.get(`/scans/${id}`)
export const getScanStatus = (id) => api.get(`/scans/${id}/status`)
export const listScans = (params) => api.get('/scans', { params })
export const listPatientScans = (patientId, params) =>
  api.get(`/patients/${patientId}/scans`, { params })
export const deleteScan = (id) => api.delete(`/scans/${id}`)
export const recomputeScan = (id, payload) => api.post(`/scans/${id}/recompute`, payload)
export const resetScanKeypoints = (id, payload = {}) =>
  api.post(`/scans/${id}/reset-keypoints`, payload)

export const getDashboardSummary = () => api.get('/dashboard/summary')
export const getSettings = () => api.get('/settings')
export const updateDetectorSettings = (payload) => api.put('/settings/detector', payload)

export const getAdminAnalytics = () => api.get('/admin/analytics/summary')
export const listAdminDoctors = (params) => api.get('/admin/doctors', { params })
export const getAdminDoctor = (id) => api.get(`/admin/doctors/${id}`)
export const updateAdminDoctor = (id, payload) => api.put(`/admin/doctors/${id}`, payload)
export const toggleDoctorStatus = (id, isActive) =>
  api.patch(`/admin/doctors/${id}/status`, { is_active: isActive })

export const listDatasetItems = (params) => api.get('/admin/dataset-items', { params })
export const createDatasetItems = (formData) =>
  api.post('/admin/dataset-items', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
export const getDatasetItem = (id) => api.get(`/admin/dataset-items/${id}`)
export const recomputeDatasetItem = (id, payload) =>
  api.post(`/admin/dataset-items/${id}/recompute`, payload)
export const resetDatasetItemKeypoints = (id, payload = {}) =>
  api.post(`/admin/dataset-items/${id}/reset-keypoints`, payload)
export const saveDatasetManualLabels = (id, payload) =>
  api.put(`/admin/dataset-items/${id}/manual-labels`, payload)
