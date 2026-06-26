import { defineStore } from 'pinia'
import {
  changePassword,
  getMe,
  loginDoctor,
  registerDoctor,
  updateMe,
} from '../api/client'

const TOKEN_KEY = 'sp_token'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    token: localStorage.getItem(TOKEN_KEY),
    doctor: null,
    loading: false,
  }),
  getters: {
    isAuthenticated: (state) => Boolean(state.token),
    doctorFullName: (state) =>
      state.doctor ? `${state.doctor.first_name} ${state.doctor.last_name}` : '',
    doctorInitials: (state) => {
      if (!state.doctor) return ''
      return `${state.doctor.first_name[0]}${state.doctor.last_name[0]}`.toUpperCase()
    },
  },
  actions: {
    hydrate() {
      this.token = localStorage.getItem(TOKEN_KEY)
    },
    setToken(token) {
      this.token = token
      if (token) localStorage.setItem(TOKEN_KEY, token)
      else localStorage.removeItem(TOKEN_KEY)
    },
    async login(email, password) {
      this.loading = true
      try {
        const { data } = await loginDoctor(email, password)
        this.setToken(data.access_token)
        this.doctor = data.doctor
        return data
      } finally {
        this.loading = false
      }
    },
    async register(payload) {
      this.loading = true
      try {
        const { data } = await registerDoctor(payload)
        this.setToken(data.access_token)
        this.doctor = data.doctor
        return data
      } finally {
        this.loading = false
      }
    },
    async fetchMe() {
      if (!this.token) return null
      const { data } = await getMe()
      this.doctor = data
      return data
    },
    async updateProfile(payload) {
      const { data } = await updateMe(payload)
      this.doctor = data
      return data
    },
    async changePassword(current, next) {
      await changePassword({ current_password: current, new_password: next })
    },
    logout() {
      this.setToken(null)
      this.doctor = null
    },
  },
})
