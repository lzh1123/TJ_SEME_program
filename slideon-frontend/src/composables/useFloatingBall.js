import { reactive } from 'vue'

const state = reactive({
  visible: false,
  status: 'generating',
  outlineId: null,
  position: { x: null, y: null },

  modalVisible: false,
  formTopic: '',
  formStyle: 'paper_light',
  useRag: true,
  inputMode: 'topic',
  selectedDocument: null,
  isGenerating: false
})

let dragState = null
let abortController = null

export function useFloatingBall() {
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

  function resetForm() {
    state.formTopic = ''
    state.inputMode = 'topic'
    state.selectedDocument = null
  }

  function showModal() {
    state.modalVisible = true
  }

  function hideModal() {
    state.modalVisible = false
    if (!state.isGenerating) {
      resetForm()
    }
  }

  function cancelGeneration() {
    if (abortController) {
      abortController.abort()
      abortController = null
    }
    state.isGenerating = false
    resetForm()
  }

  async function generateOutline(apiService, outlineStore) {
    if (state.inputMode === 'topic' && !state.formTopic.trim()) return false
    if (state.inputMode === 'document' && !state.selectedDocument) return false

    state.isGenerating = true

    try {
      const controller = new AbortController()
      abortController = controller
      const result = state.inputMode === 'topic'
        ? await apiService.generateOutline(
          state.formTopic,
          state.formStyle,
          state.useRag,
          controller.signal
        )
        : await apiService.generateOutlineFromDocument(
          state.selectedDocument,
          state.formStyle,
          controller.signal
        )

      const { id } = await outlineStore.createOutline(result)

      if (!state.modalVisible) {
        setSuccess(id)
      }

      state.isGenerating = false
      abortController = null
      resetForm()
      return { success: true, id }
    } catch (error) {
      state.isGenerating = false
      abortController = null
      resetForm()
      if (error.name === 'AbortError') {
        return { success: false, aborted: true }
      }
      if (!state.modalVisible) {
        setError()
      }
      return { success: false, error: error.message }
    }
  }

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
    onDragStart,
    resetForm
  }
}
