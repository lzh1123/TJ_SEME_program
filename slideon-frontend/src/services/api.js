import { API_CONFIG, API_ENDPOINTS } from '../config/api.js'

class ApiService {
  constructor() {
    this.baseURL = API_CONFIG.baseURL
    this.timeout = API_CONFIG.timeout
  }

  async request(url, options = {}) {
    const controller = new AbortController()
    const timeoutId = setTimeout(() => controller.abort(), this.timeout)

    try {
      const response = await fetch(`${this.baseURL}${url}`, {
        ...options,
        headers: {
          ...API_CONFIG.headers,
          ...options.headers
        },
        signal: controller.signal
      })

      clearTimeout(timeoutId)

      if (!response.ok) {
        const errorText = await response.text()
        throw new Error(`HTTP ${response.status}: ${errorText || response.statusText}`)
      }

      return response
    } catch (error) {
      clearTimeout(timeoutId)
      if (error.name === 'AbortError') {
        throw new Error('Request timeout')
      }
      throw error
    }
  }

  async get(url) {
    return this.request(url, { method: 'GET' })
  }

  async post(url, data) {
    return this.request(url, {
      method: 'POST',
      body: data ? JSON.stringify(data) : undefined
    })
  }

  async put(url, data) {
    return this.request(url, {
      method: 'PUT',
      body: data ? JSON.stringify(data) : undefined
    })
  }

  async patch(url, data) {
    return this.request(url, {
      method: 'PATCH',
      body: data ? JSON.stringify(data) : undefined
    })
  }

  // 健康检查
  async health() {
    const response = await this.get(API_ENDPOINTS.health)
    return response.json()
  }

  // 获取主题列表
  async getThemes() {
    const response = await this.get(API_ENDPOINTS.themes)
    return response.json()
  }

  // 创建演示文稿
  async createPresentation(topic, useRag = true) {
    const response = await this.post(API_ENDPOINTS.presentations.create, {
      topic,
      use_rag: useRag
    })
    return response.json()
  }

  // 获取演示文稿
  async getPresentation(id) {
    const response = await this.get(API_ENDPOINTS.presentations.get(id))
    return response.json()
  }

  // 获取DSL
  async getDsl(id) {
    const response = await this.get(API_ENDPOINTS.presentations.getDsl(id))
    return response.json()
  }

  // 获取渲染树
  async getRenderTree(id) {
    const response = await this.get(API_ENDPOINTS.presentations.getRenderTree(id))
    return response.json()
  }

  // 编辑组件
  async patchComponent(presentationId, componentId, patchData) {
    const response = await this.patch(
      API_ENDPOINTS.presentations.patchComponent(presentationId, componentId),
      patchData
    )
    return response.json()
  }

  // 重排幻灯片
  async reorderSlides(id, slideIds) {
    const response = await this.patch(API_ENDPOINTS.presentations.reorderSlides(id), {
      slideIds
    })
    return response.json()
  }

  // 切换主题
  async switchTheme(id, themeName, rerender = false) {
    const response = await this.put(API_ENDPOINTS.presentations.switchTheme(id), {
      themeName,
      rerender
    })
    return response.json()
  }

  // 重新生成
  async regenerate(id, topic = null, section = null, useRag = true) {
    const response = await this.post(API_ENDPOINTS.presentations.regenerate(id), {
      topic,
      section,
      use_rag: useRag
    })
    return response.json()
  }

  // 导出PPTX
  async exportPptx(id) {
    const response = await this.post(API_ENDPOINTS.presentations.exportPptx(id))
    const blob = await response.blob()
    return blob
  }

  // 生成大纲
  async generateOutline(topic, theme = null, useRag = true) {
    const response = await this.post(API_ENDPOINTS.dsl, {
      topic,
      theme,
      use_rag: useRag
    })
    return response.json()
  }

  // 根据大纲生成渲染树
  async compileOutline(topic, outline, theme = null) {
    const response = await this.post(API_ENDPOINTS.renderTree, {
      topic,
      outline,
      theme
    })
    return response.json()
  }
}

export const apiService = new ApiService()
