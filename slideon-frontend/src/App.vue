<template>
  <router-view />

  <!-- 全局浮动球 -->
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
            <span class="ball-text">生成中</span>
          </template>
          <template v-else-if="ballState.status === 'success'">
            <IconBase name="check" :size="22" />
            <span class="ball-text">生成成功</span>
          </template>
          <template v-else-if="ballState.status === 'error'">
            <IconBase name="times" :size="22" />
            <span class="ball-text">生成失败</span>
          </template>
        </div>
      </div>
    </Transition>
  </Teleport>

  <!-- 全局大纲生成弹窗 -->
  <Teleport to="body">
    <Transition name="modal-slide">
      <div v-if="state.modalVisible" class="modal-global active" @click.self="minimizeModal">
        <div class="modal-overlay" @click="minimizeModal"></div>
        <div class="modal-content" ref="modalContentRef">
          <div class="modal-header">
            <h2 class="modal-title">智能生成大纲</h2>
            <button class="modal-close" @click="minimizeModal">
              <IconBase name="times" :size="20" />
            </button>
          </div>

          <div class="modal-body">
            <div class="step-content">
              <div class="form-step">
                <label class="form-label">
                  <span class="step-number">1</span>
                  输入主题
                </label>
                <textarea
                  class="input textarea"
                  placeholder="描述你的PPT主题、目标受众和主要内容...

例如：为科技公司CEO准备的产品发布会PPT，介绍新一代AI芯片的性能优势和市场前景"
                  v-model="state.formTopic"
                  :disabled="state.isGenerating"
                  @input="onTopicInput"
                ></textarea>
                <div class="char-count" :class="{ error: charCount > 500 }">{{ charCount }}/500</div>
              </div>

              <div class="form-step">
                <label class="form-label">
                  <span class="step-number">2</span>
                  AI增强选项
                </label>
                <div class="rag-toggle-row">
                  <div class="rag-toggle-label">
                    <span class="rag-toggle-title">混合RAG增强 (知识库 + 网络搜索)</span>
                    <span class="rag-toggle-desc">AI将参考知识库和网络资料生成更专业的内容</span>
                  </div>
                  <button
                    :class="['rag-toggle-switch', { active: state.useRag }]"
                    @click="state.useRag = !state.useRag"
                    :disabled="state.isGenerating"
                    role="switch"
                    :aria-checked="state.useRag"
                  >
                    <span class="rag-toggle-knob"></span>
                  </button>
                </div>
              </div>
            </div>
          </div>

          <div class="modal-footer">
            <button class="btn btn-secondary" @click="handleCancel">取消</button>
            <button
              class="btn btn-primary"
              :disabled="state.isGenerating || !state.formTopic.trim()"
              @click="doGenerate"
            >
              <IconBase v-if="state.isGenerating" name="spinner" :size="14" class="animate-spin" />
              <IconBase v-else name="magic" :size="14" />
              {{ state.isGenerating ? '生成大纲中...' : '生成大纲' }}
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>

  <!-- 展开动画遮罩 -->
  <Teleport to="body">
    <div v-if="ballExpanding" class="expand-overlay">
      <div class="expand-ball" :style="expandBallStyle">
        <div class="ball-inner-global">
          <IconBase name="check" :size="22" />
          <span class="ball-text">正在打开...</span>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { ref, computed, nextTick, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useFloatingBall } from './composables/useFloatingBall.js'
import { apiService } from './services/api.js'
import { useOutlineStore } from './stores/outlineStore.js'
import IconBase from './components/icons/IconBase.vue'

const router = useRouter()
const outlineStore = useOutlineStore()
const { state, showBall, hideBall, setSuccess, showModal, hideModal, cancelGeneration, generateOutline, onDragStart } = useFloatingBall()

const ballState = state
const ballEntering = ref(false)
const ballExpanding = ref(false)
const modalContentRef = ref(null)

const ballStyle = computed(() => ({
  left: ballState.position.x != null ? ballState.position.x + 'px' : undefined,
  top: ballState.position.y != null ? ballState.position.y + 'px' : undefined,
  right: ballState.position.x == null ? '32px' : undefined,
  bottom: ballState.position.y == null ? '32px' : undefined
}))

const expandBallStyle = computed(() => ({
  left: ballState._expandFromX != null ? ballState._expandFromX + 'px' : '50%',
  top: ballState._expandFromY != null ? ballState._expandFromY + 'px' : '50%',
  transform: 'translate(-50%, -50%) scale(1)'
}))

const charCount = computed(() => state.formTopic.length)

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
    // Animate ball expanding into outline editor
    expandToEditor()
    return
  }

  if (ballState.status === 'generating') {
    // Animate ball back to center and show modal
    expandToModal()
    return
  }

  if (ballState.status === 'error') {
    hideBall()
  }
}

async function expandToModal() {
  // Smooth transition: ball fades out via Vue transition, then modal appears
  ballState.visible = false
  await nextTick()
  await new Promise(r => setTimeout(r, 200))
  showModal()
}

async function expandToEditor() {
  const id = ballState.outlineId
  if (!id) return

  ballExpanding.value = true
  ballState._expandFromX = ballState.position.x
  ballState._expandFromY = ballState.position.y

  await nextTick()
  await new Promise(r => setTimeout(r, 100))

  // Scale up animation
  const el = document.querySelector('.expand-ball')
  if (el) {
    el.style.transform = 'translate(-50%, -50%) scale(25)'
    el.style.transition = 'transform 0.6s cubic-bezier(0.34, 1.56, 0.64, 1)'
  }

  await new Promise(r => setTimeout(r, 650))
  hideBall()
  ballExpanding.value = false
  router.replace({ path: '/outline-editor', query: { id } })
}

function minimizeModal() {
  if (state.isGenerating) {
    // Animate: modal shrinks to ball position
    animateMinimize()
  } else {
    hideModal()
  }
}

async function animateMinimize() {
  hideModal()
  // Show ball at corner with bounce-in animation
  await new Promise(r => setTimeout(r, 150))
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

async function doGenerate() {
  if (!state.formTopic.trim()) {
    alert('请输入主题')
    return
  }

  const result = await generateOutline(apiService, outlineStore)

  if (result.success) {
    hideModal()
    // Don't auto-navigate — show success ball instead
    const cx = ballState.position.x != null ? ballState.position.x : window.innerWidth - 104
    const cy = ballState.position.y != null ? ballState.position.y : window.innerHeight - 104
    ballState.position = { x: cx, y: cy }
    ballEntering.value = true
    setSuccess(result.id)
    ballEntering.value = false
  } else if (!result.aborted) {
    // Hide modal and show error floating ball so user can see the failure
    hideModal()
    const cx = ballState.position.x != null ? ballState.position.x : window.innerWidth - 104
    const cy = ballState.position.y != null ? ballState.position.y : window.innerHeight - 104
    ballState.position = { x: cx, y: cy }
    setError()
    ballEntering.value = true
    setTimeout(() => { ballEntering.value = false }, 500)
  }
}

// Show ball entrance animation when success ball appears
watch(() => ballState.status, (val) => {
  if (val === 'success' && ballState.visible) {
    ballEntering.value = true
    setTimeout(() => { ballEntering.value = false }, 500)
  }
})
</script>

<style>
/* ── Floating ball ── */
.floating-ball-global {
  position: fixed;
  width: 72px; height: 72px;
  background: white;
  border-radius: 50%;
  box-shadow: 0 4px 24px rgba(0,0,0,0.18), 0 0 0 1px rgba(0,0,0,0.06);
  display: flex; align-items: center; justify-content: center;
  cursor: grab;
  z-index: 9000;
  user-select: none; -webkit-user-select: none;
}

.floating-ball-global:active { cursor: grabbing; }
.floating-ball-global:hover { box-shadow: 0 8px 32px rgba(0,0,0,0.22), 0 0 0 1px rgba(0,0,0,0.08); }
.floating-ball-global.success { border: 2px solid #10b981; }
.floating-ball-global.error { border: 2px solid #ef4444; }

/* Ball entrance animation */
.floating-ball-global.ball-enter {
  animation: ballBounceIn 0.5s cubic-bezier(0.34, 1.56, 0.64, 1);
}

@keyframes ballBounceIn {
  0%   { transform: scale(0.3); opacity: 0; }
  60%  { transform: scale(1.15); }
  100% { transform: scale(1); opacity: 1; }
}

/* Ball pop transition */
.ball-pop-enter-active { animation: ballBounceIn 0.45s cubic-bezier(0.34, 1.56, 0.64, 1); }
.ball-pop-leave-active { animation: ballPopOut 0.3s ease-in; }

@keyframes ballPopOut {
  0%   { transform: scale(1); opacity: 1; }
  100% { transform: scale(0.2); opacity: 0; }
}

.ball-inner-global {
  display: flex; flex-direction: column; align-items: center;
  gap: 2px; color: #374151; pointer-events: none;
}
.floating-ball-global.success .ball-inner-global { color: #10b981; }
.floating-ball-global.error .ball-inner-global { color: #ef4444; }
.ball-text { font-size: 10px; font-weight: 600; white-space: nowrap; }
.ball-spin { animation: spin 1s linear infinite; }

/* ── Expand overlay ── */
.expand-overlay {
  position: fixed; inset: 0;
  z-index: 9500;
  background: rgba(255,255,255,0.6);
  backdrop-filter: blur(8px);
  animation: fadeIn 0.3s ease;
}

.expand-ball {
  position: fixed;
  width: 72px; height: 72px;
  background: white;
  border: 2px solid #10b981;
  border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  z-index: 9501;
}

/* ── Modal ── */
.modal-global {
  display: none;
  position: fixed; inset: 0;
  z-index: 2000;
  align-items: center; justify-content: center;
}
.modal-global.active { display: flex; }

.modal-overlay {
  position: absolute; inset: 0;
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
  width: 640px; max-height: 85vh;
  background: white;
  border-radius: 16px;
  box-shadow: 0 25px 50px -12px rgba(0,0,0,0.25);
  display: flex; flex-direction: column;
  overflow: hidden;
}

.modal-header {
  display: flex; align-items: center; justify-content: space-between;
  padding: 24px 32px; border-bottom: 1px solid #e5e7eb;
}
.modal-title { font-size: 20px; font-weight: 600; color: #1f2937; }
.modal-close {
  width: 36px; height: 36px;
  display: flex; align-items: center; justify-content: center;
  border-radius: 6px; color: #6b7280;
  background: transparent; border: none; cursor: pointer;
}
.modal-close:hover { background: #f3f4f6; color: #374151; }
.modal-body { flex: 1; padding: 24px 32px; overflow-y: auto; }
.modal-footer {
  display: flex; justify-content: flex-end; gap: 12px;
  padding: 16px 32px; border-top: 1px solid #e5e7eb; background: #f9fafb;
}

.step-content { animation: fadeIn 0.3s ease; }
.form-step { margin-bottom: 24px; }
.form-label {
  display: flex; align-items: center; gap: 8px;
  font-size: 14px; font-weight: 600; color: #374151; margin-bottom: 12px;
}
.step-number {
  display: flex; align-items: center; justify-content: center;
  width: 24px; height: 24px; font-size: 12px; font-weight: 600;
  color: white; background: #6366f1; border-radius: 999px;
}
.char-count { text-align: right; font-size: 12px; color: #9ca3af; margin-top: 8px; }
.char-count.error { color: #ef4444; }

.textarea {
  min-height: 120px; padding: 12px 16px; resize: vertical;
  width: 100%; font-size: 14px; color: #374151;
  background: white; border: 1px solid #d1d5db; border-radius: 6px;
  outline: none; font-family: inherit;
}
.textarea:focus { border-color: #a5b4fc; box-shadow: 0 0 0 3px #e0e7ff; }

.input {
  width: 100%; height: 40px; padding: 0 16px;
  font-size: 14px; color: #374151; background: white;
  border: 1px solid #d1d5db; border-radius: 6px; outline: none;
}
.input:focus { border-color: #a5b4fc; box-shadow: 0 0 0 3px #e0e7ff; }
.input:disabled { background: #f3f4f6; color: #9ca3af; }

.rag-toggle-row {
  display: flex; align-items: center; justify-content: space-between;
  padding: 16px; background: #f9fafb; border: 1px solid #e5e7eb;
  border-radius: 8px; gap: 16px;
}
.rag-toggle-label { flex: 1; }
.rag-toggle-title { display: block; font-size: 14px; font-weight: 600; color: #1f2937; margin-bottom: 4px; }
.rag-toggle-desc { display: block; font-size: 12px; color: #6b7280; line-height: 1.4; }

.rag-toggle-switch {
  position: relative; width: 48px; height: 28px;
  background: #d1d5db; border: none; border-radius: 14px;
  cursor: pointer; transition: background 0.2s; flex-shrink: 0;
}
.rag-toggle-switch.active { background: #6366f1; }
.rag-toggle-knob {
  position: absolute; top: 3px; left: 3px;
  width: 22px; height: 22px; background: white;
  border-radius: 50%; transition: transform 0.2s;
  box-shadow: 0 1px 3px rgba(0,0,0,0.2);
}
.rag-toggle-switch.active .rag-toggle-knob { transform: translateX(20px); }

.animate-spin { animation: spin 1s linear infinite; }

@keyframes spin { to { transform: rotate(360deg) } }
@keyframes fadeIn { from { opacity: 0 } to { opacity: 1 } }

@media (max-width: 640px) {
  .modal-content { width: 100%; max-height: 100vh; border-radius: 0; }
  .floating-ball-global { width: 60px; height: 60px; }
}
</style>
