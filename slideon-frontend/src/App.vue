<template>
  <router-view />

  <Teleport to="body">
    <Transition name="ball-pop">
      <div
        v-if="ballState.visible && !ballExpanding"
        class="floating-ball-global"
        :class="[ballState.status, { 'ball-enter': ballEntering }]"
        :style="ballStyle"
        @mousedown.prevent="handleDragStart"
        @touchstart.prevent="handleDragStart"
        @click="handleBallClick"
      >
        <div class="ball-inner-global">
          <template v-if="ballState.status === 'generating'">
            <IconBase name="spinner" :size="22" class="ball-spin" />
            <span class="ball-text">Generating</span>
          </template>
          <template v-else-if="ballState.status === 'success'">
            <IconBase name="check" :size="22" />
            <span class="ball-text">Ready</span>
          </template>
          <template v-else-if="ballState.status === 'error'">
            <IconBase name="times" :size="22" />
            <span class="ball-text">Failed</span>
          </template>
        </div>
      </div>
    </Transition>
  </Teleport>

  <Teleport to="body">
    <Transition name="modal-slide">
      <div v-if="state.modalVisible" class="modal-global active" @click.self="minimizeModal">
        <div class="modal-overlay" @click="minimizeModal"></div>
        <div class="modal-content" ref="modalContentRef">
          <div class="modal-header">
            <h2 class="modal-title">Generate Outline</h2>
            <button class="modal-close" type="button" @click="minimizeModal">
              <IconBase name="times" :size="20" />
            </button>
          </div>

          <div class="modal-body">
            <div class="mode-tabs">
              <button
                type="button"
                :class="['mode-tab', { active: state.inputMode === 'topic' }]"
                :disabled="state.isGenerating"
                @click="state.inputMode = 'topic'"
              >
                <IconBase name="magic" :size="14" />
                Topic
              </button>
              <button
                type="button"
                :class="['mode-tab', { active: state.inputMode === 'document' }]"
                :disabled="state.isGenerating"
                @click="state.inputMode = 'document'"
              >
                <IconBase name="paperclip" :size="14" />
                Document
              </button>
            </div>

            <div class="form-step">
              <label class="form-label">
                <span class="step-number">1</span>
                Model
              </label>
              <div class="model-options">
                <button
                  v-for="item in modelProviders"
                  :key="item.provider"
                  type="button"
                  :class="['model-option', { active: state.modelProvider === item.provider }]"
                  :disabled="state.isGenerating"
                  @click="setModelProvider(item.provider)"
                >
                  <strong>{{ item.label }}</strong>
                  <span>{{ item.model }}</span>
                </button>
              </div>
            </div>

            <div class="form-step">
              <label class="form-label">
                <span class="step-number">2</span>
                Length
              </label>
              <div class="page-count-options">
                <button
                  v-for="item in pageCountOptions"
                  :key="item.value"
                  type="button"
                  :class="['page-count-option', { active: state.pageCountPreset === item.value }]"
                  :disabled="state.isGenerating"
                  @click="setPageCountPreset(item.value)"
                >
                  <strong>{{ item.label }}</strong>
                  <span>{{ item.desc }}</span>
                </button>
              </div>
            </div>

            <div class="form-step">
              <label class="form-label">
                <span class="step-number">3</span>
                {{ state.inputMode === 'topic' ? 'Topic' : 'Upload Document' }}
              </label>
              <textarea
                v-if="state.inputMode === 'topic'"
                v-model="state.formTopic"
                class="input textarea"
                placeholder="Example: 软件工程介绍"
                :disabled="state.isGenerating"
                @input="onTopicInput"
              ></textarea>
              <div
                v-if="state.inputMode === 'topic'"
                class="char-count"
                :class="{ error: charCount > 500 }"
              >
                {{ charCount }}/500
              </div>

              <template v-else>
                <input
                  ref="documentInput"
                  type="file"
                  accept=".pdf,.docx,.txt,.md,.pptx"
                  style="display: none"
                  :disabled="state.isGenerating"
                  @change="handleDocumentSelected"
                >
                <button
                  type="button"
                  class="document-upload"
                  :disabled="state.isGenerating"
                  @click="documentInput?.click()"
                >
                  <IconBase name="paperclip" :size="26" />
                  <strong>{{ state.selectedDocument ? state.selectedDocument.name : 'Choose a document' }}</strong>
                  <span v-if="state.selectedDocument">{{ formatFileSize(state.selectedDocument.size) }}</span>
                  <small v-else>PDF, DOCX, TXT, MD, PPTX</small>
                </button>
              </template>
            </div>

            <div v-if="state.inputMode === 'topic'" class="form-step">
              <label class="rag-option">
                <span>
                  <strong>RAG Enhance</strong>
                  <small>Knowledge base and web search</small>
                </span>
                <input v-model="state.useRag" type="checkbox" :disabled="state.isGenerating">
              </label>
            </div>
          </div>

          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" @click="handleCancel">
              {{ state.isGenerating ? 'Cancel generation' : 'Cancel' }}
            </button>
            <button
              type="button"
              class="btn btn-primary"
              :disabled="state.isGenerating || !canGenerate"
              @click="doGenerate"
            >
              <IconBase v-if="state.isGenerating" name="spinner" :size="16" class="ball-spin" />
              <IconBase v-else name="magic" :size="16" />
              {{ state.isGenerating ? 'Generating...' : 'Generate Outline' }}
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>

  <Teleport to="body">
    <div v-if="ballExpanding" class="expand-overlay">
      <div class="expand-ball" :style="expandBallStyle">
        <div class="ball-inner-global">
          <IconBase name="check" :size="22" />
          <span class="ball-text">Opening</span>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { ref, computed, nextTick, watch, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useFloatingBall } from './composables/useFloatingBall.js'
import { apiService } from './services/api.js'
import { useOutlineStore } from './stores/outlineStore.js'
import { useAuthStore } from './stores/authStore.js'
import IconBase from './components/icons/IconBase.vue'

const router = useRouter()
const outlineStore = useOutlineStore()
const authStore = useAuthStore()
const {
  state,
  showBall,
  hideBall,
  setSuccess,
  setError,
  showModal,
  hideModal,
  cancelGeneration,
  generateOutline,
  onDragStart,
  setModelProvider,
  setPageCountPreset
} = useFloatingBall()

const modelProviders = [
  { provider: 'deepseek', label: 'DeepSeek', model: 'Deepseek-V4-pro' },
  { provider: 'qwen', label: 'Qwen', model: 'qwen-plus' },
  { provider: 'kimi', label: 'Kimi', model: 'kimi-k2.6' }
]

const pageCountOptions = [
  { value: 'short', label: 'Short', desc: 'About 8-10 pages' },
  { value: 'medium', label: 'Medium', desc: 'About 13-15 pages' },
  { value: 'long', label: 'Long', desc: 'About 18-21 pages' }
]

onMounted(() => {
  authStore.init()
})

const ballState = state
const ballEntering = ref(false)
const ballExpanding = ref(false)
const modalContentRef = ref(null)
const documentInput = ref(null)

const ballStyle = computed(() => ({
  left: ballState.position.x != null ? `${ballState.position.x}px` : undefined,
  top: ballState.position.y != null ? `${ballState.position.y}px` : undefined,
  right: ballState.position.x == null ? '32px' : undefined,
  bottom: ballState.position.y == null ? '32px' : undefined
}))

const expandBallStyle = computed(() => ({
  left: ballState._expandFromX != null ? `${ballState._expandFromX}px` : '50%',
  top: ballState._expandFromY != null ? `${ballState._expandFromY}px` : '50%',
  transform: 'translate(-50%, -50%) scale(1)'
}))

const charCount = computed(() => state.formTopic.length)
const canGenerate = computed(() => (
  state.inputMode === 'topic'
    ? !!state.formTopic.trim()
    : !!state.selectedDocument
))

let dragMoved = false

function handleDragStart(e) {
  dragMoved = false
  onDragStart(e)
  const checkMove = () => {
    dragMoved = true
    document.removeEventListener('mousemove', checkMove)
    document.removeEventListener('touchmove', checkMove)
  }
  document.addEventListener('mousemove', checkMove, { once: true })
  document.addEventListener('touchmove', checkMove, { once: true })
}

function handleBallClick() {
  if (dragMoved) return

  if (ballState.status === 'success') {
    expandToEditor()
    return
  }

  if (ballState.status === 'generating') {
    expandToModal()
    return
  }

  if (ballState.status === 'error') {
    hideBall()
  }
}

async function expandToModal() {
  ballState.visible = false
  await nextTick()
  await new Promise(resolve => setTimeout(resolve, 200))
  showModal()
}

async function expandToEditor() {
  const id = ballState.outlineId
  if (!id) return

  ballExpanding.value = true
  ballState._expandFromX = ballState.position.x
  ballState._expandFromY = ballState.position.y

  await nextTick()
  await new Promise(resolve => setTimeout(resolve, 100))

  const el = document.querySelector('.expand-ball')
  if (el) {
    el.style.transform = 'translate(-50%, -50%) scale(25)'
    el.style.transition = 'transform 0.6s cubic-bezier(0.34, 1.56, 0.64, 1)'
  }

  await new Promise(resolve => setTimeout(resolve, 650))
  hideBall()
  ballExpanding.value = false
  router.replace({ path: '/outline-editor', query: { id } })
}

function minimizeModal() {
  if (state.isGenerating) {
    animateMinimize()
  } else {
    hideModal()
  }
}

async function animateMinimize() {
  hideModal()
  await new Promise(resolve => setTimeout(resolve, 150))
  ballEntering.value = true
  showBall('generating')
  setTimeout(() => { ballEntering.value = false }, 500)
}

function handleCancel() {
  if (state.isGenerating) {
    cancelGeneration()
    hideBall()
    hideModal()
  } else {
    hideModal()
  }
}

function onTopicInput() {
  if (charCount.value > 500) {
    state.formTopic = state.formTopic.slice(0, 500)
  }
}

function handleDocumentSelected(event) {
  state.selectedDocument = event.target.files?.[0] || null
}

function formatFileSize(bytes) {
  if (!Number.isFinite(bytes) || bytes <= 0) return '0 B'
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`
}

async function doGenerate() {
  if (!canGenerate.value) {
    alert(state.inputMode === 'topic' ? 'Please enter a topic.' : 'Please choose a document.')
    return
  }

  const result = await generateOutline(apiService, outlineStore)

  if (result.success) {
    hideModal()
    const cx = ballState.position.x != null ? ballState.position.x : window.innerWidth - 104
    const cy = ballState.position.y != null ? ballState.position.y : window.innerHeight - 104
    ballState.position = { x: cx, y: cy }
    ballEntering.value = true
    setSuccess(result.id)
    ballEntering.value = false
  } else if (!result.aborted && state.modalVisible) {
    setError()
    alert(`Generate outline failed: ${result.error || 'Unknown error'}`)
  }
}

watch(() => ballState.status, (val) => {
  if (val === 'success' && ballState.visible) {
    ballEntering.value = true
    setTimeout(() => { ballEntering.value = false }, 500)
  }
})
</script>

<style>
.floating-ball-global {
  position: fixed;
  width: 72px;
  height: 72px;
  background: #fff;
  border-radius: 50%;
  box-shadow: 0 4px 24px rgba(0,0,0,0.18), 0 0 0 1px rgba(0,0,0,0.06);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: grab;
  z-index: 9000;
  user-select: none;
}

.floating-ball-global:active { cursor: grabbing; }
.floating-ball-global:hover { box-shadow: 0 8px 32px rgba(0,0,0,0.22), 0 0 0 1px rgba(0,0,0,0.08); }
.floating-ball-global.success { border: 2px solid #10b981; }
.floating-ball-global.error { border: 2px solid #ef4444; }

.floating-ball-global.ball-enter {
  animation: ballBounceIn 0.5s cubic-bezier(0.34, 1.56, 0.64, 1);
}

@keyframes ballBounceIn {
  0% { transform: scale(0.3); opacity: 0; }
  60% { transform: scale(1.15); }
  100% { transform: scale(1); opacity: 1; }
}

.ball-pop-enter-active { animation: ballBounceIn 0.45s cubic-bezier(0.34, 1.56, 0.64, 1); }
.ball-pop-leave-active { animation: ballPopOut 0.3s ease-in; }

@keyframes ballPopOut {
  0% { transform: scale(1); opacity: 1; }
  100% { transform: scale(0.2); opacity: 0; }
}

.ball-inner-global {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
  color: #374151;
  pointer-events: none;
}
.floating-ball-global.success .ball-inner-global { color: #10b981; }
.floating-ball-global.error .ball-inner-global { color: #ef4444; }
.ball-text { font-size: 10px; font-weight: 600; white-space: nowrap; }
.ball-spin { animation: spin 1s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }

.expand-overlay {
  position: fixed;
  inset: 0;
  z-index: 9500;
  background: rgba(255,255,255,0.6);
  backdrop-filter: blur(8px);
  animation: fadeIn 0.3s ease;
}

.expand-ball {
  position: fixed;
  width: 72px;
  height: 72px;
  background: #fff;
  border: 2px solid #10b981;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9501;
}

.modal-global {
  display: none;
  position: fixed;
  inset: 0;
  z-index: 2000;
  align-items: center;
  justify-content: center;
}
.modal-global.active { display: flex; }
.modal-overlay {
  position: absolute;
  inset: 0;
  background: rgba(0,0,0,0.5);
  backdrop-filter: blur(4px);
}

.modal-slide-enter-active { transition: all 0.35s cubic-bezier(0.34, 1.56, 0.64, 1); }
.modal-slide-leave-active { transition: all 0.25s ease-in; }
.modal-slide-enter-from { opacity: 0; }
.modal-slide-enter-from .modal-content { transform: scale(0.7) translateY(30px); opacity: 0; }
.modal-slide-leave-to { opacity: 0; }
.modal-slide-leave-to .modal-content { transform: scale(0.7) translateY(30px); opacity: 0; }
.modal-slide-enter-to .modal-content,
.modal-slide-leave-from .modal-content { transform: scale(1) translateY(0); opacity: 1; }
.modal-slide-enter-active .modal-content,
.modal-slide-leave-active .modal-content { transition: all 0.35s cubic-bezier(0.34, 1.56, 0.64, 1); }

.modal-content {
  position: relative;
  width: min(640px, calc(100vw - 32px));
  max-height: 85vh;
  background: #fff;
  border-radius: 16px;
  box-shadow: 0 25px 50px -12px rgba(0,0,0,0.25);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 24px 32px;
  border-bottom: 1px solid #e5e7eb;
}
.modal-title { font-size: 20px; font-weight: 600; color: #1f2937; }
.modal-close {
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 6px;
  color: #6b7280;
  background: transparent;
  border: none;
  cursor: pointer;
}
.modal-close:hover { background: #f3f4f6; color: #374151; }
.modal-body { flex: 1; padding: 24px 32px; overflow-y: auto; }
.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 16px 32px;
  border-top: 1px solid #e5e7eb;
  background: #f9fafb;
}

.mode-tabs {
  display: flex;
  gap: 8px;
  padding: 4px;
  margin-bottom: 20px;
  background: #f3f4f6;
  border-radius: 8px;
}
.mode-tab {
  flex: 1;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  border: none;
  border-radius: 6px;
  background: transparent;
  color: #4b5563;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
}
.mode-tab.active {
  background: #fff;
  color: #2563eb;
  box-shadow: 0 1px 2px rgba(0,0,0,0.08);
}

.form-step { margin-bottom: 24px; }
.form-label {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  font-weight: 600;
  color: #374151;
  margin-bottom: 12px;
}
.step-number {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  font-size: 12px;
  font-weight: 600;
  color: #fff;
  background: #6366f1;
  border-radius: 999px;
}

.model-options,
.page-count-options {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px;
}
.model-option,
.page-count-option {
  min-height: 64px;
  padding: 10px 12px;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  background: #fff;
  color: #374151;
  text-align: left;
  cursor: pointer;
  transition: all 0.2s ease;
}
.model-option strong,
.model-option span,
.page-count-option strong,
.page-count-option span {
  display: block;
  line-height: 1.3;
}
.model-option strong,
.page-count-option strong { font-size: 14px; font-weight: 700; }
.model-option span,
.page-count-option span {
  margin-top: 4px;
  font-size: 12px;
  color: #6b7280;
  overflow-wrap: anywhere;
}
.model-option:hover,
.page-count-option:hover { border-color: #a5b4fc; background: #f8faff; }
.model-option.active,
.page-count-option.active {
  border-color: #6366f1;
  background: #eef2ff;
  box-shadow: 0 0 0 1px #6366f1 inset;
}
.model-option:disabled,
.page-count-option:disabled { cursor: not-allowed; opacity: 0.65; }

.textarea {
  min-height: 120px;
  padding: 12px 16px;
  resize: vertical;
  width: 100%;
  font-size: 14px;
  color: #374151;
  background: #fff;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  outline: none;
  font-family: inherit;
}
.textarea:focus { border-color: #a5b4fc; box-shadow: 0 0 0 3px #e0e7ff; }
.input:disabled { background: #f3f4f6; color: #9ca3af; }
.char-count { text-align: right; font-size: 12px; color: #9ca3af; margin-top: 8px; }
.char-count.error { color: #ef4444; }

.document-upload {
  width: 100%;
  min-height: 132px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 24px;
  border: 2px dashed #d1d5db;
  border-radius: 8px;
  background: #f9fafb;
  color: #4b5563;
  cursor: pointer;
  text-align: center;
  transition: all 0.2s ease;
}
.document-upload:hover {
  border-color: #60a5fa;
  background: #eff6ff;
  color: #2563eb;
}
.document-upload:disabled { cursor: not-allowed; opacity: 0.7; }
.document-upload small { color: #9ca3af; }

.rag-option {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 16px;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  background: #fff;
  color: #374151;
}
.rag-option span { display: flex; flex-direction: column; gap: 4px; }
.rag-option strong { font-size: 14px; }
.rag-option small { color: #6b7280; }
.rag-option input { width: 20px; height: 20px; accent-color: #6366f1; }

.btn {
  min-width: 96px;
  height: 40px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  border-radius: 6px;
  border: 1px solid #d1d5db;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
}
.btn-secondary { background: #fff; color: #374151; }
.btn-secondary:hover { background: #f3f4f6; }
.btn-primary {
  background: #6366f1;
  border-color: #6366f1;
  color: #fff;
}
.btn-primary:hover { background: #4f46e5; border-color: #4f46e5; }
.btn:disabled { cursor: not-allowed; opacity: 0.65; }

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

@media (max-width: 640px) {
  .modal-header,
  .modal-body,
  .modal-footer {
    padding-left: 20px;
    padding-right: 20px;
  }
  .model-options,
  .page-count-options {
    grid-template-columns: 1fr;
  }
  .modal-footer {
    flex-direction: column-reverse;
  }
  .btn {
    width: 100%;
  }
}
</style>
