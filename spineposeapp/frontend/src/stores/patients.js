import { defineStore } from 'pinia'
import {
  createPatient,
  deletePatient,
  getPatient,
  listPatients,
  updatePatient,
} from '../api/client'

export const usePatientsStore = defineStore('patients', {
  state: () => ({
    list: [],
    current: null,
    pagination: { total: 0, page: 1, page_size: 20, pages: 0 },
    loading: false,
  }),
  getters: {
    totalCount: (state) => state.pagination.total,
  },
  actions: {
    async fetchList(params = {}) {
      this.loading = true
      try {
        const { data } = await listPatients(params)
        this.list = data.items
        this.pagination = {
          total: data.total,
          page: data.page,
          page_size: data.page_size,
          pages: data.pages,
        }
        return data
      } finally {
        this.loading = false
      }
    },
    async fetchOne(id) {
      this.loading = true
      try {
        const { data } = await getPatient(id)
        this.current = data
        return data
      } finally {
        this.loading = false
      }
    },
    async create(payload) {
      const { data } = await createPatient(payload)
      return data
    },
    async update(id, payload) {
      const { data } = await updatePatient(id, payload)
      this.current = data
      return data
    },
    async softDelete(id) {
      await deletePatient(id)
    },
  },
})
