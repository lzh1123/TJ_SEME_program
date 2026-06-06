import { reactive, ref } from 'vue'

// Module-level reactive state — persists across page navigation
const state = reactive({
  // Floating ball
  visible: false,
  status: 'generating',  // 'generating' | 'success' | 'error'
  outlineId: null,
  position: { x: null, y: null },

  // Modal
  modalVisible: false,
  formTopic: '',
  formStyle: 'paper_light',
  useRag: true,
  isGenerating: false
})

let dragState = null
let abortController = null

export function useFloatingBall() {
  // ── Floating ball ──
  function showBall(status = 'generating', outlineId = null) {
    state.visible = true
    state.status = status
    state.outlineId = outlineId
    if (state.position.x == null) {
      state.position = { x: window.innerWidth - 104, y: window.innerHeight - 104 }
    }
  }

  function hideBall() {
    state.visible = false
    state.status = 'generating'
    state.outlineId = null
    state.position = { x: null, y: null }
  }

  function setSuccess(outlineId) {
    state.status = 'success'
    state.outlineId = outlineId
  }

  function setError() {
    state.status = 'error'
  }

  // ── Modal ──
  function showModal() {
    state.modalVisible = true
  }

  function hideModal() {
    state.modalVisible = false
    state.formTopic = ''
  }

  function cancelGeneration() {
    if (abortController) {
      abortController.abort()
      abortController = null
    }
    state.isGenerating = false
  }

  // ── Outline generation ──
  async function generateOutline(apiService, outlineStore) {
    if (!state.formTopic.trim()) return false

    state.isGenerating = true

    try {
      const controller = new AbortController()
      abortController = controller
      const result = await apiService.generateOutline(
        state.formTopic,
        state.formStyle,
        state.useRag,
        controller.signal
      )

      const { id } = outlineStore.createOutline(result)

      if (!state.modalVisible) {
        // Modal was minimized → update ball to success
        setSuccess(id)
      } else {
        // Still in modal → success handled by caller
      }

      state.isGenerating = false
      abortController = null
      return { success: true, id }
    } catch (error) {
      if (error.name === 'AbortError') {
        state.isGenerating = false
        abortController = null
        return { success: false, aborted: true }
      }
      if (!state.modalVisible) {
        setError()
      }
      state.isGenerating = false
      abortController = null
      return { success: false, error: error.message }
    }
  }

  // ── Drag ──
  function onDragStart(e) {
    const touch = e.touches ? e.touches[0] : e
    dragState = {
      startX: touch.clientX - state.position.x,
      startY: touch.clientY - state.position.y
    }

    const onMove = (ev) => {
      if (!dragState) return
      ev.preventDefault()
      const t = ev.touches ? ev.touches[0] : ev
      state.position.x = Math.max(0, Math.min(window.innerWidth - 72, t.clientX - dragState.startX))
      state.position.y = Math.max(0, Math.min(window.innerHeight - 72, t.clientY - dragState.startY))
    }

    const onEnd = () => {
      dragState = null
      document.removeEventListener('mousemove', onMove)
      document.removeEventListener('mouseup', onEnd)
      document.removeEventListener('touchmove', onMove)
      document.removeEventListener('touchend', onEnd)
    }

    document.addEventListener('mousemove', onMove)
    document.addEventListener('mouseup', onEnd)
    document.addEventListener('touchmove', onMove, { passive: false })
    document.addEventListener('touchend', onEnd)
  }

  return {
    state,
    showBall,
    hideBall,
    setSuccess,
    setError,
    showModal,
    hideModal,
    cancelGeneration,
    generateOutline,
    onDragStart
  }
}
