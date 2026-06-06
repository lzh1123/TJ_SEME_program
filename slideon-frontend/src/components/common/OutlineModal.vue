<template>
  <Teleport to="body">
    <div class="modal" :class="{ active: modelValue }" @click.self="close">
      <div class="modal-overlay" @click="close"></div>
      <div class="modal-content" :class="{ expanded: step === 'editor' }">
        <div class="modal-header">
          <h2 class="modal-title">
            <span v-if="step === 'input'">智能生成PPT</span>
            <span v-else>编辑大纲</span>
          </h2>
          <button class="modal-close" @click="close">
            <IconBase name="times" :size="20" />
          </button>
        </div>
        
        <div class="modal-body">
          <div v-if="step === 'input'" class="step-content">
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

            <div class="form-step">
              <label class="form-label">
                <span class="step-number">2</span>
                选择主题风格
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
                  role="switch"
                  :aria-checked="useRag"
                >
                  <span class="rag-toggle-knob"></span>
                </button>
              </div>
            </div>
          </div>

          <div v-else class="step-content outline-editor">
            <div class="outline-header">
              <div class="outline-stats">
                <div class="stat-item">
                  <IconBase name="thLarge" :size="14" />
                  <span>{{ outlineData.slides?.length || 0 }} 页</span>
                </div>
                <div class="stat-item">
                  <IconBase name="document" :size="14" />
                  <span>{{ outlineData.title || '未命名' }}</span>
                </div>
              </div>
              <div class="outline-actions">
                <button class="btn btn-secondary btn-sm" @click="goBack">
                  <IconBase name="arrowLeft" :size="14" />
                  返回
                </button>
                <button class="btn btn-outline btn-sm" @click="regenerateOutline">
                  <IconBase name="refresh" :size="14" />
                  重新生成
                </button>
              </div>
            </div>

            <div class="outline-tree-container">
              <div class="outline-tree">
                <div 
                  v-for="(slide, index) in outlineData.slides" 
                  :key="slide.id || index"
                  class="outline-item"
                  :class="{ expanded: slide._expanded !== false }"
                >
                  <div class="outline-item-header">
                    <button class="toggle-btn" @click="toggleExpand(slide)">
                      <IconBase name="chevronRight" :size="14" />
                    </button>
                    <div class="item-number">{{ index + 1 }}</div>
                    <input 
                      v-if="slide._editing"
                      v-model="slide.title"
                      class="item-input"
                      @blur="slide._editing = false"
                      @keyup.enter="slide._editing = false"
                      ref="inputRef"
                    />
                    <span v-else class="item-title" @click="editSlideTitle(slide)">
                      {{ slide.title }}
                    </span>
                    <div class="item-actions">
                      <button class="action-btn" @click="editSlideTitle(slide)" title="编辑">
                        <IconBase name="edit" :size="14" />
                      </button>
                      <button class="action-btn" @click="duplicateSlide(slide, index)" title="复制">
                        <IconBase name="copy" :size="14" />
                      </button>
                      <button class="action-btn" @click="moveSlideUp(index)" :disabled="index === 0" title="上移">
                        <IconBase name="chevronUp" :size="14" />
                      </button>
                      <button class="action-btn" @click="moveSlideDown(index)" :disabled="index === outlineData.slides.length - 1" title="下移">
                        <IconBase name="chevronDown" :size="14" />
                      </button>
                      <button class="action-btn danger" @click="deleteSlide(index)" title="删除">
                        <IconBase name="trash" :size="14" />
                      </button>
                    </div>
                  </div>
                  <div class="outline-children" v-if="slide._expanded !== false">
                    <div class="outline-child-item">
                      <span class="child-number">{{ index + 1 }}.1</span>
                      <span class="child-title">类型：{{ getSlideType(slide.intent) }}</span>
                    </div>
                    
                    <div class="outline-child-list" v-if="showBullets(slide)">
                      <div class="list-header">
                        <span>要点</span>
                        <button class="add-child-btn" @click="addBullet(slide)">
                          <IconBase name="plus" :size="12" />
                        </button>
                      </div>
                      <div v-if="slide.bullets && slide.bullets.length > 0" v-for="(bullet, i) in slide.bullets" :key="`bullet-${i}`" class="outline-child-item editable">
                        <span class="child-number">{{ index + 1 }}.{{ i + 2 }}</span>
                        <input 
                          v-if="bullet._editing"
                          v-model="bullet.text"
                          class="child-input"
                          @blur="bullet._editing = false"
                          @keyup.enter="bullet._editing = false"
                        />
                        <span v-else class="child-title child-bullet" @click="editChild(bullet)">• {{ bullet.text || bullet }}</span>
                        <div class="child-actions">
                          <button class="action-btn" @click="editChild(bullet)" title="编辑">
                            <IconBase name="edit" :size="12" />
                          </button>
                          <button class="action-btn danger" @click="removeBullet(slide, i)" title="删除">
                            <IconBase name="trash" :size="12" />
                          </button>
                        </div>
                      </div>
                      <div v-else class="outline-child-item empty">
                        <span class="child-title">暂无要点</span>
                      </div>
                    </div>
                    
                    <div class="outline-child-list" v-if="showParagraphs(slide)">
                      <div class="list-header">
                        <span>段落</span>
                        <button class="add-child-btn" @click="addParagraph(slide)">
                          <IconBase name="plus" :size="12" />
                        </button>
                      </div>
                      <div v-if="slide.paragraphs && slide.paragraphs.length > 0" v-for="(para, i) in slide.paragraphs" :key="`para-${i}`" class="outline-child-item editable">
                        <span class="child-number">{{ index + 1 }}.{{ i + (slide.bullets ? slide.bullets.length : 0) + 2 }}</span>
                        <textarea 
                          v-if="para._editing"
                          v-model="para.text"
                          class="child-textarea"
                          @blur="para._editing = false"
                        ></textarea>
                        <span v-else class="child-title child-paragraph" @click="editChild(para)">{{ (para.text || para).substring(0, 50) }}{{ (para.text || para).length > 50 ? '...' : '' }}</span>
                        <div class="child-actions">
                          <button class="action-btn" @click="editChild(para)" title="编辑">
                            <IconBase name="edit" :size="12" />
                          </button>
                          <button class="action-btn danger" @click="removeParagraph(slide, i)" title="删除">
                            <IconBase name="trash" :size="12" />
                          </button>
                        </div>
                      </div>
                      <div v-else class="outline-child-item empty">
                        <span class="child-title">暂无段落</span>
                      </div>
                    </div>
                    
                    <div class="outline-child-list" v-if="showItems(slide)">
                      <div class="list-header">
                        <span>项目</span>
                        <button class="add-child-btn" @click="addItem(slide)">
                          <IconBase name="plus" :size="12" />
                        </button>
                      </div>
                      <div v-if="slide.items && slide.items.length > 0" v-for="(item, i) in slide.items" :key="`item-${i}`" class="outline-child-item editable">
                        <span class="child-number">{{ index + 1 }}.{{ i + 2 }}</span>
                        <input 
                          v-if="item._editing"
                          v-model="item.text"
                          class="child-input"
                          @blur="item._editing = false"
                          @keyup.enter="item._editing = false"
                        />
                        <span v-else class="child-title child-item" @click="editChild(item)">- {{ item.text || item }}</span>
                        <div class="child-actions">
                          <button class="action-btn" @click="editChild(item)" title="编辑">
                            <IconBase name="edit" :size="12" />
                          </button>
                          <button class="action-btn danger" @click="removeItem(slide, i)" title="删除">
                            <IconBase name="trash" :size="12" />
                          </button>
                        </div>
                      </div>
                      <div v-else class="outline-child-item empty">
                        <span class="child-title">暂无项目</span>
                      </div>
                    </div>
                    
                    <div class="outline-child-list" v-if="slide.notes && slide.notes.length > 0">
                      <div class="list-header">
                        <span>备注</span>
                      </div>
                      <div v-for="(note, i) in slide.notes" :key="`note-${i}`" class="outline-child-item">
                        <span class="child-number">{{ index + 1 }}.{{ i + (slide.bullets ? slide.bullets.length : 0) + (slide.paragraphs ? slide.paragraphs.length : 0) + (slide.items ? slide.items.length : 0) + 2 }}</span>
                        <span class="child-title child-note">📝 {{ (note.text || note).substring(0, 40) }}{{ (note.text || note).length > 40 ? '...' : '' }}</span>
                      </div>
                    </div>
                  </div>
                </div>

                <button class="add-section-btn" @click="addNewSlide">
                  <IconBase name="plus" :size="16" />
                  添加新页面
                </button>
              </div>
            </div>
          </div>
        </div>

        <div class="modal-footer">
          <button class="btn btn-secondary" @click="close">取消</button>
          <button 
            v-if="step === 'input'"
            class="btn btn-primary" 
            :disabled="isGenerating || !form.topic.trim()"
            @click="generateOutline"
          >
            <IconBase v-if="isGenerating" name="spinner" :size="14" class="animate-spin" />
            <IconBase v-else name="magic" :size="14" />
            {{ isGenerating ? '生成大纲中...' : '生成大纲' }}
          </button>
          <button 
            v-else
            class="btn btn-primary" 
            :disabled="isGenerating"
            @click="generatePresentation"
          >
            <IconBase v-if="isGenerating" name="spinner" :size="14" class="animate-spin" />
            <IconBase v-else name="check" :size="14" />
            {{ isGenerating ? '生成中...' : '生成PPT' }}
          </button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { ref, computed, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import IconBase from '../icons/IconBase.vue'
import { apiService } from '../../services/api.js'
import { new_id } from '../../utils/ids.js'

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['update:modelValue'])

const router = useRouter()

const step = ref('input')
const isGenerating = ref(false)
const presentationId = ref('')

const form = ref({
  topic: '',
  style: 'modern_blue'
})

const useRag = ref(true)

const outlineData = ref({
  title: '',
  theme: 'modern_blue',
  slides: []
})

const charCount = computed(() => form.value.topic.length)

const styleOptions = [
  { value: 'modern_blue', name: '现代蓝', icon: '💼' },
  { value: 'paper_light', name: '纸张白', icon: '📄' },
  { value: 'academic_gray', name: '学术灰', icon: '📖' },
  { value: 'minimal_black', name: '简约黑', icon: '🎨' }
]

const close = () => {
  emit('update:modelValue', false)
  step.value = 'input'
  form.value.topic = ''
  outlineData.value = { title: '', theme: 'modern_blue', slides: [] }
}

const updateCharCount = () => {
  if (charCount.value > 500) {
    form.value.topic = form.value.topic.slice(0, 500)
  }
}

const prepareChildForEdit = (child) => {
  if (typeof child === 'string') {
    return { text: child, _editing: false }
  }
  return { ...child, _editing: false }
}

const prepareSlideForEdit = (slide) => {
  const prepared = {
    ...slide,
    _expanded: true,
    _editing: false
  }
  
  if (slide.intent === 'text') {
    if (slide.bullets) prepared.bullets = slide.bullets.map(prepareChildForEdit)
    if (slide.paragraphs) prepared.paragraphs = slide.paragraphs.map(prepareChildForEdit)
  }
  
  if (slide.intent === 'agenda' || slide.intent === 'kpi') {
    if (slide.items) prepared.items = slide.items.map(prepareChildForEdit)
  }
  
  if (slide.notes) prepared.notes = slide.notes.map(prepareChildForEdit)
  
  return prepared
}

const generateOutline = async () => {
  if (!form.value.topic.trim()) {
    alert('请输入主题')
    return
  }

  isGenerating.value = true
  
  try {
    const result = await apiService.generateOutline(form.value.topic, form.value.style, useRag.value)
    
    console.log('✅ 生成大纲成功:', result)
    
    outlineData.value = {
      title: result.title || form.value.topic,
      theme: result.theme || form.value.style,
      slides: (result.slides || []).map(prepareSlideForEdit)
    }
    
    step.value = 'editor'
  } catch (error) {
    console.error('❌ 生成大纲失败:', error)
    alert('生成大纲失败: ' + error.message)
  } finally {
    isGenerating.value = false
  }
}

const goBack = () => {
  step.value = 'input'
}

const regenerateOutline = () => {
  generateOutline()
}

const toggleExpand = (slide) => {
  slide._expanded = !slide._expanded
}

const editSlideTitle = (slide) => {
  slide._editing = true
  nextTick(() => {
    const input = document.querySelector('.item-input:focus')
    if (input) input.focus()
  })
}

const duplicateSlide = (slide, index) => {
  const newSlide = {
    ...slide,
    id: new_id('slide'),
    title: slide.title + ' (副本)',
    _expanded: true,
    _editing: false
  }
  outlineData.value.slides.splice(index + 1, 0, newSlide)
}

const moveSlideUp = (index) => {
  if (index === 0) return
  const slide = outlineData.value.slides[index]
  outlineData.value.slides.splice(index, 1)
  outlineData.value.slides.splice(index - 1, 0, slide)
}

const moveSlideDown = (index) => {
  if (index === outlineData.value.slides.length - 1) return
  const slide = outlineData.value.slides[index]
  outlineData.value.slides.splice(index, 1)
  outlineData.value.slides.splice(index + 1, 0, slide)
}

const deleteSlide = (index) => {
  if (outlineData.value.slides.length <= 1) {
    alert('至少需要保留一页')
    return
  }
  outlineData.value.slides.splice(index, 1)
}

const addNewSlide = () => {
  const newSlide = {
    id: new_id('slide'),
    title: '新页面',
    intent: 'text',
    bullets: [],
    paragraphs: [],
    notes: [],
    _expanded: true,
    _editing: true
  }
  outlineData.value.slides.push(newSlide)
}

const getSlideType = (intent) => {
  const typeMap = {
    'cover': '标题页',
    'agenda': '议程页',
    'text': '内容页',
    'chart': '图表页',
    'quote': '引用页',
    'kpi': 'KPI页',
    'divider': '分隔页',
    'architecture': '架构页',
    'timeline': '时间线',
    'comparison': '对比页',
    'swot': 'SWOT分析',
    'roadmap': '路线图',
    'process_flow': '流程图',
    'multi_column': '多列页',
    'team': '团队页'
  }
  return typeMap[intent] || '内容页'
}

const showBullets = (slide) => {
  return slide.intent === 'text'
}

const showParagraphs = (slide) => {
  return slide.intent === 'text'
}

const showItems = (slide) => {
  return slide.intent === 'agenda' || slide.intent === 'kpi'
}

const allowedFieldsByIntent = {
  'cover': ['id', 'intent', 'section', 'title', 'notes', 'subtitle', 'tagline', 'highlights'],
  'agenda': ['id', 'intent', 'section', 'title', 'notes', 'items'],
  'text': ['id', 'intent', 'section', 'title', 'notes', 'paragraphs', 'bullets'],
  'timeline': ['id', 'intent', 'section', 'title', 'notes', 'events'],
  'kpi': ['id', 'intent', 'section', 'title', 'notes', 'items'],
  'comparison': ['id', 'intent', 'section', 'title', 'notes', 'left', 'right'],
  'swot': ['id', 'intent', 'section', 'title', 'notes', 'swot'],
  'roadmap': ['id', 'intent', 'section', 'title', 'notes', 'phases'],
  'process_flow': ['id', 'intent', 'section', 'title', 'notes', 'steps'],
  'chart': ['id', 'intent', 'section', 'title', 'notes', 'chart'],
  'multi_column': ['id', 'intent', 'section', 'title', 'notes', 'columns'],
  'architecture': ['id', 'intent', 'section', 'title', 'notes', 'layers'],
  'quote': ['id', 'intent', 'section', 'title', 'notes', 'quote', 'author'],
  'divider': ['id', 'intent', 'section', 'title', 'notes', 'subtitle'],
  'team': ['id', 'intent', 'section', 'title', 'notes', 'members']
}

const cleanSlideByIntent = (slide) => {
  const allowed = allowedFieldsByIntent[slide.intent] || allowedFieldsByIntent['text']
  const cleaned = {}
  
  allowed.forEach(field => {
    if (slide[field] !== undefined) {
      if (field === 'bullets' || field === 'paragraphs' || field === 'items' || field === 'notes') {
        cleaned[field] = slide[field].map(prepareChildForBackend)
      } else {
        cleaned[field] = slide[field]
      }
    }
  })
  
  return cleaned
}

const editChild = (child) => {
  child._editing = true
  nextTick(() => {
    const input = document.querySelector('.child-input:focus, .child-textarea:focus')
    if (input) input.focus()
  })
}

const addBullet = (slide) => {
  if (!slide.bullets) slide.bullets = []
  slide.bullets.push({ text: '新要点', _editing: true })
}

const removeBullet = (slide, index) => {
  slide.bullets.splice(index, 1)
}

const addParagraph = (slide) => {
  if (!slide.paragraphs) slide.paragraphs = []
  slide.paragraphs.push({ text: '新段落', _editing: true })
}

const removeParagraph = (slide, index) => {
  slide.paragraphs.splice(index, 1)
}

const addItem = (slide) => {
  if (!slide.items) slide.items = []
  slide.items.push({ text: '新项目', _editing: true })
}

const removeItem = (slide, index) => {
  slide.items.splice(index, 1)
}

const prepareChildForBackend = (child) => {
  if (typeof child === 'string') return child
  return child.text || ''
}

const generatePresentation = async () => {
  isGenerating.value = true
  
  try {
    const outline = {
      ...outlineData.value,
      slides: outlineData.value.slides.map(cleanSlideByIntent)
    }
    
    const renderTree = await apiService.compileOutline(form.value.topic, outline, form.value.style)
    
    console.log('✅ 生成渲染树成功:', renderTree)
    
    close()
    
    const id = new_id('pres')
    const meta = {
      id,
      topic: form.value.topic,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
      version: 1
    }
    
    const bundle = {
      meta,
      dsl: outline,
      renderTree
    }
    
    window.__presentationBundle = bundle
    
    router.push({
      path: '/editor',
      query: { id }
    })
  } catch (error) {
    console.error('❌ 生成PPT失败:', error)
    alert('生成PPT失败: ' + error.message)
  } finally {
    isGenerating.value = false
  }
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

.action-btn:disabled {
  opacity: 0.3;
  cursor: not-allowed;
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

.child-bullet {
  color: var(--gray-700);
}

.child-paragraph {
  color: var(--gray-600);
  font-style: italic;
}

.child-item {
  color: var(--primary-700);
}

.child-note {
  color: var(--success-700);
  font-size: 13px;
}

.outline-child-list {
  margin-bottom: var(--space-3);
}

.list-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--space-2) var(--space-4);
  padding-left: calc(var(--space-4) + 48px);
  font-size: 12px;
  font-weight: 600;
  color: var(--gray-500);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.add-child-btn {
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
  background: transparent;
  cursor: pointer;
  color: var(--primary-500);
  border-radius: var(--radius-sm);
  transition: all 0.2s ease;
}

.add-child-btn:hover {
  background: var(--primary-100);
}

.outline-child-item.editable {
  cursor: pointer;
}

.outline-child-item.editable:hover {
  background: var(--gray-100);
}

.outline-child-item.empty {
  color: var(--gray-400);
  font-style: italic;
}

.child-input {
  flex: 1;
  padding: var(--space-1) var(--space-2);
  border: 1px solid var(--primary-300);
  border-radius: var(--radius-sm);
  font-size: 14px;
  outline: none;
  background: white;
}

.child-input:focus {
  border-color: var(--primary-500);
  box-shadow: 0 0 0 3px var(--primary-100);
}

.child-textarea {
  flex: 1;
  padding: var(--space-2);
  border: 1px solid var(--primary-300);
  border-radius: var(--radius-sm);
  font-size: 14px;
  outline: none;
  background: white;
  resize: vertical;
  min-height: 60px;
  font-family: inherit;
}

.child-textarea:focus {
  border-color: var(--primary-500);
  box-shadow: 0 0 0 3px var(--primary-100);
}

.child-actions {
  display: flex;
  gap: var(--space-1);
  opacity: 0;
  transition: opacity 0.2s ease;
}

.outline-child-item.editable:hover .child-actions {
  opacity: 1;
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
