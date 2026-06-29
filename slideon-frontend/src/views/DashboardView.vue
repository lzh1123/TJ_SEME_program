<template>
  <div class="dashboard-page">
    <AppHeader @create-outline="showModal()" />

    <div class="container">
      <div class="page-header">
        <div>
          <h1>我的大纲</h1>
          <p class="page-subtitle">管理您的大纲项目，点击即可编辑</p>
        </div>
        <div class="header-actions">
          <div class="search-box">
            <IconBase name="search" :size="14" class="search-icon" />
            <input
              type="text"
              class="search-input"
              placeholder="搜索大纲..."
              v-model="searchQuery"
            />
            <button v-if="searchQuery" class="search-clear" @click="searchQuery = ''">
              <IconBase name="times" :size="12" />
            </button>
          </div>
          <select class="time-filter" v-model="timeFilter">
            <option value="all">全部时间</option>
            <option value="today">今天</option>
            <option value="7days">最近7天</option>
            <option value="30days">最近30天</option>
            <option value="older">更早</option>
          </select>
          <button class="btn btn-primary" @click="showModal()">
            <IconBase name="plus" :size="14" />
            新建大纲
          </button>
        </div>
      </div>

      <!-- 大纲列表 -->
      <div v-if="filteredOutlines.length > 0" class="outlines-grid">
        <div
          v-for="outline in filteredOutlines"
          :key="outline.id"
          class="outline-card"
          @click="openOutline(outline)"
        >
          <div class="card-preview">
            <IconBase name="file" :size="32" />
            <span class="preview-slide-count">{{ outline.slideCount }}页</span>
          </div>
          <div class="card-body">
            <h3 class="card-title">{{ outline.title }}</h3>
            <div class="card-meta">
              <span class="card-time">
                <IconBase name="clock" :size="12" />
                创建 {{ formatFullTime(outline.createdAt) }}
              </span>
            </div>
          </div>
          <div class="card-actions">
            <button class="mini-btn" @click.stop="openOutline(outline)" title="编辑">
              <IconBase name="edit" :size="14" />
            </button>
            <button class="mini-btn danger" @click.stop="confirmDelete(outline)" title="删除">
              <IconBase name="trash" :size="14" />
            </button>
          </div>
        </div>
      </div>

      <!-- 搜索无结果 -->
      <div v-else-if="outlines.length > 0 && filteredOutlines.length === 0" class="empty-state">
        <div class="empty-icon">
          <IconBase name="search" :size="64" />
        </div>
        <h2>未找到匹配的大纲</h2>
        <p>没有标题包含「{{ searchQuery }}」的大纲，试试其他关键词</p>
        <button class="btn btn-secondary" @click="searchQuery = ''">清除搜索</button>
      </div>

      <!-- 完全空状态 -->
      <div v-else-if="outlines.length === 0" class="empty-state">
        <div class="empty-icon">
          <IconBase name="file" :size="64" />
        </div>
        <h2>还没有大纲</h2>
        <p>点击上方按钮创建您的第一个大纲，AI将为您生成专业的PPT大纲结构</p>
        <button class="btn btn-primary btn-lg" @click="showModal()">
          <IconBase name="magic" :size="18" />
          开始创建
        </button>
      </div>
    </div>

    <!-- 删除确认 -->
    <Teleport to="body">
      <div v-if="deleteTarget" class="confirm-overlay" @click.self="deleteTarget = null">
        <div class="confirm-dialog">
          <h3>确认删除</h3>
          <p>确定要删除「{{ deleteTarget.title }}」吗？此操作不可恢复。</p>
          <div class="confirm-actions">
            <button class="btn btn-secondary" @click="deleteTarget = null">取消</button>
            <button class="btn btn-danger" @click="doDelete">删除</button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import AppHeader from '../components/common/AppHeader.vue'
import IconBase from '../components/icons/IconBase.vue'
import { useOutlineStore } from '../stores/outlineStore.js'
import { useFloatingBall } from '../composables/useFloatingBall.js'

const router = useRouter()
const outlineStore = useOutlineStore()
const { showModal } = useFloatingBall()
const deleteTarget = ref(null)
const searchQuery = ref('')
const timeFilter = ref('all')

const outlines = computed(() => outlineStore.outlines)

const filteredOutlines = computed(() => {
  let result = outlines.value
  const q = searchQuery.value.trim().toLowerCase()
  if (q) result = result.filter(o => o.title.toLowerCase().includes(q))

  const now = new Date()
  const startOfDay = new Date(now.getFullYear(), now.getMonth(), now.getDate())
  const msPerDay = 86400000

  switch (timeFilter.value) {
    case 'today':
      result = result.filter(o => o.createdAt && new Date(o.createdAt) >= startOfDay)
      break
    case '7days':
      result = result.filter(o => o.createdAt && new Date(o.createdAt) >= new Date(now.getTime() - 7 * msPerDay))
      break
    case '30days':
      result = result.filter(o => o.createdAt && new Date(o.createdAt) >= new Date(now.getTime() - 30 * msPerDay))
      break
    case 'older':
      result = result.filter(o => o.createdAt && new Date(o.createdAt) < new Date(now.getTime() - 30 * msPerDay))
      break
  }

  return result
})

onMounted(() => {
  outlineStore.loadOutlines()
})

function openOutline(outline) {
  router.push({ path: '/outline-editor', query: { id: outline.id } })
}

function confirmDelete(outline) {
  deleteTarget.value = outline
}

async function doDelete() {
  if (deleteTarget.value) {
    try {
      await outlineStore.deleteOutline(deleteTarget.value.id)
      deleteTarget.value = null
    } catch (error) {
      alert('删除失败: ' + error.message)
    }
  }
}

function formatFullTime(isoString) {
  if (!isoString) return ''
  const d = new Date(isoString)
  const y = d.getFullYear()
  const mo = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  const h = String(d.getHours()).padStart(2, '0')
  const mi = String(d.getMinutes()).padStart(2, '0')
  const s = String(d.getSeconds()).padStart(2, '0')
  return `${y}-${mo}-${day} ${h}:${mi}:${s}`
}
</script>

<style scoped>
.dashboard-page {
  padding-top: 64px;
  min-height: 100vh;
  background: var(--gray-50);
}

.container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 40px var(--space-8);
}

.page-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  margin-bottom: var(--space-8);
  flex-wrap: wrap;
  gap: var(--space-4);
}

.page-header h1 {
  font-size: 28px;
  font-weight: 700;
  color: var(--gray-800);
  margin: 0 0 var(--space-1);
}

.page-subtitle {
  font-size: 14px;
  color: var(--gray-500);
  margin: 0;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: var(--space-3);
}

.search-box {
  position: relative;
  width: 240px;
}

.search-icon {
  position: absolute;
  left: 12px;
  top: 50%;
  transform: translateY(-50%);
  color: var(--gray-400);
  pointer-events: none;
}

.search-input {
  width: 100%;
  height: 40px;
  padding: 0 36px 0 36px;
  font-size: 13px;
  border: 1px solid var(--gray-200);
  border-radius: var(--radius-lg);
  background: white;
  transition: all 0.2s ease;
  outline: none;
}

.search-input:focus {
  border-color: var(--primary-300);
  box-shadow: 0 0 0 3px var(--primary-100);
}

.search-clear {
  position: absolute;
  right: 8px;
  top: 50%;
  transform: translateY(-50%);
  width: 20px;
  height: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
  background: var(--gray-200);
  color: var(--gray-500);
  border-radius: 50%;
  cursor: pointer;
  font-size: 10px;
}

.search-clear:hover {
  background: var(--gray-300);
  color: var(--gray-700);
}

.time-filter {
  height: 40px;
  padding: 0 32px 0 12px;
  font-size: 13px;
  color: var(--gray-700);
  background: white;
  border: 1px solid var(--gray-200);
  border-radius: var(--radius-lg);
  cursor: pointer;
  outline: none;
  appearance: none;
  background-image: url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 20 20'%3e%3cpath stroke='%236b7280' stroke-linecap='round' stroke-linejoin='round' stroke-width='1.5' d='M6 8l4 4 4-4'/%3e%3c/svg%3e");
  background-position: right 8px center;
  background-repeat: no-repeat;
  background-size: 18px;
  transition: border-color 0.2s ease;
}

.time-filter:hover {
  border-color: var(--gray-300);
}

.time-filter:focus {
  border-color: var(--primary-300);
  box-shadow: 0 0 0 3px var(--primary-100);
}

/* 大纲卡片网格 */
.outlines-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: var(--space-6);
}

.outline-card {
  background: white;
  border-radius: var(--radius-xl);
  border: 1px solid var(--gray-200);
  overflow: hidden;
  cursor: pointer;
  transition: all 0.2s ease;
  position: relative;
}

.outline-card:hover {
  transform: translateY(-4px);
  box-shadow: var(--shadow-lg);
  border-color: var(--primary-300);
}

.card-preview {
  height: 120px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: var(--space-2);
  color: white;
}

.preview-slide-count {
  font-size: 12px;
  background: rgba(255,255,255,0.2);
  padding: 2px 10px;
  border-radius: var(--radius-full);
  font-weight: 500;
}

.card-body {
  padding: var(--space-4);
}

.card-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--gray-800);
  margin: 0 0 var(--space-2);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.card-meta {
  display: flex;
  align-items: center;
  gap: var(--space-1);
}

.card-time {
  font-size: 12px;
  color: var(--gray-500);
  display: flex;
  align-items: center;
  gap: 4px;
}

.card-actions {
  position: absolute;
  top: var(--space-2);
  right: var(--space-2);
  display: flex;
  gap: 4px;
  opacity: 0;
  transition: opacity 0.2s ease;
}

.outline-card:hover .card-actions {
  opacity: 1;
}

.card-actions .mini-btn {
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
  background: rgba(255,255,255,0.9);
  color: var(--gray-600);
  border-radius: var(--radius-sm);
  cursor: pointer;
  backdrop-filter: blur(4px);
}

.card-actions .mini-btn:hover {
  background: white;
  color: var(--gray-800);
}

.card-actions .mini-btn.danger:hover {
  background: var(--error-50);
  color: var(--error-600);
}

/* 空状态 */
.empty-state {
  text-align: center;
  padding: 80px 20px;
  background: white;
  border-radius: var(--radius-2xl);
  border: 1px solid var(--gray-200);
}

.empty-icon {
  color: var(--gray-300);
  margin-bottom: var(--space-4);
}

.empty-state h2 {
  font-size: 20px;
  font-weight: 600;
  color: var(--gray-800);
  margin: 0 0 var(--space-2);
}

.empty-state p {
  font-size: 14px;
  color: var(--gray-500);
  margin: 0 0 var(--space-6);
  max-width: 400px;
  margin-left: auto;
  margin-right: auto;
}

/* 删除确认 */
.confirm-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.5);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000;
}

.confirm-dialog {
  background: white;
  padding: var(--space-6);
  border-radius: var(--radius-xl);
  box-shadow: var(--shadow-2xl);
  max-width: 400px;
  width: 90%;
}

.confirm-dialog h3 {
  font-size: 18px;
  font-weight: 600;
  color: var(--gray-800);
  margin: 0 0 var(--space-2);
}

.confirm-dialog p {
  font-size: 14px;
  color: var(--gray-600);
  margin: 0 0 var(--space-6);
}

.confirm-actions {
  display: flex;
  justify-content: flex-end;
  gap: var(--space-3);
}

.btn-danger {
  background: var(--error-500);
  color: white;
  border: none;
}

.btn-danger:hover {
  background: var(--error-600);
}

/* 响应式 */
@media (max-width: 1200px) {
  .outlines-grid {
    grid-template-columns: repeat(3, 1fr);
  }
}

@media (max-width: 900px) {
  .outlines-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 600px) {
  .outlines-grid {
    grid-template-columns: 1fr;
  }

  .page-header {
    flex-direction: column;
    gap: var(--space-4);
  }
}
</style>
