import { defineStore } from 'pinia'
import { ref } from 'vue'
import { new_id } from '../utils/ids.js'
import { authService } from '../services/auth.js'
import { apiService } from '../services/api.js'

const INDEX_KEY = 'slideon_outlines_index'
const OUTLINE_PREFIX = 'slideon_outline_'

export const useOutlineStore = defineStore('outline', () => {
  // ── state ──
  const outlines = ref([])

  // ── helpers ──
  function isLoggedIn() {
    return authService.isAuthenticated
  }

  function loadLocalIndex() {
    try {
      const raw = localStorage.getItem(INDEX_KEY)
      if (raw) return JSON.parse(raw)
    } catch (e) {
      console.error('加载大纲索引失败:', e)
    }
    return []
  }

  function saveLocalIndex() {
    try {
      localStorage.setItem(INDEX_KEY, JSON.stringify(outlines.value))
    } catch (e) {
      console.error('保存大纲索引失败:', e)
    }
  }

  function ensureSlideIds(dsl) {
    if (dsl.slides) {
      dsl.slides = dsl.slides.map((slide) => ({
        ...slide,
        id: slide.id || new_id('slide'),
        section: slide.section || ''
      }))
    }
    return dsl
  }

  // ── actions (sync by default, async sync to cloud in background) ──

  /** 加载大纲索引：优先云端，失败回退本地 */
  async function loadOutlines() {
    if (isLoggedIn()) {
      try {
        const data = await apiService.listOutlines()
        outlines.value = data
        return outlines.value
      } catch (e) {
        console.error('云端加载大纲失败，回退本地:', e)
      }
    }
    outlines.value = loadLocalIndex()
    return outlines.value
  }

  /** 获取单个大纲：先查本地，再查云端 */
  async function getOutline(id) {
    // 1) 先查本地 localStorage（即时返回）
    try {
      const raw = localStorage.getItem(OUTLINE_PREFIX + id)
      if (raw) return JSON.parse(raw)
    } catch (e) {
      console.error('加载大纲失败:', id, e)
    }

    // 2) 再查云端
    if (isLoggedIn()) {
      try {
        const data = await apiService.getOutline(id)
        if (data && data.dsl) {
          const dsl = typeof data.dsl === 'string' ? JSON.parse(data.dsl) : data.dsl
          // 缓存到本地
          localStorage.setItem(OUTLINE_PREFIX + id, JSON.stringify(dsl))
          return dsl
        }
      } catch (e) {
        console.error('云端获取大纲失败:', e)
      }
    }
    return null
  }

  /** 创建大纲：先存本地（同步返回），后台同步云端 */
  function createOutline(dsl) {
    const id = new_id('outline')
    const now = new Date().toISOString()

    ensureSlideIds(dsl)

    const entry = {
      id,
      title: dsl.title || '未命名大纲',
      slideCount: (dsl.slides && dsl.slides.length) || 0,
      createdAt: now,
      updatedAt: now
    }

    // 立即存本地（同步）
    outlines.value.unshift({ ...entry })
    saveLocalIndex()
    localStorage.setItem(OUTLINE_PREFIX + id, JSON.stringify(dsl))

    // 后台异步同步云端
    if (isLoggedIn()) {
      apiService.createOutline({
        id,
        title: entry.title,
        dsl: JSON.stringify(dsl),
        slide_count: entry.slideCount
      }).catch(e => console.error('云端保存大纲失败:', e))
    }

    return { id, entry }
  }

  /** 更新大纲 */
  function saveOutline(id, dsl) {
    const now = new Date().toISOString()

    ensureSlideIds(dsl)

    const index = outlines.value.findIndex(o => o.id === id)
    if (index !== -1) {
      outlines.value[index] = {
        ...outlines.value[index],
        title: dsl.title || outlines.value[index].title,
        slideCount: (dsl.slides && dsl.slides.length) || 0,
        updatedAt: now
      }
    }

    // 立即存本地（同步）
    saveLocalIndex()
    localStorage.setItem(OUTLINE_PREFIX + id, JSON.stringify(dsl))

    // 后台异步同步云端
    if (isLoggedIn()) {
      apiService.updateOutline(id, {
        title: dsl.title || '未命名大纲',
        dsl: JSON.stringify(dsl),
        slide_count: (dsl.slides && dsl.slides.length) || 0
      }).catch(e => console.error('云端更新大纲失败:', e))
    }
    return true
  }

  /** 删除大纲 */
  function deleteOutline(id) {
    outlines.value = outlines.value.filter(o => o.id !== id)

    // 立即删本地（同步）
    saveLocalIndex()
    localStorage.removeItem(OUTLINE_PREFIX + id)

    // 后台异步同步云端
    if (isLoggedIn()) {
      apiService.deleteOutline(id)
        .catch(e => console.error('云端删除大纲失败:', e))
    }
  }

  /** 检查大纲是否存在 */
  function hasOutline(id) {
    return localStorage.getItem(OUTLINE_PREFIX + id) !== null
  }

  // 初始化
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
