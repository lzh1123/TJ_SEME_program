// API 配置

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8080/api'

export const API_CONFIG = {
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
}

// API 端点
export const API_ENDPOINTS = {
  // 用户相关
  auth: {
    login: '/auth/login',
    register: '/auth/register',
    logout: '/auth/logout',
    refresh: '/auth/refresh'
  },
  
  // PPT项目相关
  projects: {
    list: '/projects',
    create: '/projects',
    get: (id) => `/projects/${id}`,
    update: (id) => `/projects/${id}`,
    delete: (id) => `/projects/${id}`,
    save: (id) => `/projects/${id}/save`
  },
  
  // AI生成相关
  ai: {
    generateOutline: '/ai/generate-outline',
    generateContent: '/ai/generate-content',
    optimize: '/ai/optimize',
    chat: '/ai/chat'
  },
  
  // 文件上传相关
  upload: {
    file: '/upload/file',
    image: '/upload/image'
  },
  
  // 模板相关
  templates: {
    list: '/templates',
    categories: '/templates/categories'
  }
}

// WebSocket 配置
export const WS_CONFIG = {
  url: import.meta.env.VITE_WS_URL || 'ws://localhost:8080/ws',
  reconnectInterval: 3000,
  maxReconnectAttempts: 5
}

// 文件上传配置
export const UPLOAD_CONFIG = {
  maxFileSize: parseInt(import.meta.env.VITE_MAX_FILE_SIZE) || 20 * 1024 * 1024, // 20MB
  allowedTypes: ['.pdf', '.docx', '.txt', '.md', '.doc', '.pptx'],
  maxFiles: 10
}
