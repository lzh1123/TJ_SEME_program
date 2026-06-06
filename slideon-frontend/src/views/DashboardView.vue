<template>
  <div class="dashboard-page">
    <AppHeader @create-outline="showModal = true" />

    <div class="container">
      <div class="page-header">
        <div>
          <h1>我的大纲</h1>
          <p class="page-subtitle">管理您的大纲项目，点击即可编辑</p>
        </div>
        <button class="btn btn-primary" @click="showModal = true">
          <IconBase name="plus" :size="14" />
          新建大纲
        </button>
      </div>

      <!-- 大纲列表 -->
      <div v-if="outlines.length > 0" class="outlines-grid">
        <div
          v-for="outline in outlines"
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
                {{ formatTime(outline.updatedAt) }}
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

      <!-- 空状态 -->
      <div v-else class="empty-state">
        <div class="empty-icon">
          <IconBase name="file" :size="64" />
        </div>
        <h2>还没有大纲</h2>
        <p>点击上方按钮创建您的第一个大纲，AI将为您生成专业的PPT大纲结构</p>
        <button class="btn btn-primary btn-lg" @click="showModal = true">
          <IconBase name="magic" :size="18" />
          开始创建
        </button>
      </div>
    </div>

    <!-- 大纲生成对话框 -->
    <OutlineModal v-model="showModal" />

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
import OutlineModal from '../components/common/OutlineModal.vue'
import IconBase from '../components/icons/IconBase.vue'
import { useOutlineStore } from '../stores/outlineStore.js'

const router = useRouter()
const outlineStore = useOutlineStore()
const showModal = ref(false)
const deleteTarget = ref(null)

const outlines = computed(() => outlineStore.outlines)

onMounted(() => {
  outlineStore.loadOutlines()
})

function openOutline(outline) {
  router.push({ path: '/outline-editor', query: { id: outline.id } })
}

function confirmDelete(outline) {
  deleteTarget.value = outline
}

function doDelete() {
  if (deleteTarget.value) {
    outlineStore.deleteOutline(deleteTarget.value.id)
    deleteTarget.value = null
  }
}

function formatTime(isoString) {
  if (!isoString) return ''
  const date = new Date(isoString)
  const now = new Date()
  const diff = now - date
  const mins = Math.floor(diff / 60000)
  const hours = Math.floor(diff / 3600000)
  const days = Math.floor(diff / 86400000)

  if (mins < 1) return '刚刚'
  if (mins < 60) return `${mins}分钟前`
  if (hours < 24) return `${hours}小时前`
  if (days < 7) return `${days}天前`
  return date.toLocaleDateString('zh-CN')
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
