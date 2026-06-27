import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { authService } from '../services/auth.js'

export const useAuthStore = defineStore('auth', () => {
  // ── State ──
  const user = ref(null)
  const loading = ref(false)
  const initialized = ref(false)

  // ── Getters ──
  const isAuthenticated = computed(() => !!user.value)

  // ── Actions ──

  /** 初始化：检查本地 token 并尝试获取用户信息 */
  async function init() {
    if (initialized.value) return
    loading.value = true
    try {
      if (authService.isAuthenticated) {
        user.value = await authService.getMe()
      }
    } catch (e) {
      // Token 无效或过期，尝试刷新
      try {
        await authService.refresh()
        user.value = await authService.getMe()
      } catch (_) {
        // 刷新也失败，清除状态
        user.value = null
      }
    } finally {
      loading.value = false
      initialized.value = true
    }
  }

  /** 登录 */
  async function login(username, password) {
    loading.value = true
    try {
      const data = await authService.login(username, password)
      user.value = data.user
      return data
    } finally {
      loading.value = false
    }
  }

  /** 注册 */
  async function register(username, email, password, displayName) {
    loading.value = true
    try {
      return await authService.register(username, email, password, displayName)
    } finally {
      loading.value = false
    }
  }

  /** 登出 */
  async function logout() {
    await authService.logout()
    user.value = null
  }

  return {
    user,
    loading,
    initialized,
    isAuthenticated,
    init,
    login,
    register,
    logout
  }
})
