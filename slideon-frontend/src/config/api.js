// API 配置

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? ''

export const API_CONFIG = {
  baseURL: API_BASE_URL,
  timeout: 600000,
  headers: {
    'Content-Type': 'application/json'
  }
}

// API 端点
export const API_ENDPOINTS = {
  // 健康检查
  health: '/health',

  // 主题相关
  themes: '/themes',

  // 大纲相关
  dsl: '/dsl',
  renderTree: '/render-tree',
  outlines: {
    list: '/outlines',
    create: '/outlines',
    get: (id) => `/outlines/${id}`,
    update: (id) => `/outlines/${id}`,
    delete: (id) => `/outlines/${id}`
  },

  // 认证相关
  auth: {
    register: '/auth/register',
    login: '/auth/login',
    refresh: '/auth/refresh',
    me: '/auth/me',
    llmConfig: '/auth/llm-config',
    logout: '/auth/logout'
  },

  // 演示文稿相关
  presentations: {
    list: '/presentations',
    create: '/presentations',
    get: (id) => `/presentations/${id}`,
    getDsl: (id) => `/presentations/${id}/dsl`,
    getRenderTree: (id) => `/presentations/${id}/render-tree`,
    patchComponent: (presentationId, componentId) => `/presentations/${presentationId}/components/${componentId}`,
    reorderSlides: (id) => `/presentations/${id}/slides/reorder`,
    switchTheme: (id) => `/presentations/${id}/theme`,
    regenerate: (id) => `/presentations/${id}/regenerate`,
    exportPptx: (id) => `/presentations/${id}/export/pptx`
  },

  // 知识库相关
  rag: {
    search: '/rag/search',
    enhance: '/rag/enhance',
    documents: '/rag/documents',
    documentsBatch: '/rag/documents/batch',
    documentPreview: (source) => `/rag/documents/${encodeURIComponent(source)}/preview`,
    documentDelete: (source) => `/rag/documents/${encodeURIComponent(source)}`,
    documentsClear: '/rag/documents',
    sources: '/rag/sources',
    taskStatus: (taskId) => `/rag/tasks/${taskId}`,
    stats: '/rag/stats',
    collectionInit: '/rag/collection/init',
    collectionReset: '/rag/collection/reset',
    bootstrap: '/rag/bootstrap'
  },

  // 文档导入生成大纲
  dslFromDocument: '/dsl/from-document',

  // 评估相关
  eval: {
    single: (presentationId) => `/eval/single/${presentationId}`,
    batch: '/eval/batch'
  }
}

// WebSocket 配置
export const WS_CONFIG = {
  url: import.meta.env.VITE_WS_URL || 'ws://localhost:8000/ws',
  reconnectInterval: 3000,
  maxReconnectAttempts: 5
}

// 文件上传配置
export const UPLOAD_CONFIG = {
  maxFileSize: parseInt(import.meta.env.VITE_MAX_FILE_SIZE) || 20 * 1024 * 1024, // 20MB
  allowedTypes: ['.pdf', '.docx', '.txt', '.md', '.doc', '.pptx'],
  maxFiles: 10
}
