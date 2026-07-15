import { API_CONFIG, API_ENDPOINTS } from '../config/api.js'
import { authService } from './auth.js'

class ApiService {
  constructor() {
    this.baseURL = API_CONFIG.baseURL
    this.timeout = API_CONFIG.timeout
  }

  _getAuthHeaders() {
    const token = authService.accessToken
    return token ? { 'Authorization': `Bearer ${token}` } : {}
  }

  async request(url, options = {}) {
    const timeoutController = new AbortController()
    const timeoutId = setTimeout(() => timeoutController.abort(), this.timeout)
    const externalSignal = options.signal

    const signal = externalSignal
      ? this._combinedSignal(externalSignal, timeoutController.signal)
      : timeoutController.signal

    delete options.signal

    const headers = {
      ...API_CONFIG.headers,
      ...this._getAuthHeaders(),
      ...options.headers
    }

    if (options.body instanceof FormData) {
      delete headers['Content-Type']
    }

    try {
      const response = await fetch(`${this.baseURL}${url}`, {
        ...options,
        headers,
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

  async delete(url) {
    return this.request(url, { method: 'DELETE' })
  }
  async health() {
    const response = await this.get(API_ENDPOINTS.health)
    return response.json()
  }

  async getThemes() {
    const response = await this.get(API_ENDPOINTS.themes)
    return response.json()
  }

  async getLLMConfig() {
    const response = await this.get(API_ENDPOINTS.auth.llmConfig)
    return response.json()
  }

  async updateLLMConfig(data) {
    const response = await this.put(API_ENDPOINTS.auth.llmConfig, data)
    return response.json()
  }

  async createPresentation(topic, useRag = true) {
    const response = await this.post(API_ENDPOINTS.presentations.create, {
      topic,
      use_rag: useRag
    })
    return response.json()
  }

  async getPresentation(id) {
    const response = await this.get(API_ENDPOINTS.presentations.get(id))
    return response.json()
  }

  async getDsl(id) {
    const response = await this.get(API_ENDPOINTS.presentations.getDsl(id))
    return response.json()
  }
  async getRenderTree(id) {
    const response = await this.get(API_ENDPOINTS.presentations.getRenderTree(id))
    return response.json()
  }

  async patchComponent(presentationId, componentId, patchData) {
    const response = await this.patch(
      API_ENDPOINTS.presentations.patchComponent(presentationId, componentId),
      patchData
    )
    return response.json()
  }
  async reorderSlides(id, slideIds) {
    const response = await this.patch(API_ENDPOINTS.presentations.reorderSlides(id), {
      slideIds
    })
    return response.json()
  }

  async switchTheme(id, themeName, rerender = false) {
    const response = await this.put(API_ENDPOINTS.presentations.switchTheme(id), {
      themeName,
      rerender
    })
    return response.json()
  }

  async regenerate(id, topic = null, section = null, useRag = true) {
    const response = await this.post(API_ENDPOINTS.presentations.regenerate(id), {
      topic,
      section,
      use_rag: useRag
    })
    return response.json()
  }

  async exportPptx(id) {
    const response = await this.post(API_ENDPOINTS.presentations.exportPptx(id))
    const blob = await response.blob()
    return blob
  }

  async generateOutline(topic, theme = null, useRag = true, signal = null, modelProvider = 'deepseek', pageCountPreset = 'medium') {
    const response = await this.request(API_ENDPOINTS.dsl, {
      method: 'POST',
      body: JSON.stringify({ topic, theme, use_rag: useRag, modelProvider, pageCountPreset }),
      signal
    })
    return response.json()
  }
  async compileOutline(topic, outline, theme = null) {
    const response = await this.post(API_ENDPOINTS.renderTree, {
      topic,
      outline,
      theme
    })
    return response.json()
  }

  async listPresentations() {
    const response = await this.get(API_ENDPOINTS.presentations.list)
    return response.json()
  }


  async ragSearch(query, topK = 5, enableWeb = true, enableLocal = true, deepFetch = true) {
    const response = await this.post(API_ENDPOINTS.rag.search, {
      query, top_k: topK, enable_web: enableWeb, enable_local: enableLocal, deep_fetch: deepFetch
    })
    return response.json()
  }

  async ragEnhance(query, topK = 5, enableWeb = true, enableLocal = true, deepFetch = true) {
    const response = await this.post(API_ENDPOINTS.rag.enhance, {
      query, top_k: topK, enable_web: enableWeb, enable_local: enableLocal, deep_fetch: deepFetch
    })
    return response.json()
  }

  async ragUploadDocument(file, force = false) {
    const formData = new FormData()
    formData.append('file', file)
    if (force) formData.append('force', 'true')
    const response = await this.request(API_ENDPOINTS.rag.documents, {
      method: 'POST',
      headers: { ...this._getAuthHeaders() },
      body: formData
    })
    return response.json()
  }

  async ragListSources() {
    const response = await this.get(API_ENDPOINTS.rag.sources)
    return response.json()
  }

  async ragDeleteDocument(source) {
    const response = await this.delete(API_ENDPOINTS.rag.documentDelete(source))
    return response.json()
  }

  async ragClearAll() {
    const response = await this.delete(API_ENDPOINTS.rag.documentsClear)
    return response.json()
  }

  async ragStats() {
    const response = await this.get(API_ENDPOINTS.rag.stats)
    return response.json()
  }

  async ragInitCollection() {
    const response = await this.post(API_ENDPOINTS.rag.collectionInit)
    return response.json()
  }

  async ragResetCollection() {
    const response = await this.post(API_ENDPOINTS.rag.collectionReset)
    return response.json()
  }

  async ragBootstrap(maxArticlesPerTopic = 3, maxTopics = 0) {
    const response = await this.post(API_ENDPOINTS.rag.bootstrap, {
      max_articles_per_topic: maxArticlesPerTopic,
      max_topics: maxTopics
    })
    return response.json()
  }

  async getTaskStatus(taskId) {
    const response = await this.get(API_ENDPOINTS.rag.taskStatus(taskId))
    return response.json()
  }

  async getImportTaskStatus(taskId) {
    return this.getTaskStatus(taskId)
  }


  async evalSingle(presentationId, referenceText = null, enableLlmJudge = true, metrics = null) {
    const response = await this.post(API_ENDPOINTS.eval.single(presentationId), {
      reference_text: referenceText,
      enable_llm_judge: enableLlmJudge,
      metrics
    })
    return response.json()
  }

  async evalBatch(configs, topics, metrics = null, referenceTexts = {}) {
    const response = await this.post(API_ENDPOINTS.eval.batch, {
      configs, topics, metrics, reference_texts: referenceTexts
    })
    return response.json()
  }


  async dslFromDocument(filename, content, modelProvider = 'deepseek', pageCountPreset = 'medium') {
    const response = await this.post(API_ENDPOINTS.dslFromDocument, { filename, content, modelProvider, pageCountPreset })
    return response.json()
  }

  async generateOutlineFromDocument(file, theme = null, signal = null, modelProvider = 'deepseek', pageCountPreset = 'medium') {
    const formData = new FormData()
    formData.append('file', file)
    if (theme) formData.append('theme', theme)
    formData.append('modelProvider', modelProvider)
    formData.append('pageCountPreset', pageCountPreset)
    const response = await this.request(API_ENDPOINTS.dslFromDocument, {
      method: 'POST',
      body: formData,
      signal
    })
    return response.json()
  }


  async listOutlines() {
    const response = await this.get(API_ENDPOINTS.outlines.list)
    return response.json()
  }

  async getOutline(id) {
    const response = await this.get(API_ENDPOINTS.outlines.get(id))
    return response.json()
  }

  async createOutline(data) {
    const response = await this.post(API_ENDPOINTS.outlines.create, data)
    return response.json()
  }

  async updateOutline(id, data) {
    const response = await this.put(API_ENDPOINTS.outlines.update(id), data)
    return response.json()
  }

  async deleteOutline(id) {
    const response = await this.delete(API_ENDPOINTS.outlines.delete(id))
    return response.json()
  }


  async getKBDocuments() {
    const response = await this.get(API_ENDPOINTS.rag.documents)
    return response.json()
  }

  async uploadDocumentsToKB(files) {
    const formData = new FormData()
    files.forEach(file => formData.append('files', file))
    const response = await this.request(API_ENDPOINTS.rag.documentsBatch, {
      method: 'POST',
      body: formData
    })
    return response.json()
  }

  async previewKBDocument(source) {
    const response = await this.get(API_ENDPOINTS.rag.documentPreview(source))
    return response.json()
  }

  async removeKBDocument(source) {
    return this.ragDeleteDocument(source)
  }

  async clearAllKBDocuments() {
    return this.ragClearAll()
  }
}

export const apiService = new ApiService()
