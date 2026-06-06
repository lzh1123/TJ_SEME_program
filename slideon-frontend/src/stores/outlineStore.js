import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { new_id } from '../utils/ids.js'

const INDEX_KEY = 'slideon_outlines_index'
const OUTLINE_PREFIX = 'slideon_outline_'

export const useOutlineStore = defineStore('outline', () => {
  // ── state ──
  const outlines = ref([]) // index list: [{id, title, slideCount, createdAt, updatedAt}, ...]

  // ── private helpers ──
  function loadIndex() {
    try {
      const raw = localStorage.getItem(INDEX_KEY)
      if (raw) {
        outlines.value = JSON.parse(raw)
      }
    } catch (e) {
      console.error('加载大纲索引失败:', e)
      outlines.value = []
    }
  }

  function saveIndex() {
    try {
      localStorage.setItem(INDEX_KEY, JSON.stringify(outlines.value))
    } catch (e) {
      console.error('保存大纲索引失败:', e)
    }
  }

  // ── actions ──

  /** 加载所有大纲元数据 */
  function loadOutlines() {
    loadIndex()
    return outlines.value
  }

  /** 根据 ID 获取单个大纲完整 DSL */
  function getOutline(id) {
    try {
      const raw = localStorage.getItem(OUTLINE_PREFIX + id)
      if (raw) {
        return JSON.parse(raw)
      }
    } catch (e) {
      console.error('加载大纲失败:', id, e)
    }
    return null
  }

  /** 创建新大纲并保存到 localStorage */
  function createOutline(dsl) {
    const id = new_id('outline')
    const now = new Date().toISOString()

    const entry = {
      id,
      title: dsl.title || '未命名大纲',
      slideCount: (dsl.slides && dsl.slides.length) || 0,
      createdAt: now,
      updatedAt: now
    }

    // 确保 slides 中每个 slide 都有 id
    if (dsl.slides) {
      dsl.slides = dsl.slides.map((slide, idx) => ({
        ...slide,
        id: slide.id || new_id('slide'),
        section: slide.section || ''
      }))
    }

    outlines.value.unshift(entry)
    saveIndex()
    localStorage.setItem(OUTLINE_PREFIX + id, JSON.stringify(dsl))

    return { id, entry }
  }

  /** 保存（更新）已有大纲 */
  function saveOutline(id, dsl) {
    const now = new Date().toISOString()
    const index = outlines.value.findIndex(o => o.id === id)

    if (index !== -1) {
      outlines.value[index] = {
        ...outlines.value[index],
        title: dsl.title || outlines.value[index].title,
        slideCount: (dsl.slides && dsl.slides.length) || 0,
        updatedAt: now
      }
      saveIndex()
    }

    // 确保 slides 中每个 slide 都有 id
    if (dsl.slides) {
      dsl.slides = dsl.slides.map((slide, idx) => ({
        ...slide,
        id: slide.id || new_id('slide'),
        section: slide.section || ''
      }))
    }

    localStorage.setItem(OUTLINE_PREFIX + id, JSON.stringify(dsl))
    return true
  }

  /** 删除大纲 */
  function deleteOutline(id) {
    outlines.value = outlines.value.filter(o => o.id !== id)
    saveIndex()
    localStorage.removeItem(OUTLINE_PREFIX + id)
  }

  /** 检查大纲是否存在 */
  function hasOutline(id) {
    return localStorage.getItem(OUTLINE_PREFIX + id) !== null
  }

  // 初始化加载
  loadIndex()

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
