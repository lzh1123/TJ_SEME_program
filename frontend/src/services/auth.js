// 认证相关 API 端点
import { API_CONFIG } from '../config/api.js'

const AUTH_BASE = `${API_CONFIG.baseURL}/auth`

class AuthService {
  constructor() {
    this._accessToken = localStorage.getItem('access_token') || null
    this._refreshToken = localStorage.getItem('refresh_token') || null
  }

  get accessToken() {
    return this._accessToken
  }

  get isAuthenticated() {
    return !!this._accessToken
  }

  _setTokens(accessToken, refreshToken) {
    this._accessToken = accessToken
    this._refreshToken = refreshToken
    localStorage.setItem('access_token', accessToken)
    localStorage.setItem('refresh_token', refreshToken)
  }

  _clearTokens() {
    this._accessToken = null
    this._refreshToken = null
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
  }

  async _request(url, options = {}) {
    const headers = { 'Content-Type': 'application/json' }
    if (this._accessToken) {
      headers['Authorization'] = `Bearer ${this._accessToken}`
    }

    const response = await fetch(`${AUTH_BASE}${url}`, {
      ...options,
      headers: { ...headers, ...options.headers }
    })

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: response.statusText }))
      throw new Error(error.detail || `HTTP ${response.status}`)
    }

    return response.json()
  }

  // ── 注册 ──
  async register(username, email, password, displayName = null) {
    const data = await this._request('/register', {
      method: 'POST',
      body: JSON.stringify({
        username,
        email,
        password,
        display_name: displayName
      })
    })
    return data
  }

  // ── 登录 ──
  async login(username, password) {
    const data = await this._request('/login', {
      method: 'POST',
      body: JSON.stringify({ username, password })
    })
    this._setTokens(data.access_token, data.refresh_token)
    return data
  }

  // ── 刷新令牌 ──
  async refresh() {
    if (!this._refreshToken) {
      throw new Error('No refresh token available')
    }
    try {
      const data = await this._request('/refresh', {
        method: 'POST',
        body: JSON.stringify({ refreshToken: this._refreshToken })
      })
      this._setTokens(data.access_token, data.refresh_token)
      return data
    } catch (e) {
      this._clearTokens()
      throw e
    }
  }

  // ── 获取当前用户信息 ──
  async getMe() {
    return this._request('/me', { method: 'GET' })
  }

  // ── 登出 ──
  async logout() {
    try {
      await this._request('/logout', { method: 'POST' })
    } catch (e) {
      // ignore errors during logout
    }
    this._clearTokens()
  }
}

export const authService = new AuthService()
