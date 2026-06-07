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

  <!-- 全局大纲生成弹窗 (uses OutlineModal component with doc upload) -->
  <OutlineModal v-model="state.modalVisible" />

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
import IconBase from './components/icons/IconBase.vue'
import OutlineModal from './components/common/OutlineModal.vue'

const router = useRouter()
const { state, showBall, hideBall, showModal, hideModal, onDragStart } = useFloatingBall()

const ballState = state
const ballEntering = ref(false)
const ballExpanding = ref(false)

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

@media (max-width: 640px) {
  .floating-ball-global { width: 60px; height: 60px; }
}
</style>
