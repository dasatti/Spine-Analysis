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

export const getDashboardSummary = () => api.get('/dashboard/summary')
export const getSettings = () => api.get('/settings')
export const updateDetectorSettings = (payload) => api.put('/settings/detector', payload)
