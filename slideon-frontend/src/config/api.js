// API 配置

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

export const API_CONFIG = {
  baseURL: API_BASE_URL,
  timeout: 180000,
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

  // 演示文稿相关
  presentations: {
    create: '/presentations',
    get: (id) => `/presentations/${id}`,
    getDsl: (id) => `/presentations/${id}/dsl`,
    getRenderTree: (id) => `/presentations/${id}/render-tree`,
    patchComponent: (presentationId, componentId) => `/presentations/${presentationId}/components/${componentId}`,
    reorderSlides: (id) => `/presentations/${id}/slides/reorder`,
    switchTheme: (id) => `/presentations/${id}/theme`,
    regenerate: (id) => `/presentations/${id}/regenerate`,
    exportPptx: (id) => `/presentations/${id}/export/pptx`
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
