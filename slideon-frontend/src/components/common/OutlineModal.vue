<template>
  <Teleport to="body">
    <!-- 模态框 -->
    <div v-if="modelValue" class="modal active" @click.self="minimize">
      <div class="modal-overlay" @click="minimize"></div>
      <div class="modal-content">
        <div class="modal-header">
          <h2 class="modal-title">智能生成大纲</h2>
          <button class="modal-close" @click="minimize">
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
                v-model="form.topic"
                :disabled="isGenerating"
                @input="updateCharCount"
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
                  :class="['rag-toggle-switch', { active: useRag }]"
                  @click="useRag = !useRag"
                  :disabled="isGenerating"
                  role="switch"
                  :aria-checked="useRag"
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
            :disabled="isGenerating || !form.topic.trim()"
            @click="generateOutline"
          >
            <IconBase v-if="isGenerating" name="spinner" :size="14" class="animate-spin" />
            <IconBase v-else name="magic" :size="14" />
            {{ isGenerating ? '生成大纲中...' : '生成大纲' }}
          </button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import IconBase from '../icons/IconBase.vue'
import { apiService } from '../../services/api.js'
import { useOutlineStore } from '../../stores/outlineStore.js'
import { useFloatingBall } from '../../composables/useFloatingBall.js'

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['update:modelValue'])

const outlineStore = useOutlineStore()
const { state: ballState, show: showBall, setSuccess, setError, consumeReopen } = useFloatingBall()

const isGenerating = ref(false)
let abortController = null

// Watch for reopen request (user clicked ball during generation)
watch(() => ballState.reopenRequested, (val) => {
  if (val) {
    consumeReopen()
    emit('update:modelValue', true)
  }
})

const form = ref({
  topic: '',
  style: 'paper_light'
})

const useRag = ref(true)
const charCount = computed(() => form.value.topic.length)

const close = () => {
  emit('update:modelValue', false)
  form.value.topic = ''
}

const updateCharCount = () => {
  if (charCount.value > 500) {
    form.value.topic = form.value.topic.slice(0, 500)
  }
}

const minimize = () => {
  if (isGenerating.value) {
    // Show floating ball and close modal
    showBall('generating')
    emit('update:modelValue', false)
  } else {
    close()
  }
}

const handleCancel = () => {
  if (isGenerating.value) {
    if (abortController) {
      abortController.abort()
      abortController = null
    }
    isGenerating.value = false
  } else {
    close()
  }
}

const generateOutline = async () => {
  if (!form.value.topic.trim()) {
    alert('请输入主题')
    return
  }

  isGenerating.value = true

  try {
    abortController = new AbortController()
    const result = await apiService.generateOutline(
      form.value.topic,
      form.value.style,
      useRag.value,
      abortController.signal
    )

    console.log('✅ 生成大纲成功:', result)

    const { id } = outlineStore.createOutline(result)

    // Check if modal was closed (minimized to ball) during generation
    if (!props.modelValue) {
      // Ball is visible, update to success
      setSuccess(id)
    } else {
      // Still in modal, close and navigate
      close()
      router.push({ path: '/outline-editor', query: { id } })
    }
  } catch (error) {
    if (error.name === 'AbortError') {
      console.log('⚠️ 生成已取消')
      return
    }
    console.error('❌ 生成大纲失败:', error)
    if (!props.modelValue) {
      setError()
    } else {
      alert('生成大纲失败: ' + error.message)
    }
  } finally {
    isGenerating.value = false
    abortController = null
  }
}

// Need router for navigation on success when modal is still open
import { useRouter } from 'vue-router'
const router = useRouter()
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

.form-label {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  font-size: 14px;
  font-weight: 600;
  color: var(--gray-700);
  margin-bottom: var(--space-3);
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

.rag-toggle-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--space-4);
  background: var(--gray-50);
  border: 1px solid var(--gray-200);
  border-radius: var(--radius-lg);
  gap: var(--space-4);
}

.rag-toggle-label {
  flex: 1;
}

.rag-toggle-title {
  display: block;
  font-size: 14px;
  font-weight: 600;
  color: var(--gray-800);
  margin-bottom: var(--space-1);
}

.rag-toggle-desc {
  display: block;
  font-size: 12px;
  color: var(--gray-500);
  line-height: 1.4;
}

.rag-toggle-switch {
  position: relative;
  width: 48px;
  height: 28px;
  background: var(--gray-300);
  border: none;
  border-radius: 14px;
  cursor: pointer;
  transition: background 0.2s ease;
  flex-shrink: 0;
}

.rag-toggle-switch.active {
  background: var(--primary-500);
}

.rag-toggle-knob {
  position: absolute;
  top: 3px;
  left: 3px;
  width: 22px;
  height: 22px;
  background: white;
  border-radius: 50%;
  transition: transform 0.2s ease;
  box-shadow: 0 1px 3px rgba(0,0,0,0.2);
}

.rag-toggle-switch.active .rag-toggle-knob {
  transform: translateX(20px);
}

@keyframes slideUp {
  from { opacity: 0; transform: translateY(20px); }
  to { opacity: 1; transform: translateY(0); }
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

@media (max-width: 640px) {
  .modal-content {
    width: 100%;
    max-height: 100vh;
    border-radius: 0;
  }
}
</style>
