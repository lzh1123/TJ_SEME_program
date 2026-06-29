<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/authStore.js'

const router = useRouter()
const authStore = useAuthStore()

const form = reactive({
  username: '',
  email: '',
  password: '',
  confirmPassword: '',
  displayName: ''
})
const error = ref('')
const submitting = ref(false)
const success = ref(false)

function validate() {
  if (!form.username || form.username.length < 3) {
    return '用户名至少需要3个字符'
  }
  if (!/^[a-zA-Z0-9_]+$/.test(form.username)) {
    return '用户名只能包含字母、数字和下划线'
  }
  if (!form.email) {
    return '请填写邮箱'
  }
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email)) {
    return '邮箱格式不正确'
  }
  if (!form.password || form.password.length < 6) {
    return '密码至少需要6个字符'
  }
  if (form.password !== form.confirmPassword) {
    return '两次密码输入不一致'
  }
  return null
}

async function handleSubmit() {
  error.value = ''
  const validationError = validate()
  if (validationError) {
    error.value = validationError
    return
  }

  submitting.value = true
  try {
    await authStore.register(
      form.username,
      form.email,
      form.password,
      form.displayName || null
    )
    success.value = true
    // 注册成功后跳转到登录页
    setTimeout(() => {
      router.push('/login')
    }, 1500)
  } catch (e) {
    error.value = e.message || '注册失败，请稍后重试'
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <div class="auth-page">
    <div class="auth-card">
      <div class="auth-header">
        <h1 class="auth-title">注册</h1>
        <p class="auth-subtitle">创建您的 Slideon 账号</p>
      </div>

      <div v-if="success" class="success-message">
        <div class="success-icon">✓</div>
        <p>注册成功！正在跳转到登录页...</p>
      </div>

      <form v-else @submit.prevent="handleSubmit" class="auth-form">
        <div class="form-group">
          <label for="username">用户名 <span class="required">*</span></label>
          <input
            id="username"
            v-model="form.username"
            type="text"
            placeholder="字母、数字和下划线"
            autocomplete="username"
            :disabled="submitting"
          />
        </div>

        <div class="form-group">
          <label for="email">邮箱 <span class="required">*</span></label>
          <input
            id="email"
            v-model="form.email"
            type="email"
            placeholder="请输入邮箱地址"
            autocomplete="email"
            :disabled="submitting"
          />
        </div>

        <div class="form-group">
          <label for="displayName">显示名称</label>
          <input
            id="displayName"
            v-model="form.displayName"
            type="text"
            placeholder="选填，默认使用用户名"
            :disabled="submitting"
          />
        </div>

        <div class="form-row">
          <div class="form-group">
            <label for="password">密码 <span class="required">*</span></label>
            <input
              id="password"
              v-model="form.password"
              type="password"
              placeholder="至少6个字符"
              autocomplete="new-password"
              :disabled="submitting"
            />
          </div>

          <div class="form-group">
            <label for="confirmPassword">确认密码 <span class="required">*</span></label>
            <input
              id="confirmPassword"
              v-model="form.confirmPassword"
              type="password"
              placeholder="再次输入密码"
              autocomplete="new-password"
              :disabled="submitting"
            />
          </div>
        </div>

        <div v-if="error" class="form-error">{{ error }}</div>

        <button type="submit" class="btn btn-primary btn-block" :disabled="submitting">
          {{ submitting ? '注册中...' : '创建账号' }}
        </button>
      </form>

      <div class="auth-footer">
        <span>已有账号？</span>
        <router-link to="/login" class="auth-link">立即登录</router-link>
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
  max-width: 480px;
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
  flex: 1;
}

.form-group label {
  font-size: 14px;
  font-weight: 600;
  color: var(--gray-700);
}

.required {
  color: var(--error-500);
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

.form-row {
  display: flex;
  gap: var(--space-4);
}

@media (max-width: 480px) {
  .form-row {
    flex-direction: column;
    gap: var(--space-5);
  }
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

.success-message {
  text-align: center;
  padding: var(--space-8) 0;
}

.success-icon {
  width: 60px;
  height: 60px;
  border-radius: 50%;
  background: var(--success-100);
  color: var(--success-500);
  font-size: 30px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto var(--space-4);
}
</style>
