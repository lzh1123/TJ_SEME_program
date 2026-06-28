<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/authStore.js'
import { authService } from '../services/auth.js'
import { apiService } from '../services/api.js'
import AppHeader from '../components/common/AppHeader.vue'

const router = useRouter()
const authStore = useAuthStore()

const loading = ref(true)
const saving = ref(false)
const error = ref('')
const success = ref('')
const user = ref(null)

const form = reactive({
  displayName: ''
})

onMounted(async () => {
  await authStore.init()
  if (!authStore.isAuthenticated) {
    router.push('/login')
    return
  }
  try {
    const data = await authService.getMe()
    user.value = data
    form.displayName = data.displayName || ''
  } catch (e) {
    error.value = '获取用户信息失败'
  } finally {
    loading.value = false
  }
})

async function handleSubmit() {
  error.value = ''
  success.value = ''
  saving.value = true
  try {
    const data = await apiService.request('/auth/me', {
      method: 'PUT',
      body: JSON.stringify({ displayName: form.displayName })
    })
    const result = await data.json()
    user.value = result
    authStore.user = result
    success.value = '个人信息已更新'
    setTimeout(() => { success.value = '' }, 3000)
  } catch (e) {
    error.value = e.message || '更新失败'
  } finally {
    saving.value = false
  }
}

async function handleLogout() {
  await authStore.logout()
  router.push('/login')
}
</script>

<template>
  <AppHeader />
  <div class="profile-page">
    <div class="profile-container">
      <h1 class="page-title">个人信息</h1>

      <div v-if="loading" class="loading-state">
        <div class="spinner"></div>
        <p>加载中...</p>
      </div>

      <template v-else-if="user">
        <!-- 用户基本信息卡片 -->
        <div class="card info-card">
          <div class="avatar-section">
            <div class="avatar">{{ (user.displayName || user.username)[0].toUpperCase() }}</div>
            <div class="avatar-info">
              <h2 class="display-name">{{ user.displayName || user.username }}</h2>
              <p class="username">@{{ user.username }}</p>
            </div>
          </div>
        </div>

        <!-- 登录状态卡片 -->
        <div class="card status-card">
          <h3 class="card-title">登录状态</h3>
          <div class="status-row">
            <span class="label">状态</span>
            <span class="badge badge-active">在线</span>
          </div>
          <div class="status-row">
            <span class="label">上次登录</span>
            <span class="value">{{ user.lastLoginAt ? new Date(user.lastLoginAt).toLocaleString('zh-CN') : '首次登录' }}</span>
          </div>
        </div>

        <!-- 编辑信息卡片 -->
        <div class="card edit-card">
          <h3 class="card-title">编辑资料</h3>

          <div class="form-group">
            <label>用户名</label>
            <input type="text" :value="user.username" disabled class="input-disabled" />
            <p class="form-hint">用户名不可修改</p>
          </div>

          <div class="form-group">
            <label>邮箱</label>
            <input type="email" :value="user.email" disabled class="input-disabled" />
            <p class="form-hint">邮箱不可修改</p>
          </div>

          <div class="form-group">
            <label for="displayName">显示名称</label>
            <input
              id="displayName"
              v-model="form.displayName"
              type="text"
              placeholder="请输入显示名称"
              maxlength="100"
            />
          </div>

          <div v-if="error" class="msg msg-error">{{ error }}</div>
          <div v-if="success" class="msg msg-success">{{ success }}</div>

          <button
            class="btn btn-primary"
            :disabled="saving"
            @click="handleSubmit"
          >
            {{ saving ? '保存中...' : '保存修改' }}
          </button>
        </div>

        <!-- 退出登录 -->
        <div class="card logout-card">
          <button class="btn btn-danger" @click="handleLogout">
            退出登录
          </button>
        </div>
      </template>
    </div>
  </div>
</template>

<style scoped>
.profile-page {
  min-height: 100vh;
  background: var(--gray-50);
  padding: calc(72px + var(--space-8)) var(--space-8) var(--space-8);
}

.profile-container {
  max-width: 600px;
  margin: 0 auto;
}

.page-title {
  font-size: 24px;
  font-weight: 700;
  color: var(--gray-900);
  margin-bottom: var(--space-6);
}

.loading-state {
  text-align: center;
  padding: var(--space-16);
  color: var(--gray-500);
}

.spinner {
  width: 32px;
  height: 32px;
  border: 3px solid var(--gray-200);
  border-top-color: var(--primary-500);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  margin: 0 auto var(--space-4);
}

@keyframes spin { to { transform: rotate(360deg) } }

.card {
  background: white;
  border-radius: var(--radius-xl);
  box-shadow: var(--shadow-sm);
  padding: var(--space-6);
  margin-bottom: var(--space-4);
}

.card-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--gray-900);
  margin: 0 0 var(--space-4);
}

/* Avatar */
.avatar-section {
  display: flex;
  align-items: center;
  gap: var(--space-5);
}

.avatar {
  width: 64px;
  height: 64px;
  border-radius: 50%;
  background: var(--primary-100);
  color: var(--primary-700);
  font-size: 24px;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.display-name {
  font-size: 20px;
  font-weight: 700;
  color: var(--gray-900);
  margin: 0;
}

.username {
  font-size: 14px;
  color: var(--gray-500);
  margin: var(--space-1) 0 0;
}

/* Status */
.status-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--space-3) 0;
  border-bottom: 1px solid var(--gray-100);
}

.status-row:last-child {
  border-bottom: none;
}

.status-row .label {
  font-size: 14px;
  color: var(--gray-500);
}

.status-row .value {
  font-size: 14px;
  color: var(--gray-700);
}

.badge {
  padding: 2px 10px;
  border-radius: var(--radius-full);
  font-size: 12px;
  font-weight: 600;
}

.badge-active {
  background: var(--success-50);
  color: var(--success-700);
}

/* Form */
.form-group {
  margin-bottom: var(--space-5);
}

.form-group label {
  display: block;
  font-size: 14px;
  font-weight: 600;
  color: var(--gray-700);
  margin-bottom: var(--space-2);
}

.form-group input {
  width: 100%;
  padding: var(--space-3) var(--space-4);
  border: 1px solid var(--gray-300);
  border-radius: var(--radius-lg);
  font-size: 15px;
  color: var(--gray-900);
  background: white;
  outline: none;
  transition: border-color 0.2s;
  box-sizing: border-box;
}

.form-group input:focus {
  border-color: var(--primary-500);
  box-shadow: 0 0 0 3px var(--primary-100);
}

.input-disabled {
  background: var(--gray-50) !important;
  color: var(--gray-500) !important;
  cursor: not-allowed;
}

.form-hint {
  font-size: 12px;
  color: var(--gray-400);
  margin: var(--space-1) 0 0;
}

/* Messages */
.msg {
  padding: var(--space-3) var(--space-4);
  border-radius: var(--radius-lg);
  font-size: 14px;
  margin-bottom: var(--space-4);
}

.msg-error {
  background: var(--error-50);
  color: var(--error-700);
}

.msg-success {
  background: var(--success-50);
  color: var(--success-700);
}

/* Buttons */
.btn {
  padding: var(--space-3) var(--space-6);
  border: none;
  border-radius: var(--radius-lg);
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s, opacity 0.2s;
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-primary {
  background: var(--primary-600);
  color: white;
  width: 100%;
}

.btn-primary:hover:not(:disabled) {
  background: var(--primary-700);
}

.btn-danger {
  background: var(--error-50);
  color: var(--error-700);
  width: 100%;
}

.btn-danger:hover {
  background: var(--error-100);
}

.logout-card {
  text-align: center;
}
</style>
