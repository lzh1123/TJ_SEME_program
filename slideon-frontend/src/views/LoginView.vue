<script setup>
import { ref, reactive } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '../stores/authStore.js'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

const form = reactive({
  username: '',
  password: ''
})
const error = ref('')
const submitting = ref(false)

async function handleSubmit() {
  error.value = ''
  if (!form.username || !form.password) {
    error.value = '请填写用户名和密码'
    return
  }
  submitting.value = true
  try {
    await authStore.login(form.username, form.password)
    // 登录成功，跳转到之前页面或首页
    const redirect = route.query.redirect || '/'
    router.push(redirect)
  } catch (e) {
    error.value = e.message || '登录失败，请检查用户名和密码'
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <div class="auth-page">
    <div class="auth-card">
      <div class="auth-header">
        <h1 class="auth-title">登录</h1>
        <p class="auth-subtitle">欢迎回到 Slideon</p>
      </div>

      <form @submit.prevent="handleSubmit" class="auth-form">
        <div class="form-group">
          <label for="username">用户名 / 邮箱</label>
          <input
            id="username"
            v-model="form.username"
            type="text"
            placeholder="请输入用户名或邮箱"
            autocomplete="username"
            :disabled="submitting"
          />
        </div>

        <div class="form-group">
          <label for="password">密码</label>
          <input
            id="password"
            v-model="form.password"
            type="password"
            placeholder="请输入密码"
            autocomplete="current-password"
            :disabled="submitting"
          />
        </div>

        <div v-if="error" class="form-error">{{ error }}</div>

        <button type="submit" class="btn btn-primary btn-block" :disabled="submitting">
          {{ submitting ? '登录中...' : '登录' }}
        </button>
      </form>

      <div class="auth-footer">
        <span>还没有账号？</span>
        <router-link to="/register" class="auth-link">立即注册</router-link>
      </div>
    </div>
  </div>
</template>

<style scoped>
.auth-page {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  background: linear-gradient(135deg, var(--primary-50) 0%, var(--info-50) 100%);
  padding: var(--space-4);
}

.auth-card {
  background: white;
  border-radius: var(--radius-2xl);
  box-shadow: var(--shadow-xl);
  padding: var(--space-10);
  width: 100%;
  max-width: 420px;
}

.auth-header {
  text-align: center;
  margin-bottom: var(--space-8);
}

.auth-title {
  font-size: 28px;
  font-weight: 700;
  color: var(--gray-900);
  margin: 0 0 var(--space-2);
}

.auth-subtitle {
  font-size: 15px;
  color: var(--gray-500);
  margin: 0;
}

.auth-form {
  display: flex;
  flex-direction: column;
  gap: var(--space-5);
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

.form-group label {
  font-size: 14px;
  font-weight: 600;
  color: var(--gray-700);
}

.form-group input {
  padding: var(--space-3) var(--space-4);
  border: 1px solid var(--gray-300);
  border-radius: var(--radius-lg);
  font-size: 15px;
  color: var(--gray-900);
  background: white;
  transition: border-color 0.2s, box-shadow 0.2s;
  outline: none;
}

.form-group input:focus {
  border-color: var(--primary-500);
  box-shadow: 0 0 0 3px var(--primary-100);
}

.form-group input:disabled {
  background: var(--gray-50);
  cursor: not-allowed;
}

.form-error {
  padding: var(--space-3) var(--space-4);
  background: var(--error-50);
  color: var(--error-700);
  border-radius: var(--radius-lg);
  font-size: 14px;
  text-align: center;
}

.btn-block {
  width: 100%;
  padding: var(--space-3);
  font-size: 16px;
  font-weight: 600;
  border: none;
  border-radius: var(--radius-lg);
  cursor: pointer;
  transition: background 0.2s, opacity 0.2s;
}

.btn-primary {
  background: var(--primary-600);
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background: var(--primary-700);
}

.btn-primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.auth-footer {
  text-align: center;
  margin-top: var(--space-6);
  font-size: 14px;
  color: var(--gray-500);
}

.auth-link {
  color: var(--primary-600);
  font-weight: 600;
  text-decoration: none;
  margin-left: var(--space-1);
}

.auth-link:hover {
  color: var(--primary-700);
  text-decoration: underline;
}
</style>
