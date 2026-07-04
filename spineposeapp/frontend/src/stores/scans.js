import { defineStore } from 'pinia'
import {
  createScan,
  deleteScan,
  getScan,
  getScanStatus,
  listScans,
  recomputeScan,
  resetScanKeypoints,
} from '../api/client'

export const useScansStore = defineStore('scans', {
  state: () => ({
    current: null,
    list: [],
    polling: false,
    loading: false,
    pollTimer: null,
  }),
  actions: {
    async createScan(formData) {
      this.loading = true
      try {
        const { data } = await createScan(formData)
        return data
      } finally {
        this.loading = false
      }
    },
    async fetchScan(scanId) {
      this.loading = true
      try {
        const { data } = await getScan(scanId)
        this.current = data
        return data
      } finally {
        this.loading = false
      }
    },
    async fetchList(params = {}) {
      this.loading = true
      try {
        const { data } = await listScans(params)
        this.list = data.items
        return data
      } finally {
        this.loading = false
      }
    },
    async deleteScan(scanId) {
      await deleteScan(scanId)
    },
    async recomputeScan(scanId, payload) {
      this.loading = true
      try {
        const { data } = await recomputeScan(scanId, payload)
        this.current = data
        return data
      } finally {
        this.loading = false
      }
    },
    async resetScanKeypoints(scanId, payload = {}) {
      this.loading = true
      try {
        const { data } = await resetScanKeypoints(scanId, payload)
        this.current = data
        return data
      } finally {
        this.loading = false
      }
    },
    pollStatus(scanId, onUpdate) {
      this.stopPolling()
      this.polling = true
      const poll = async () => {
        try {
          const { data } = await getScanStatus(scanId)
          onUpdate(data)
          if (data.status === 'completed' || data.status === 'failed') {
            this.stopPolling()
          }
        } catch {
          this.stopPolling()
        }
      }
      poll()
      this.pollTimer = setInterval(poll, 2000)
    },
    stopPolling() {
      if (this.pollTimer) {
        clearInterval(this.pollTimer)
        this.pollTimer = null
      }
      this.polling = false
    },
  },
})
