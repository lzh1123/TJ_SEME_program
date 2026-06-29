import { defineStore } from 'pinia'
import { ref } from 'vue'
import { new_id } from '../utils/ids.js'
import { authService } from '../services/auth.js'
import { apiService } from '../services/api.js'

const INDEX_KEY = 'slideon_outlines_index'
const OUTLINE_PREFIX = 'slideon_outline_'

export const useOutlineStore = defineStore('outline', () => {
  const outlines = ref([])

  function isLoggedIn() {
    return authService.isAuthenticated
  }

  function loadLocalIndex() {
    try {
      const raw = localStorage.getItem(INDEX_KEY)
      return raw ? JSON.parse(raw) : []
    } catch (e) {
      console.error('Failed to load local outline index:', e)
      return []
    }
  }

  function saveLocalIndex() {
    try {
      localStorage.setItem(INDEX_KEY, JSON.stringify(outlines.value))
    } catch (e) {
      console.error('Failed to save local outline index:', e)
    }
  }

  function cacheOutline(id, dsl) {
    try {
      localStorage.setItem(OUTLINE_PREFIX + id, JSON.stringify(dsl))
    } catch (e) {
      console.error('Failed to cache outline:', e)
    }
  }

  function removeCachedOutline(id) {
    try {
      localStorage.removeItem(OUTLINE_PREFIX + id)
    } catch {}
  }

  function normalizeEntry(entry, fallbackDsl = null) {
    const slideCount = entry.slideCount ?? entry.slide_count ?? fallbackDsl?.slides?.length ?? 0
    return {
      id: entry.id,
      title: entry.title || fallbackDsl?.title || '未命名大纲',
      slideCount,
      createdAt: entry.createdAt ?? entry.created_at ?? new Date().toISOString(),
      updatedAt: entry.updatedAt ?? entry.updated_at ?? new Date().toISOString(),
    }
  }

  function ensureSlideIds(dsl) {
    const copy = JSON.parse(JSON.stringify(dsl || {}))
    if (copy.slides) {
      copy.slides = copy.slides.map((slide) => ({
        ...slide,
        id: slide.id || new_id('slide'),
        section: slide.section || ''
      }))
    }
    return copy
  }

  function upsertLocalEntry(entry) {
    const normalized = normalizeEntry(entry)
    const index = outlines.value.findIndex(o => o.id === normalized.id)
    if (index === -1) {
      outlines.value.unshift(normalized)
    } else {
      outlines.value[index] = { ...outlines.value[index], ...normalized }
    }
    saveLocalIndex()
    return normalized
  }

  async function loadOutlines() {
    if (isLoggedIn()) {
      const data = await apiService.listOutlines()
      outlines.value = data.map(item => normalizeEntry(item))
      saveLocalIndex()
      return outlines.value
    }

    outlines.value = loadLocalIndex()
    return outlines.value
  }

  async function getOutline(id) {
    if (isLoggedIn()) {
      const data = await apiService.getOutline(id)
      const dsl = typeof data.dsl === 'string' ? JSON.parse(data.dsl) : data.dsl
      cacheOutline(id, dsl)
      upsertLocalEntry(data)
      return dsl
    }

    try {
      const raw = localStorage.getItem(OUTLINE_PREFIX + id)
      return raw ? JSON.parse(raw) : null
    } catch (e) {
      console.error('Failed to load local outline:', id, e)
      return null
    }
  }

  async function createOutline(dsl) {
    const normalizedDsl = ensureSlideIds(dsl)
    const localId = new_id('outline')
    const now = new Date().toISOString()
    const localEntry = {
      id: localId,
      title: normalizedDsl.title || '未命名大纲',
      slideCount: normalizedDsl.slides?.length || 0,
      createdAt: now,
      updatedAt: now,
    }

    if (isLoggedIn()) {
      const saved = await apiService.createOutline({
        id: localId,
        title: localEntry.title,
        dsl: JSON.stringify(normalizedDsl),
        slide_count: localEntry.slideCount
      })
      const entry = upsertLocalEntry(saved)
      cacheOutline(entry.id, normalizedDsl)
      return { id: entry.id, entry }
    }

    outlines.value.unshift(localEntry)
    saveLocalIndex()
    cacheOutline(localId, normalizedDsl)
    return { id: localId, entry: localEntry }
  }

  async function saveOutline(id, dsl) {
    const normalizedDsl = ensureSlideIds(dsl)
    const payload = {
      title: normalizedDsl.title || '未命名大纲',
      dsl: JSON.stringify(normalizedDsl),
      slide_count: normalizedDsl.slides?.length || 0
    }

    if (isLoggedIn()) {
      const saved = await apiService.updateOutline(id, payload)
      upsertLocalEntry(saved)
      cacheOutline(id, normalizedDsl)
      return true
    }

    const now = new Date().toISOString()
    const index = outlines.value.findIndex(o => o.id === id)
    const entry = {
      id,
      title: payload.title,
      slideCount: payload.slide_count,
      createdAt: index !== -1 ? outlines.value[index].createdAt : now,
      updatedAt: now
    }
    if (index !== -1) outlines.value[index] = entry
    else outlines.value.unshift(entry)
    saveLocalIndex()
    cacheOutline(id, normalizedDsl)
    return true
  }

  async function deleteOutline(id) {
    if (isLoggedIn()) {
      await apiService.deleteOutline(id)
    }

    outlines.value = outlines.value.filter(o => o.id !== id)
    saveLocalIndex()
    removeCachedOutline(id)
  }

  function hasOutline(id) {
    if (isLoggedIn()) return outlines.value.some(o => o.id === id)
    return localStorage.getItem(OUTLINE_PREFIX + id) !== null
  }

  outlines.value = loadLocalIndex()

  return {
    outlines,
    loadOutlines,
    getOutline,
    createOutline,
    saveOutline,
    deleteOutline,
    hasOutline
  }
})
