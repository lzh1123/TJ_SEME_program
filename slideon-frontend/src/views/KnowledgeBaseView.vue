<template>
  <div class="kb-page">
    <AppHeader @create-outline="showModal()" />

    <div class="container">
      <div class="page-header">
        <div>
          <h1>知识库管理</h1>
          <p class="page-subtitle">管理已导入的知识文档，上传新文档以增强 AI 生成质量</p>
        </div>
        <div class="header-actions">
          <button class="btn btn-primary" @click="triggerUpload">
            <IconBase name="plus" :size="14" />
            导入文档
          </button>
          <input
            ref="uploadInput"
            type="file"
            accept=".pdf,.docx,.txt,.md"
            multiple
            style="display:none"
            @change="handleFiles"
          />
        </div>
      </div>

      <!-- Upload Progress -->
      <div v-if="uploading" class="upload-progress-card">
        <div class="progress-header">
          <IconBase name="spinner" :size="18" class="animate-spin" />
          <span>{{ progressText }}</span>
        </div>
        <div class="progress-bar">
          <div class="progress-fill" :style="{ width: progressPercent + '%' }"></div>
        </div>
        <p class="progress-detail">文件正在后台处理中，您可以继续其他操作</p>
      </div>

      <!-- Stats Overview (always visible once loaded or cached) -->
      <div class="stats-row">
        <div class="stat-card">
          <div class="stat-value">{{ loading && !hasCache ? '—' : (stats.num_entities || 0) }}</div>
          <div class="stat-label">知识条目</div>
        </div>
        <div class="stat-card">
          <div class="stat-value">{{ loading && !hasCache ? '—' : importedDocs.length }}</div>
          <div class="stat-label">已导入文档</div>
        </div>
        <div class="stat-card">
          <div class="stat-value">{{ importingCount || '—' }}</div>
          <div class="stat-label">处理中</div>
        </div>
      </div>

      <!-- Document List -->
      <section class="docs-section">
        <h2>已导入文档</h2>

        <!-- Loading skeleton -->
        <div v-if="loading && !hasCache" class="loading-skeleton">
          <div v-for="n in 3" :key="n" class="skeleton-row">
            <div class="skeleton-cell" style="width:40%"></div>
            <div class="skeleton-cell" style="width:15%"></div>
            <div class="skeleton-cell" style="width:20%"></div>
            <div class="skeleton-cell" style="width:10%"></div>
          </div>
        </div>

        <div v-else-if="importedDocs.length === 0 && !uploading" class="empty-state">
          <div class="empty-icon">
            <IconBase name="database" :size="64" />
          </div>
          <h2>知识库为空</h2>
          <p>上传 PDF、Word、TXT 或 Markdown 文档来构建您的知识库。AI 将基于这些资料生成更专业、更有深度的 PPT 内容。</p>
          <div
            class="upload-zone-empty"
            @click="triggerUpload"
            @dragover.prevent
            @drop.prevent="handleDrop"
          >
            <IconBase name="upload" :size="28" />
            <p>拖拽文件到此处或点击上传</p>
            <span class="upload-hint">支持 PDF、Word、TXT、Markdown，可批量上传</span>
          </div>
        </div>

        <div v-else class="docs-table-wrapper">
          <table class="docs-table">
            <thead>
              <tr>
                <th>文档名称</th>
                <th>条目数</th>
                <th>状态</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(doc, i) in importedDocs" :key="i">
                <td>
                  <div class="doc-name-cell">
                    <IconBase name="file" :size="16" />
                    <span>{{ doc.name }}</span>
                  </div>
                </td>
                <td>{{ doc.chunks || '—' }}</td>
                <td>
                  <span class="status-badge" :class="doc.status">{{ statusLabel(doc.status) }}</span>
                </td>
                <td>
                  <button class="mini-btn danger" @click="removeDoc(doc)" title="删除">
                    <IconBase name="trash" :size="14" />
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import AppHeader from '../components/common/AppHeader.vue'
import IconBase from '../components/icons/IconBase.vue'
import { useFloatingBall } from '../composables/useFloatingBall.js'
import { apiService } from '../services/api.js'

const { showModal } = useFloatingBall()

const KB_CACHE_KEY = 'slideon_kb_cache'

const loading = ref(true)
const hasCache = ref(false)
const stats = ref({ num_entities: 0 })
const importedDocs = ref([])
const uploading = ref(false)
const importingCount = ref(0)
const progressPercent = ref(0)
const progressText = ref('')
const uploadInput = ref(null)
let pollTimer = null

// Restore cached data instantly to avoid flash
function restoreCache() {
  try {
    const raw = sessionStorage.getItem(KB_CACHE_KEY)
    if (raw) {
      const cached = JSON.parse(raw)
      if (cached.stats) stats.value = cached.stats
      if (cached.importedDocs) importedDocs.value = cached.importedDocs
      hasCache.value = true
    }
  } catch {}
}

function saveCache() {
  try {
    sessionStorage.setItem(KB_CACHE_KEY, JSON.stringify({
      stats: stats.value,
      importedDocs: importedDocs.value,
      ts: Date.now(),
    }))
  } catch {}
}

onMounted(() => {
  restoreCache()
  loadData()
})

watch(importingCount, (val) => {
  if (val === 0 && pollTimer) {
    clearInterval(pollTimer)
    pollTimer = null
  }
})

function triggerUpload() { uploadInput.value?.click() }

function handleFiles(e) {
  const files = Array.from(e.target.files || [])
  if (files.length > 0) startUpload(files)
  // Reset input so same file can be re-selected
  if (uploadInput.value) uploadInput.value.value = ''
}

function handleDrop(e) {
  const files = Array.from(e.dataTransfer?.files || [])
  if (files.length > 0) startUpload(files)
}

async function startUpload(files) {
  uploading.value = true
  importingCount.value = files.length
  progressText.value = '正在上传...'
  progressPercent.value = 0

  // Add placeholder docs
  const placeholders = files.map(f => ({
    name: f.name,
    chunks: '—',
    status: 'importing'
  }))
  importedDocs.value = [...placeholders, ...importedDocs.value]

  try {
    const result = await apiService.uploadDocumentsToKB(files)
    const taskId = result.task_id

    pollTimer = setInterval(async () => {
      try {
        const task = await apiService.getImportTaskStatus(taskId)
        if (task.total > 0) {
          progressPercent.value = Math.round((task.processed / task.total) * 100)
        }
        progressText.value = `处理中 ${task.processed}/${task.total}`

        if (task.status === 'completed' || task.status === 'failed') {
          clearInterval(pollTimer)
          pollTimer = null
          uploading.value = false
          importingCount.value = 0

          if (task.errors && task.errors.length > 0) {
            progressText.value = `导入完成（${task.errors.length} 个错误）`
          } else {
            progressText.value = '导入完成'
          }

          // Remove placeholder entries and reload from server
          importedDocs.value = importedDocs.value.filter(d => d.status !== 'importing')
          loadData()
        }
      } catch {
        clearInterval(pollTimer)
        pollTimer = null
        uploading.value = false
        importingCount.value = 0
      }
    }, 1000)
  } catch (e) {
    uploading.value = false
    importingCount.value = 0
    progressText.value = '上传失败: ' + e.message
  }
}

async function loadData() {
  loading.value = true
  try {
    const data = await apiService.getKBDocuments()
    stats.value = { num_entities: data.num_entities || 0 }
    importingCount.value = 0

    if (data.documents && data.documents.length > 0) {
      importedDocs.value = data.documents.map(d => ({
        name: d.filename || d.source,
        source: d.source,
        chunks: d.chunks,
        status: 'ready'
      }))
    } else {
      importedDocs.value = []
    }

    progressPercent.value = 0
    progressText.value = ''
    uploading.value = false
    saveCache()
  } catch {
    // Keep cached data on error
  } finally {
    loading.value = false
  }
}

function removeDoc(doc) {
  if (confirm(`确定要删除「${doc.name}」吗？此操作不可恢复。`)) {
    apiService.removeKBDocument(doc.source).then(() => {
      importedDocs.value = importedDocs.value.filter(d => d.source !== doc.source)
      stats.value.num_entities = Math.max(0, (stats.value.num_entities || 0) - (doc.chunks || 0))
      saveCache()
      loadData()
    }).catch(() => {})
  }
}

function statusLabel(s) {
  return s === 'ready' ? '就绪' : s === 'importing' ? '导入中' : '错误'
}
</script>

<style scoped>
.kb-page {
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

/* Upload progress */
.upload-progress-card {
  padding: var(--space-4) var(--space-6);
  background: var(--primary-50);
  border: 1px solid var(--primary-200);
  border-radius: var(--radius-lg);
  margin-bottom: var(--space-6);
}

.progress-header {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  font-size: 14px;
  font-weight: 600;
  color: var(--primary-700);
  margin-bottom: var(--space-2);
}

.progress-bar {
  height: 6px;
  background: var(--primary-100);
  border-radius: 3px;
  overflow: hidden;
  margin-bottom: var(--space-2);
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #6366f1, #8b5cf6);
  border-radius: 3px;
  transition: width 0.3s ease;
}

.progress-detail {
  font-size: 12px;
  color: var(--primary-500);
  margin: 0;
}

.animate-spin { animation: spin 1s linear infinite; }
@keyframes spin { to { transform: rotate(360deg) } }

/* Stats */
.stats-row {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: var(--space-6);
  margin-bottom: var(--space-8);
}

.stat-card {
  background: white;
  border-radius: var(--radius-xl);
  padding: var(--space-6);
  text-align: center;
  border: 1px solid var(--gray-200);
}

.stat-value {
  font-size: 32px;
  font-weight: 700;
  color: var(--primary-600);
  margin-bottom: var(--space-1);
}

.stat-label {
  font-size: 13px;
  color: var(--gray-500);
  font-weight: 500;
}

/* Document list */
.docs-section {
  background: white;
  border-radius: var(--radius-xl);
  border: 1px solid var(--gray-200);
  padding: var(--space-6);
}

.docs-section h2 {
  font-size: 18px;
  font-weight: 600;
  color: var(--gray-800);
  margin: 0 0 var(--space-4);
}

.docs-table-wrapper {
  overflow-x: auto;
}

.docs-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 14px;
}

.docs-table th {
  text-align: left;
  padding: 12px 16px;
  background: var(--gray-50);
  color: var(--gray-600);
  font-weight: 600;
  border-bottom: 2px solid var(--gray-200);
}

.docs-table td {
  padding: 12px 16px;
  border-bottom: 1px solid var(--gray-100);
  color: var(--gray-700);
}

.doc-name-cell {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  font-weight: 500;
}

.status-badge {
  display: inline-block;
  padding: 2px 10px;
  border-radius: var(--radius-full);
  font-size: 12px;
  font-weight: 500;
}

.status-badge.ready {
  background: var(--success-100);
  color: var(--success-700);
}

.status-badge.importing {
  background: var(--primary-100);
  color: var(--primary-700);
}

/* Empty state */
.empty-state {
  text-align: center;
  padding: 60px 20px;
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
  margin: 0 auto var(--space-6);
  max-width: 500px;
  line-height: 1.6;
}

.upload-zone-empty {
  border: 2px dashed var(--gray-300);
  border-radius: var(--radius-xl);
  padding: var(--space-8);
  text-align: center;
  cursor: pointer;
  transition: all 0.2s ease;
  background: var(--gray-50);
  max-width: 500px;
  margin: 0 auto;
  color: var(--gray-600);
}

.upload-zone-empty:hover {
  border-color: var(--primary-400);
  background: var(--primary-50);
  color: var(--primary-600);
}

.upload-zone-empty p {
  font-size: 14px;
  margin: var(--space-2) 0 var(--space-1);
  color: inherit;
}

.upload-hint {
  font-size: 12px;
  color: var(--gray-400);
}

/* Loading skeleton */
.loading-skeleton {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.skeleton-row {
  display: flex;
  gap: 16px;
  padding: 14px 16px;
  background: var(--gray-50);
  border-radius: var(--radius-md);
}

.skeleton-cell {
  height: 16px;
  background: linear-gradient(90deg, #e5e7eb 25%, #f3f4f6 50%, #e5e7eb 75%);
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite;
  border-radius: 4px;
}

@keyframes shimmer {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}

/* Responsive */
@media (max-width: 768px) {
  .stats-row {
    grid-template-columns: 1fr;
  }
}
</style>
