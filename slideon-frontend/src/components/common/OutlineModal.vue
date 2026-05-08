<template>
  <Teleport to="body">
    <div class="modal" :class="{ active: modelValue }" @click.self="close">
      <div class="modal-overlay" @click="close"></div>
      <div class="modal-content" :class="{ expanded: currentStep === 2 }">
        <div class="modal-header">
          <h2 class="modal-title">{{ currentStep === 2 ? '编辑PPT大纲' : '智能生成PPT大纲' }}</h2>
          <button class="modal-close" @click="close">
            <IconBase name="times" :size="20" />
          </button>
        </div>
        
        <div class="modal-body">
          <!-- Step 1: 输入设置 -->
          <div v-if="currentStep === 1" class="step-content">
            <div class="form-step">
              <label class="form-label">
                <span class="step-number">1</span>
                输入主题
              </label>
              <textarea 
                class="input textarea" 
                placeholder="描述你的PPT主题、目标受众和主要内容...

例如：为科技公司CEO准备的产品发布会PPT，介绍新一代AI芯片的性能优势和市场前景"
                v-model="form.topic"
                @input="updateCharCount"
              ></textarea>
              <div class="char-count" :class="{ error: charCount > 500 }">{{ charCount }}/500</div>
            </div>

            <div class="form-group">
              <label class="form-label optional">
                <IconBase name="paperclip" :size="14" />
                上传参考文档（可选）
              </label>
              <div 
                class="upload-area"
                :class="{ dragover: isDragging }"
                @click="triggerFileInput"
                @dragover.prevent="isDragging = true"
                @dragleave.prevent="isDragging = false"
                @drop.prevent="handleDrop"
              >
                <div class="upload-content">
                  <IconBase name="cloudUpload" :size="40" class="upload-icon" />
                  <p class="upload-text">拖拽文件到此处，或点击上传</p>
                  <p class="upload-hint">支持 PDF, DOCX, TXT, MD（最大 20MB）</p>
                </div>
                <input 
                  ref="fileInput"
                  type="file" 
                  class="file-input" 
                  multiple 
                  accept=".pdf,.docx,.txt,.md"
                  @change="handleFileChange"
                >
              </div>
              
              <div v-if="uploadedFiles.length > 0" class="uploaded-files-list">
                <div v-for="file in uploadedFiles" :key="file.id" class="file-item">
                  <div class="file-icon" :class="file.type">
                    <IconBase :name="getFileIcon(file.type)" :size="18" />
                  </div>
                  <div class="file-info">
                    <div class="file-name">{{ file.name }}</div>
                    <div class="file-meta">
                      <span class="file-size">{{ formatFileSize(file.size) }}</span>
                      <span class="file-status" :class="file.status">
                        <IconBase v-if="file.status === 'uploading'" name="spinner" :size="12" class="animate-spin" />
                        <IconBase v-else-if="file.status === 'success'" name="check" :size="12" />
                        {{ getStatusText(file.status) }}
                      </span>
                    </div>
                    <div v-if="file.status === 'uploading'" class="upload-progress">
                      <div class="upload-progress-bar" :style="{ width: file.progress + '%' }"></div>
                    </div>
                  </div>
                  <button class="file-remove" @click.stop="removeFile(file.id)">
                    <IconBase name="times" :size="14" />
                  </button>
                </div>
              </div>
            </div>

            <div class="form-step">
              <label class="form-label">
                <span class="step-number">2</span>
                选择风格
              </label>
              <div class="style-options">
                <div 
                  v-for="style in styleOptions" 
                  :key="style.value"
                  :class="['style-card', { active: form.style === style.value }]"
                  @click="form.style = style.value"
                >
                  <div class="style-icon">{{ style.icon }}</div>
                  <span class="style-name">{{ style.name }}</span>
                  <div class="style-radio"></div>
                </div>
              </div>
            </div>

            <div class="form-step">
              <label class="form-label">
                <span class="step-number">3</span>
                设置页数
              </label>
              <div class="page-slider">
                <input 
                  type="range" 
                  min="8" 
                  max="20" 
                  v-model="form.pageCount" 
                  class="slider"
                >
                <div class="slider-info">
                  <span class="page-count">{{ form.pageCount }} 页</span>
                  <span class="page-hint">推荐 8-20 页</span>
                </div>
              </div>
            </div>
          </div>

          <!-- Step 2: 编辑大纲 -->
          <div v-if="currentStep === 2" class="step-content outline-editor">
            <div class="outline-header">
              <div class="outline-stats">
                <span class="stat-item">
                  <IconBase name="list" :size="14" />
                  {{ outlineItems.length }} 个章节
                </span>
                <span class="stat-item">
                  <IconBase name="file" :size="14" />
                  {{ totalPages }} 页
                </span>
              </div>
              <div class="outline-actions">
                <button class="btn btn-secondary btn-sm" @click="regenerateOutline">
                  <IconBase name="refresh" :size="14" />
                  重新生成
                </button>
              </div>
            </div>

            <div class="outline-tree-container">
              <div class="outline-tree">
                <div 
                  v-for="(item, index) in outlineItems" 
                  :key="item.id"
                  class="outline-item"
                  :class="{ expanded: item.expanded }"
                >
                  <div class="outline-item-header">
                    <button 
                      class="toggle-btn"
                      @click="toggleItem(item)"
                      :class="{ hidden: !item.children || item.children.length === 0 }"
                    >
                      <IconBase name="chevronRight" :size="12" />
                    </button>
                    <span class="item-number">{{ index + 1 }}</span>
                    <input 
                      v-if="item.editing"
                      v-model="item.title"
                      class="item-input"
                      @blur="item.editing = false"
                      @keyup.enter="item.editing = false"
                      ref="inputRef"
                    >
                    <span 
                      v-else
                      class="item-title"
                      @dblclick="startEdit(item)"
                    >
                      {{ item.title }}
                    </span>
                    <div class="item-actions">
                      <button class="action-btn" @click="addChildItem(item)" title="添加子章节">
                        <IconBase name="plus" :size="12" />
                      </button>
                      <button class="action-btn" @click="startEdit(item)" title="编辑">
                        <IconBase name="edit" :size="12" />
                      </button>
                      <button class="action-btn danger" @click="removeItem(item)" title="删除">
                        <IconBase name="trash" :size="12" />
                      </button>
                    </div>
                  </div>

                  <div v-if="item.expanded && item.children" class="outline-children">
                    <div 
                      v-for="child in item.children" 
                      :key="child.id"
                      class="outline-child-item"
                    >
                      <span class="child-number">{{ child.pageNumber }}</span>
                      <input 
                        v-if="child.editing"
                        v-model="child.title"
                        class="item-input"
                        @blur="child.editing = false"
                        @keyup.enter="child.editing = false"
                      >
                      <span 
                        v-else
                        class="child-title"
                        @dblclick="startEdit(child)"
                      >
                        {{ child.title }}
                      </span>
                      <div class="item-actions">
                        <button class="action-btn" @click="startEdit(child)" title="编辑">
                          <IconBase name="edit" :size="12" />
                        </button>
                        <button class="action-btn danger" @click="removeChildItem(item, child)" title="删除">
                          <IconBase name="trash" :size="12" />
                        </button>
                      </div>
                    </div>
                    <button class="add-child-btn" @click="addChildItem(item)">
                      <IconBase name="plus" :size="12" />
                      添加页面
                    </button>
                  </div>
                </div>
              </div>
              
              <button class="add-section-btn" @click="addSection">
                <IconBase name="plus" :size="14" />
                添加章节
              </button>
            </div>
          </div>
        </div>

        <div class="modal-footer">
          <template v-if="currentStep === 1">
            <button class="btn btn-secondary" @click="close">取消</button>
            <button 
              class="btn btn-primary" 
              :disabled="isGenerating || !form.topic.trim()"
              @click="generateOutline"
            >
              <IconBase v-if="isGenerating" name="spinner" :size="14" class="animate-spin" />
              <IconBase v-else name="magic" :size="14" />
              {{ isGenerating ? '生成中...' : '开始生成' }}
            </button>
          </template>
          <template v-else>
            <button class="btn btn-secondary" @click="prevStep">返回修改</button>
            <button class="btn btn-primary" @click="confirmOutline">
              <IconBase name="check" :size="14" />
              确认大纲并创建
            </button>
          </template>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { ref, computed, nextTick } from 'vue'
import IconBase from '../icons/IconBase.vue'

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['update:modelValue', 'generate'])

const fileInput = ref(null)
const inputRef = ref(null)
const isDragging = ref(false)
const isGenerating = ref(false)
const uploadedFiles = ref([])
const currentStep = ref(1)

const form = ref({
  topic: '',
  style: 'modern',
  pageCount: 12
})

const outlineItems = ref([])

const charCount = computed(() => form.value.topic.length)

const totalPages = computed(() => {
  let count = 0
  outlineItems.value.forEach(item => {
    if (item.children) {
      count += item.children.length
    }
  })
  return count
})

const styleOptions = [
  { value: 'business', name: '商务正式', icon: '💼' },
  { value: 'creative', name: '创意活泼', icon: '🎨' },
  { value: 'academic', name: '学术严谨', icon: '📖' },
  { value: 'modern', name: '简约现代', icon: '✨' }
]

const generateId = () => Date.now() + Math.random()

const close = () => {
  currentStep.value = 1
  outlineItems.value = []
  emit('update:modelValue', false)
}

const updateCharCount = () => {
  if (charCount.value > 500) {
    form.value.topic = form.value.topic.slice(0, 500)
  }
}

const triggerFileInput = () => {
  fileInput.value?.click()
}

const handleFileChange = (e) => {
  handleFiles(e.target.files)
}

const handleDrop = (e) => {
  isDragging.value = false
  handleFiles(e.dataTransfer.files)
}

const handleFiles = (files) => {
  const validTypes = ['.pdf', '.docx', '.txt', '.md']
  const maxSize = 20 * 1024 * 1024

  Array.from(files).forEach(file => {
    const extension = '.' + file.name.split('.').pop().toLowerCase()
    
    if (!validTypes.includes(extension)) {
      alert(`不支持的文件格式: ${file.name}`)
      return
    }
    
    if (file.size > maxSize) {
      alert(`文件过大: ${file.name} (最大20MB)`)
      return
    }
    
    if (uploadedFiles.value.some(f => f.name === file.name)) {
      alert(`文件已存在: ${file.name}`)
      return
    }
    
    const fileData = {
      id: generateId(),
      name: file.name,
      size: file.size,
      type: extension,
      status: 'uploading',
      progress: 0
    }
    
    uploadedFiles.value.push(fileData)
    simulateUpload(fileData)
  })
}

const simulateUpload = (fileData) => {
  const file = uploadedFiles.value.find(f => f.id === fileData.id)
  if (!file) return
  
  let progress = 0
  const interval = setInterval(() => {
    progress += Math.random() * 30
    if (progress >= 100) {
      progress = 100
      clearInterval(interval)
      file.status = 'success'
      file.progress = 100
    } else {
      file.progress = progress
    }
  }, 200)
}

const removeFile = (id) => {
  uploadedFiles.value = uploadedFiles.value.filter(f => f.id !== id)
}

const getFileIcon = (type) => {
  const iconMap = {
    '.pdf': 'filePdf',
    '.docx': 'fileWord',
    '.txt': 'fileAlt',
    '.md': 'fileCode'
  }
  return iconMap[type] || 'file'
}

const formatFileSize = (bytes) => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i]
}

const getStatusText = (status) => {
  const statusMap = {
    uploading: '上传中...',
    success: '上传成功',
    error: '上传失败'
  }
  return statusMap[status] || status
}

const generateOutline = () => {
  isGenerating.value = true
  
  setTimeout(() => {
    outlineItems.value = generateMockOutline(form.value.topic, form.value.pageCount)
    isGenerating.value = false
    currentStep.value = 2
  }, 2000)
}

const generateMockOutline = (topic, pageCount) => {
  const pagesPerSection = Math.floor(pageCount / 4)
  let pageNumber = 1
  
  const outline = [
    {
      id: generateId(),
      title: '封面',
      expanded: true,
      children: [
        { id: generateId(), title: `${topic} - 封面`, pageNumber: pageNumber++ }
      ]
    },
    {
      id: generateId(),
      title: '目录',
      expanded: false,
      children: [
        { id: generateId(), title: '目录', pageNumber: pageNumber++ }
      ]
    },
    {
      id: generateId(),
      title: '第一章：项目概述',
      expanded: true,
      children: [
        { id: generateId(), title: '项目背景', pageNumber: pageNumber++ },
        { id: generateId(), title: '目标与意义', pageNumber: pageNumber++ },
        { id: generateId(), title: '核心概念', pageNumber: pageNumber++ }
      ]
    },
    {
      id: generateId(),
      title: '第二章：详细内容',
      expanded: true,
      children: [
        { id: generateId(), title: '关键要点一', pageNumber: pageNumber++ },
        { id: generateId(), title: '关键要点二', pageNumber: pageNumber++ },
        { id: generateId(), title: '数据与分析', pageNumber: pageNumber++ }
      ]
    },
    {
      id: generateId(),
      title: '第三章：总结与展望',
      expanded: false,
      children: [
        { id: generateId(), title: '成果总结', pageNumber: pageNumber++ },
        { id: generateId(), title: '未来规划', pageNumber: pageNumber++ }
      ]
    },
    {
      id: generateId(),
      title: '结束页',
      expanded: false,
      children: [
        { id: generateId(), title: '谢谢观看', pageNumber: pageNumber++ }
      ]
    }
  ]
  
  return outline
}

const regenerateOutline = () => {
  if (confirm('确定要重新生成大纲吗？当前修改将丢失。')) {
    generateOutline()
  }
}

const prevStep = () => {
  currentStep.value = 1
}

const confirmOutline = () => {
  emit('generate', { 
    ...form.value, 
    files: uploadedFiles.value,
    outline: outlineItems.value 
  })
  close()
}

const toggleItem = (item) => {
  item.expanded = !item.expanded
}

const startEdit = (item) => {
  item.editing = true
  nextTick(() => {
    const inputs = document.querySelectorAll('.item-input')
    inputs[inputs.length - 1]?.focus()
  })
}

const addSection = () => {
  const newSection = {
    id: generateId(),
    title: '新章节',
    expanded: true,
    children: []
  }
  outlineItems.value.push(newSection)
  startEdit(newSection)
}

const removeItem = (item) => {
  if (confirm(`确定要删除章节 "${item.title}" 吗？`)) {
    outlineItems.value = outlineItems.value.filter(i => i.id !== item.id)
    renumberPages()
  }
}

const addChildItem = (parentItem) => {
  if (!parentItem.children) {
    parentItem.children = []
  }
  
  const newChild = {
    id: generateId(),
    title: '新页面',
    pageNumber: 0
  }
  
  parentItem.children.push(newChild)
  parentItem.expanded = true
  renumberPages()
  startEdit(newChild)
}

const removeChildItem = (parentItem, child) => {
  if (confirm(`确定要删除页面 "${child.title}" 吗？`)) {
    parentItem.children = parentItem.children.filter(c => c.id !== child.id)
    renumberPages()
  }
}

const renumberPages = () => {
  let pageNumber = 1
  outlineItems.value.forEach(item => {
    if (item.children) {
      item.children.forEach(child => {
        child.pageNumber = pageNumber++
      })
    }
  })
}
</script>

<style scoped>
.modal {
  display: none;
  position: fixed;
  inset: 0;
  z-index: 2000;
  align-items: center;
  justify-content: center;
}

.modal.active {
  display: flex;
}

.modal-overlay {
  position: absolute;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  backdrop-filter: blur(4px);
}

.modal-content {
  position: relative;
  width: 640px;
  max-height: 85vh;
  background: white;
  border-radius: var(--radius-2xl);
  box-shadow: var(--shadow-2xl);
  display: flex;
  flex-direction: column;
  animation: slideUp 0.3s ease;
  overflow: hidden;
}

.modal-content.expanded {
  width: 800px;
  max-height: 90vh;
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--space-6) var(--space-8);
  border-bottom: 1px solid var(--gray-200);
}

.modal-title {
  font-size: 20px;
  font-weight: 600;
  color: var(--gray-800);
}

.modal-close {
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--radius-md);
  color: var(--gray-500);
  transition: all 0.2s ease;
  background: transparent;
  border: none;
  cursor: pointer;
}

.modal-close:hover {
  background: var(--gray-100);
  color: var(--gray-700);
}

.modal-body {
  flex: 1;
  padding: var(--space-6) var(--space-8);
  overflow-y: auto;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: var(--space-3);
  padding: var(--space-4) var(--space-8);
  border-top: 1px solid var(--gray-200);
  background: var(--gray-50);
}

.step-content {
  animation: fadeIn 0.3s ease;
}

.form-step {
  margin-bottom: var(--space-6);
}

.form-group {
  margin-bottom: var(--space-6);
}

.form-label {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  font-size: 14px;
  font-weight: 600;
  color: var(--gray-700);
  margin-bottom: var(--space-3);
}

.form-label.optional {
  font-weight: 500;
  color: var(--gray-600);
}

.step-number {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  font-size: 12px;
  font-weight: 600;
  color: white;
  background: var(--primary-500);
  border-radius: var(--radius-full);
}

.char-count {
  text-align: right;
  font-size: 12px;
  color: var(--gray-400);
  margin-top: var(--space-2);
}

.char-count.error {
  color: var(--error-500);
}

.upload-area {
  border: 2px dashed var(--gray-300);
  border-radius: var(--radius-lg);
  padding: var(--space-8);
  text-align: center;
  cursor: pointer;
  transition: all 0.2s ease;
  position: relative;
}

.upload-area:hover,
.upload-area.dragover {
  border-color: var(--primary-400);
  background: var(--primary-50);
}

.file-input {
  display: none;
}

.upload-icon {
  color: var(--gray-400);
  margin-bottom: var(--space-3);
}

.upload-text {
  font-size: 14px;
  font-weight: 500;
  color: var(--gray-700);
  margin-bottom: var(--space-1);
}

.upload-hint {
  font-size: 12px;
  color: var(--gray-500);
}

.uploaded-files-list {
  margin-top: var(--space-4);
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}

.file-item {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-3) var(--space-4);
  background: var(--gray-50);
  border-radius: var(--radius-lg);
  border: 1px solid var(--gray-200);
}

.file-icon {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: white;
  border-radius: var(--radius-md);
  flex-shrink: 0;
}

.file-icon.pdf {
  color: #EF4444;
}

.file-icon.docx {
  color: #3B82F6;
}

.file-icon.txt,
.file-icon.md {
  color: #6B7280;
}

.file-info {
  flex: 1;
  min-width: 0;
}

.file-name {
  font-size: 14px;
  font-weight: 500;
  color: var(--gray-800);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  margin-bottom: 2px;
}

.file-meta {
  font-size: 12px;
  color: var(--gray-500);
  display: flex;
  align-items: center;
  gap: var(--space-2);
}

.file-size {
  padding: 1px 6px;
  background: var(--gray-200);
  border-radius: var(--radius-sm);
}

.file-status {
  display: flex;
  align-items: center;
  gap: var(--space-1);
}

.file-status.uploading {
  color: var(--primary-500);
}

.file-status.success {
  color: var(--success-500);
}

.upload-progress {
  width: 100%;
  height: 4px;
  background: var(--gray-200);
  border-radius: var(--radius-full);
  overflow: hidden;
  margin-top: var(--space-2);
}

.upload-progress-bar {
  height: 100%;
  background: linear-gradient(90deg, var(--primary-500), var(--primary-400));
  border-radius: var(--radius-full);
  transition: width 0.3s ease;
}

.file-remove {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--gray-400);
  background: transparent;
  border: none;
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all 0.2s ease;
  flex-shrink: 0;
}

.file-remove:hover {
  color: var(--error-500);
  background: var(--error-50);
}

.style-options {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: var(--space-3);
}

.style-card {
  padding: var(--space-4);
  border: 2px solid var(--gray-200);
  border-radius: var(--radius-lg);
  text-align: center;
  cursor: pointer;
  transition: all 0.2s ease;
}

.style-card:hover {
  border-color: var(--primary-300);
}

.style-card.active {
  border-color: var(--primary-500);
  background: var(--primary-50);
}

.style-icon {
  font-size: 24px;
  margin-bottom: var(--space-2);
}

.style-name {
  display: block;
  font-size: 13px;
  font-weight: 500;
  color: var(--gray-700);
  margin-bottom: var(--space-2);
}

.style-radio {
  width: 16px;
  height: 16px;
  border: 2px solid var(--gray-300);
  border-radius: var(--radius-full);
  margin: 0 auto;
  transition: all 0.2s ease;
}

.style-card.active .style-radio {
  border-color: var(--primary-500);
  background: var(--primary-500);
  box-shadow: inset 0 0 0 3px white;
}

.page-slider {
  padding: var(--space-4) 0;
}

.slider {
  width: 100%;
  height: 6px;
  -webkit-appearance: none;
  appearance: none;
  background: var(--gray-200);
  border-radius: var(--radius-full);
  outline: none;
}

.slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 20px;
  height: 20px;
  background: var(--primary-500);
  border-radius: var(--radius-full);
  cursor: pointer;
  box-shadow: var(--shadow-md);
}

.slider::-moz-range-thumb {
  width: 20px;
  height: 20px;
  background: var(--primary-500);
  border-radius: var(--radius-full);
  cursor: pointer;
  border: none;
  box-shadow: var(--shadow-md);
}

.slider-info {
  display: flex;
  justify-content: space-between;
  margin-top: var(--space-3);
}

.page-count {
  font-size: 15px;
  font-weight: 600;
  color: var(--primary-600);
}

.page-hint {
  font-size: 13px;
  color: var(--gray-500);
}

.outline-editor {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.outline-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--space-4);
  padding-bottom: var(--space-4);
  border-bottom: 1px solid var(--gray-200);
}

.outline-stats {
  display: flex;
  gap: var(--space-4);
}

.stat-item {
  display: flex;
  align-items: center;
  gap: var(--space-1);
  font-size: 13px;
  color: var(--gray-600);
}

.outline-actions {
  display: flex;
  gap: var(--space-2);
}

.outline-tree-container {
  flex: 1;
  overflow-y: auto;
  padding-right: var(--space-2);
}

.outline-tree {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

.outline-item {
  border: 1px solid var(--gray-200);
  border-radius: var(--radius-lg);
  overflow: hidden;
  background: white;
}

.outline-item-header {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-3) var(--space-4);
  background: var(--gray-50);
  transition: background 0.2s ease;
}

.outline-item-header:hover {
  background: var(--gray-100);
}

.toggle-btn {
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
  background: transparent;
  cursor: pointer;
  color: var(--gray-500);
  transition: transform 0.2s ease;
  flex-shrink: 0;
}

.toggle-btn.hidden {
  visibility: hidden;
}

.toggle-btn:hover {
  color: var(--primary-600);
}

.outline-item.expanded .toggle-btn {
  transform: rotate(90deg);
}

.item-number {
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--primary-500);
  color: white;
  font-size: 12px;
  font-weight: 600;
  border-radius: var(--radius-full);
  flex-shrink: 0;
}

.item-title,
.child-title {
  flex: 1;
  font-size: 14px;
  font-weight: 500;
  color: var(--gray-800);
  cursor: text;
}

.item-input {
  flex: 1;
  font-size: 14px;
  font-weight: 500;
  color: var(--gray-800);
  border: 1px solid var(--primary-400);
  border-radius: var(--radius-sm);
  padding: var(--space-1) var(--space-2);
  outline: none;
  background: white;
}

.item-actions {
  display: flex;
  gap: var(--space-1);
  opacity: 0;
  transition: opacity 0.2s ease;
}

.outline-item:hover .item-actions,
.outline-child-item:hover .item-actions {
  opacity: 1;
}

.action-btn {
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
  background: transparent;
  cursor: pointer;
  color: var(--gray-500);
  border-radius: var(--radius-sm);
  transition: all 0.2s ease;
}

.action-btn:hover {
  background: var(--gray-200);
  color: var(--gray-700);
}

.action-btn.danger:hover {
  background: var(--error-50);
  color: var(--error-600);
}

.outline-children {
  padding: var(--space-2) 0;
  background: white;
}

.outline-child-item {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-2) var(--space-4);
  padding-left: calc(var(--space-4) + 48px);
  transition: background 0.2s ease;
}

.outline-child-item:hover {
  background: var(--gray-50);
}

.child-number {
  width: 28px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--gray-200);
  color: var(--gray-600);
  font-size: 11px;
  font-weight: 600;
  border-radius: var(--radius-sm);
  flex-shrink: 0;
}

.add-child-btn {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-1);
  padding: var(--space-2);
  border: none;
  background: transparent;
  color: var(--primary-600);
  font-size: 13px;
  cursor: pointer;
  transition: background 0.2s ease;
}

.add-child-btn:hover {
  background: var(--primary-50);
}

.add-section-btn {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-2);
  padding: var(--space-4);
  margin-top: var(--space-4);
  border: 2px dashed var(--gray-300);
  border-radius: var(--radius-lg);
  background: transparent;
  color: var(--gray-600);
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
}

.add-section-btn:hover {
  border-color: var(--primary-400);
  color: var(--primary-600);
  background: var(--primary-50);
}

@keyframes slideUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes fadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

@media (max-width: 1024px) {
  .modal-content.expanded {
    width: 90%;
  }
}

@media (max-width: 640px) {
  .modal-content,
  .modal-content.expanded {
    width: 100%;
    max-height: 100vh;
    border-radius: 0;
  }
  
  .style-options {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>