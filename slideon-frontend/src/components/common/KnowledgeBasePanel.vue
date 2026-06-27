<template>
  <Teleport to="body">
    <div v-if="visible" class="kb-overlay" @click.self="close">
      <div class="kb-panel">
        <div class="kb-header">
          <h2>知识库管理</h2>
          <button class="modal-close-btn" @click="close">
            <IconBase name="times" :size="20" />
          </button>
        </div>

        <!-- Upload Area -->
        <div class="kb-section">
          <h3>导入文档</h3>
          <div
            class="upload-zone"
            :class="{ 'drag-over': isDragOver }"
            @click="triggerUpload"
            @dragover.prevent="isDragOver = true"
            @dragleave.prevent="isDragOver = false"
            @drop.prevent="handleDrop"
          >
            <input ref="uploadInput" type="file" accept=".pdf,.docx,.txt,.md" multiple style="display:none" @change="handleFiles" />
            <IconBase name="upload" :size="28" />
            <p>拖拽文件到此处或点击上传</p>
            <span class="hint">支持 PDF、Word、TXT、Markdown，可批量上传</span>
          </div>

          <!-- Selected files -->
          <div v-if="pendingFiles.length > 0 && !uploading" class="pending-files">
            <div v-for="(f, i) in pendingFiles" :key="i" class="pending-file">
              <IconBase name="file" :size="14" />
              <span>{{ f.name }}</span>
              <span class="file-size">{{ formatSize(f.size) }}</span>
              <button class="mini-btn" @click="pendingFiles.splice(i,1)">✕</button>
            </div>
            <button class="btn btn-primary btn-sm" @click="startUpload">
              开始导入 ({{ pendingFiles.length }} 个文件)
            </button>
          </div>

          <!-- Progress -->
          <div v-if="uploading" class="upload-progress">
            <div class="progress-bar">
              <div class="progress-fill" :style="{ width: progressPercent + '%' }"></div>
            </div>
            <span class="progress-text">{{ progressText }}</span>
          </div>
        </div>

        <!-- Stats -->
        <div class="kb-section">
          <h3>知识库统计</h3>
          <div class="kb-stats">
            <span>共 <strong>{{ stats.num_entities || 0 }}</strong> 条知识条目</span>
          </div>
        </div>

        <div class="kb-footer">
          <button class="btn btn-secondary" @click="close">关闭</button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { ref, watch } from 'vue'
import IconBase from '../icons/IconBase.vue'
import { apiService } from '../../services/api.js'

const props = defineProps({
  visible: { type: Boolean, default: false }
})
const emit = defineEmits(['update:visible'])

const isDragOver = ref(false)
const pendingFiles = ref([])
const uploading = ref(false)
const progressPercent = ref(0)
const progressText = ref('')
const stats = ref({})
const uploadInput = ref(null)
let pollTimer = null

watch(() => props.visible, (val) => { if (val) loadStats() })

function close() { emit('update:visible', false) }

function triggerUpload() { uploadInput.value?.click() }
function handleFiles(e) {
  const files = Array.from(e.target.files || [])
  pendingFiles.value.push(...files)
}
function handleDrop(e) {
  isDragOver.value = false
  const files = Array.from(e.dataTransfer?.files || [])
  pendingFiles.value.push(...files)
}

async function startUpload() {
  if (pendingFiles.value.length === 0) return
  uploading.value = true
  progressText.value = '正在上传...'
  try {
    const result = await apiService.uploadDocumentsToKB(pendingFiles.value)
    const taskId = result.task_id
    pendingFiles.value = []
    pollTimer = setInterval(async () => {
      try {
        const task = await apiService.getImportTaskStatus(taskId)
        if (task.total > 0) {
          progressPercent.value = Math.round((task.processed / task.total) * 100)
        }
        progressText.value = `处理中 ${task.processed}/${task.total}`
        if (task.status === 'completed' || task.status === 'failed') {
          clearInterval(pollTimer)
          uploading.value = false
          progressText.value = task.status === 'completed' ? '导入完成' : '导入失败'
          if (task.errors && task.errors.length > 0) {
            progressText.value += ` (${task.errors.length} 个错误)`
          }
          loadStats()
        }
      } catch { clearInterval(pollTimer); uploading.value = false }
    }, 1000)
  } catch (e) {
    uploading.value = false
    progressText.value = '上传失败: ' + e.message
  }
}

async function loadStats() {
  try {
    stats.value = await apiService.getKBStats()
  } catch {}
}

function formatSize(bytes) {
  if (!bytes) return '0 B'
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1048576) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / 1048576).toFixed(1) + ' MB'
}
</script>

<style scoped>
.kb-overlay { position:fixed; inset:0; background:rgba(0,0,0,0.5); backdrop-filter:blur(4px); display:flex; align-items:center; justify-content:center; z-index:2000; }
.kb-panel { background:white; border-radius:16px; width:640px; max-height:80vh; display:flex; flex-direction:column; overflow:hidden; box-shadow:0 20px 60px rgba(0,0,0,0.15); }
.kb-header { display:flex; align-items:center; justify-content:space-between; padding:20px 24px; border-bottom:1px solid #e5e7eb; }
.kb-header h2 { font-size:18px; font-weight:600; color:#1f2937; margin:0; }
.modal-close-btn { width:36px; height:36px; display:flex; align-items:center; justify-content:center; border:none; background:transparent; border-radius:8px; color:#6b7280; cursor:pointer; }
.modal-close-btn:hover { background:#f3f4f6; color:#1f2937; }
.kb-section { padding:20px 24px; border-bottom:1px solid #f3f4f6; }
.kb-section h3 { font-size:14px; font-weight:600; color:#374151; margin:0 0 12px; }
.upload-zone { border:2px dashed #d1d5db; border-radius:12px; padding:32px; text-align:center; cursor:pointer; transition:all .2s; background:#f9fafb; color:#6b7280; }
.upload-zone:hover, .upload-zone.drag-over { border-color:#6366f1; background:#eef2ff; color:#4f46e5; }
.upload-zone p { font-size:14px; margin:8px 0 4px; }
.hint { font-size:12px; color:#9ca3af; }
.pending-files { margin-top:12px; }
.pending-file { display:flex; align-items:center; gap:8px; padding:8px 12px; background:#f9fafb; border-radius:8px; margin-bottom:6px; font-size:13px; }
.file-size { color:#9ca3af; font-size:12px; margin-left:auto; }
.upload-progress { margin-top:12px; }
.progress-bar { height:6px; background:#e5e7eb; border-radius:3px; overflow:hidden; }
.progress-fill { height:100%; background:linear-gradient(90deg,#6366f1,#8b5cf6); border-radius:3px; transition:width .3s; }
.progress-text { font-size:12px; color:#6b7280; display:block; margin-top:6px; }
.kb-stats { font-size:14px; color:#374151; text-align:center; padding:12px; background:#f9fafb; border-radius:8px; }
.kb-footer { display:flex; align-items:center; justify-content:flex-end; padding:16px 24px; background:#f9fafb; font-size:13px; color:#6b7280; }
</style>
