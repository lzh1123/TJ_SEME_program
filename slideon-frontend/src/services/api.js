import { API_CONFIG, API_ENDPOINTS } from '../config/api.js'

class ApiService {
  constructor() {
    this.baseURL = API_CONFIG.baseURL
    this.timeout = API_CONFIG.timeout
  }

  async request(url, options = {}) {
    const timeoutController = new AbortController()
    const timeoutId = setTimeout(() => timeoutController.abort(), this.timeout)
    const externalSignal = options.signal

    // Merge external signal with timeout signal
    const signal = externalSignal
      ? this._combinedSignal(externalSignal, timeoutController.signal)
      : timeoutController.signal

    delete options.signal

    try {
      const response = await fetch(`${this.baseURL}${url}`, {
        ...options,
        headers: {
          ...API_CONFIG.headers,
          ...options.headers
        },
        signal
      })

      clearTimeout(timeoutId)

      if (!response.ok) {
        let errorMessage = `HTTP ${response.status}: ${response.statusText}`
        try {
          const errorBody = await response.json()
          if (errorBody.detail) {
            errorMessage = errorBody.detail
          }
        } catch {
          // Fall back to raw text if JSON parse fails
          const errorText = await response.text()
          if (errorText) errorMessage = errorText
        }
        const error = new Error(errorMessage)
        error.status = response.status
        error.errorType = response.status === 504 ? 'timeout' : response.status === 503 ? 'server_busy' : 'error'
        throw error
      }

      return response
    } catch (error) {
      clearTimeout(timeoutId)
      if (error.name === 'AbortError') {
        // Re-throw AbortError so callers can distinguish cancel from timeout
        throw error
      }
      throw error
    }
  }

  _combinedSignal(signalA, signalB) {
    if (signalA.aborted || signalB.aborted) return AbortSignal.abort()
    const controller = new AbortController()
    const onAbort = () => controller.abort()
    signalA.addEventListener('abort', onAbort, { once: true })
    signalB.addEventListener('abort', onAbort, { once: true })
    return controller.signal
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

  // 生成大纲 (signal 可选，用于取消请求)
  async generateOutline(topic, theme = null, useRag = true, signal = null) {
    const response = await this.request(API_ENDPOINTS.dsl, {
      method: 'POST',
      body: JSON.stringify({ topic, theme, use_rag: useRag }),
      signal
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

  // ── 文档上传生成大纲 ──
  async generateOutlineFromDocument(file, theme = null, signal = null) {
    const formData = new FormData()
    formData.append('file', file)
    if (theme) formData.append('theme', theme)

    const response = await fetch(`${this.baseURL}${API_ENDPOINTS.dslFromDocument}`, {
      method: 'POST',
      body: formData,
      signal
    })
    if (!response.ok) {
      let detail = `HTTP ${response.status}`
      try { const err = await response.json(); detail = err.detail || detail } catch {}
      throw new Error(detail)
    }
    return response.json()
  }

  // ── 知识库管理 ──
  async uploadDocumentsToKB(files) {
    const formData = new FormData()
    files.forEach(f => formData.append('files', f))
    const response = await fetch(`${this.baseURL}${API_ENDPOINTS.rag.documentsBatch}`, {
      method: 'POST',
      body: formData
    })
    if (!response.ok) {
      let detail = `HTTP ${response.status}`
      try { const err = await response.json(); detail = err.detail || detail } catch {}
      throw new Error(detail)
    }
    return response.json()
  }

  async getImportTaskStatus(taskId) {
    const response = await this.get(API_ENDPOINTS.rag.taskStatus(taskId))
    return response.json()
  }

  async getKBDocuments() {
    const response = await this.get(API_ENDPOINTS.rag.documents)
    return response.json()
  }

  async removeKBDocument(source) {
    const response = await this.request(API_ENDPOINTS.rag.documentDelete(source), {
      method: 'DELETE'
    })
    return response.json()
  }

  async getKBStats() {
    const response = await this.get(API_ENDPOINTS.rag.stats)
    return response.json()
  }

  // ── 评估 ──
  async evaluatePresentation(presentationId, options = {}) {
    const response = await this.post(API_ENDPOINTS.eval.single(presentationId), {
      reference_text: options.referenceText || null,
      enable_llm_judge: options.enableLLMJudge !== false,
      metrics: options.metrics || null
    })
    return response.json()
  }

  async batchEvaluate(config) {
    const response = await this.post(API_ENDPOINTS.eval.batch, config)
    return response.json()
  }
}

export const apiService = new ApiService()
