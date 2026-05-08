<template>
  <div class="editor-page">
    <!-- 顶部工具栏 -->
    <header class="editor-header">
      <div class="header-left">
        <router-link to="/" class="btn btn-ghost btn-icon">
          <IconBase name="arrowLeft" :size="18" />
        </router-link>
        <div class="project-info">
          <input 
            type="text" 
            class="project-title-input" 
            v-model="projectTitle"
            placeholder="输入PPT标题"
            @blur="saveTitle"
            @keypress.enter="$event.target.blur()"
          >
          <span class="project-status" :class="{ saved: isSaved }">
            <IconBase v-if="isSaved" name="check" :size="10" />
            <IconBase v-else name="sync" :size="10" class="animate-spin" />
            {{ isSaved ? '已保存' : '保存中...' }}
          </span>
        </div>
      </div>
      <div class="header-right">
        <button class="btn btn-secondary btn-sm" @click="saveProject">
          <IconBase name="save" :size="14" />
          保存
        </button>
        <button class="btn btn-secondary btn-sm" @click="shareProject">
          <IconBase name="share" :size="14" />
          分享
        </button>
        <div class="dropdown">
          <button class="btn btn-primary btn-sm" @click="exportPresentation">
            <IconBase name="download" :size="14" />
            导出
          </button>
        </div>
        <div class="user-avatar">
          <img :src="userAvatar" alt="用户头像">
        </div>
      </div>
    </header>

    <!-- 编辑器主体 -->
    <div class="editor-container">
      <!-- 左侧边栏 - 大纲 -->
      <aside class="editor-sidebar">
        <div class="sidebar-tabs">
          <button 
            :class="['sidebar-tab', { active: activeTab === 'outline' }]"
            @click="activeTab = 'outline'"
          >
            <IconBase name="list" :size="14" />
            大纲
          </button>
          <button 
            :class="['sidebar-tab', { active: activeTab === 'slides' }]"
            @click="activeTab = 'slides'"
          >
            <IconBase name="images" :size="14" />
            页面
          </button>
        </div>
        
        <!-- 大纲视图 -->
        <div v-show="activeTab === 'outline'" class="sidebar-content">
          <div class="outline-tree">
            <div 
              v-for="(item, index) in outlineItems" 
              :key="index"
              :class="['outline-item', { expanded: item.expanded }]"
            >
              <div class="outline-header" @click="toggleOutlineItem(index)">
                <IconBase 
                  :name="item.expanded ? 'chevronDown' : 'chevronRight'" 
                  :size="10" 
                  class="toggle-icon"
                />
                <span class="outline-number">{{ item.number }}</span>
                <span class="outline-title">{{ item.title }}</span>
              </div>
              <div v-if="item.expanded && item.children" class="outline-children">
                <div 
                  v-for="(child, childIndex) in item.children" 
                  :key="childIndex"
                  :class="['outline-item-page', { active: currentPage === child.pageNumber }]"
                  @click="selectPage(child.pageNumber)"
                >
                  <span class="page-number">{{ child.pageNumber }}</span>
                  <span class="page-title">{{ child.title }}</span>
                </div>
              </div>
            </div>
          </div>
          
          <button class="add-page-btn" @click="addPage">
            <IconBase name="plus" :size="14" />
            添加页面
          </button>
        </div>
        
        <!-- 页面缩略图视图 -->
        <div v-show="activeTab === 'slides'" class="sidebar-content">
          <div class="slides-grid">
            <div 
              v-for="slide in slides" 
              :key="slide.number"
              :class="['slide-thumb', { active: currentPage === slide.number }]"
              @click="selectPage(slide.number)"
            >
              <div class="slide-thumb-preview" :style="{ background: slide.background }">
                <span class="slide-number">{{ slide.number }}</span>
              </div>
              <span class="slide-thumb-title">{{ slide.title }}</span>
            </div>
          </div>
        </div>
      </aside>

      <!-- 中间画布区域 -->
      <main class="editor-canvas-area">
        <div class="canvas-wrapper">
          <div class="slide-canvas" :style="getCanvasStyle()">
            <div class="slide-content" v-if="currentSlide.components">
              <div 
                v-for="component in currentSlide.components" 
                :key="component.id"
                class="slide-component"
                :style="getComponentStyle(component)"
              >
                <!-- 标题组件 -->
                <div v-if="component.type === 'Title'" class="component-title">
                  {{ component.props?.text || '' }}
                </div>
                <!-- 副标题组件 -->
                <div v-else-if="component.type === 'Subtitle'" class="component-subtitle">
                  {{ component.props?.text || '' }}
                </div>
                <!-- 文本组件 -->
                <div v-else-if="component.type === 'Text'" class="component-text">
                  {{ component.props?.text || '' }}
                </div>
                <!-- 项目符号列表 -->
                <div v-else-if="component.type === 'BulletList'" class="component-bullet-list">
                  <ul>
                    <li v-for="(item, idx) in component.props?.items || []" :key="idx">{{ item }}</li>
                  </ul>
                </div>
                <!-- 引用组件 -->
                <div v-else-if="component.type === 'Quote'" class="component-quote">
                  <blockquote>{{ component.props?.text || '' }}</blockquote>
                </div>
                <!-- 分隔线 -->
                <div v-else-if="component.type === 'Divider'" class="component-divider">
                  <hr />
                </div>
                <!-- 图片组件 -->
                <div v-else-if="component.type === 'Image'" class="component-image">
                  <img v-if="component.props?.url" :src="component.props.url" :alt="component.props?.alt || ''" />
                  <div v-else style="display:flex;align-items:center;justify-content:center;height:100%;color:#888;">[图片]</div>
                </div>
                <!-- 其他组件 - 显示类型 -->
                <div v-else class="component-other">
                  [{{ component.type }}]
                </div>
              </div>
            </div>
            <!-- 默认渲染 -->
            <div v-else class="slide-content">
              <div class="slide-layout-title">
                <h1 class="slide-title">{{ currentSlide.title }}</h1>
                <p class="slide-subtitle">{{ currentSlide.subtitle }}</p>
                <div class="slide-date">{{ currentSlide.date }}</div>
              </div>
            </div>
          </div>
        </div>
        
        <!-- 画布工具栏 -->
        <div class="canvas-toolbar">
          <div class="toolbar-group">
            <button class="toolbar-btn" title="撤销" @click="undo">
              <IconBase name="undo" :size="16" />
            </button>
            <button class="toolbar-btn" title="重做" @click="redo">
              <IconBase name="redo" :size="16" />
            </button>
          </div>
          <div class="toolbar-divider"></div>
          <div class="toolbar-group">
            <button class="toolbar-btn" title="插入" @click="showToast('打开插入菜单')">
              <IconBase name="plus" :size="16" />
              <IconBase name="chevronDown" :size="10" />
            </button>
            <button class="toolbar-btn" title="布局" @click="showToast('打开布局菜单')">
              <IconBase name="thLarge" :size="16" />
              <IconBase name="chevronDown" :size="10" />
            </button>
            <button class="toolbar-btn" title="主题" @click="showToast('打开主题菜单')">
              <IconBase name="palette" :size="16" />
              <IconBase name="chevronDown" :size="10" />
            </button>
          </div>
          <div class="toolbar-divider"></div>
          <div class="toolbar-group">
            <button class="toolbar-btn" title="缩小" @click="zoomOut">
              <IconBase name="minus" :size="16" />
            </button>
            <span class="zoom-level">{{ zoom }}%</span>
            <button class="toolbar-btn" title="放大" @click="zoomIn">
              <IconBase name="plus" :size="16" />
            </button>
          </div>
          <div class="toolbar-divider"></div>
          <div class="toolbar-group">
            <span class="page-indicator">{{ currentPage }} / {{ totalPages }}</span>
            <button class="toolbar-btn" title="播放" @click="playPresentation">
              <IconBase name="play" :size="16" />
            </button>
          </div>
        </div>
      </main>

      <!-- 右侧AI助手面板 -->
      <aside class="editor-ai-panel">
        <div class="ai-panel-header">
          <div class="ai-avatar">
            <IconBase name="robot" :size="20" />
          </div>
          <div class="ai-info">
            <h3 class="ai-name">AI助手</h3>
            <span class="ai-status">
              <span class="status-dot"></span>
              在线
            </span>
          </div>
          <button class="btn btn-ghost btn-icon" title="设置" @click="showToast('打开设置')">
            <IconBase name="cog" :size="16" />
          </button>
        </div>
        
        <div class="ai-chat-container">
          <div class="ai-welcome">
            <div class="ai-message">
              <div class="ai-avatar-small">
                <IconBase name="robot" :size="14" />
              </div>
              <div class="message-content">
                <p>你好！我是你的AI助手，可以帮你：</p>
                <ul>
                  <li>优化幻灯片内容</li>
                  <li>生成配图建议</li>
                  <li>调整页面风格</li>
                  <li>补充数据案例</li>
                </ul>
              </div>
            </div>
          </div>
          
          <div class="chat-messages">
            <div 
              v-for="(msg, index) in chatMessages" 
              :key="index"
              :class="['message', msg.type]"
            >
              <div v-if="msg.type === 'ai'" class="ai-avatar-small">
                <IconBase name="robot" :size="14" />
              </div>
              <div class="message-content">
                <p>{{ msg.content }}</p>
              </div>
            </div>
          </div>
        </div>
        
        <div class="ai-quick-actions">
          <span class="quick-actions-label">快捷操作：</span>
          <div class="quick-actions-list">
            <button 
              v-for="action in quickActions" 
              :key="action.text"
              class="quick-action-btn"
              @click="sendQuickMessage(action.text)"
            >
              <IconBase :name="action.icon" :size="11" />
              {{ action.text }}
            </button>
          </div>
        </div>
        
        <div class="ai-input-area">
          <div class="input-wrapper">
            <textarea 
              class="ai-input" 
              placeholder="输入你的问题或需求..."
              rows="1"
              v-model="aiInput"
              @input="autoResize"
              @keypress.enter.prevent="sendMessage"
            ></textarea>
            <button class="ai-send-btn" @click="sendMessage">
              <IconBase name="paperPlane" :size="16" />
            </button>
          </div>
        </div>
      </aside>
    </div>

    <!-- 底部状态栏 -->
    <footer class="editor-footer">
      <div class="footer-left">
        <span class="footer-info">正在编辑：第{{ currentPage }}页</span>
      </div>
      <div class="footer-right">
        <span class="footer-info">最后保存：{{ lastSaved }}</span>
      </div>
    </footer>

    <!-- 生成中提示 -->
    <div class="toast" :class="{ show: showGeneratingToast }">
      <div class="toast-content">
        <div class="spinner"></div>
        <span>AI正在生成内容...</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import IconBase from '../components/icons/IconBase.vue'
import { apiService } from '../services/api.js'

const route = useRoute()

// 项目信息
const projectTitle = ref('加载中...')
const isSaved = ref(true)
const userAvatar = 'https://api.dicebear.com/7.x/avataaars/svg?seed=user'
const presentationId = ref(null)

// 侧边栏
const activeTab = ref('outline')

// 大纲数据
const outlineItems = ref([])

// 幻灯片数据
const slides = ref([])
const renderTree = ref(null)

const currentPage = ref(1)
const totalPages = computed(() => slides.value.length)

const currentSlide = computed(() => {
  const slide = slides.value[currentPage.value - 1]
  return slide || {
    title: '页面标题',
    subtitle: currentPage.value === 1 ? 'PPT内容展示' : '副标题',
    date: new Date().getFullYear() + '年'
  }
})

// 获取画布样式
const getCanvasStyle = () => {
  const slide = currentSlide.value
  return {
    width: (slide.width || 1280) + 'px',
    height: (slide.height || 720) + 'px',
    background: slide.background || 'white'
  }
}

// 获取组件样式
const getComponentStyle = (component) => {
  const style = {
    position: 'absolute',
    left: component.x + 'px',
    top: component.y + 'px',
    width: component.w + 'px',
    height: component.h + 'px',
    zIndex: component.z
  }

  if (component.style) {
    if (component.style.color) {
      style.color = component.style.color
    }
    if (component.style.background) {
      style.backgroundColor = component.style.background
    }
    if (component.style.borderColor) {
      style.borderColor = component.style.borderColor
      style.borderWidth = '1px'
      style.borderStyle = 'solid'
    }
    if (component.style.borderWidth) {
      style.borderWidth = component.style.borderWidth + 'px'
    }
    if (component.style.radius) {
      style.borderRadius = component.style.radius + 'px'
    }
    if (component.style.fontFamily) {
      style.fontFamily = component.style.fontFamily
    }
    if (component.style.fontSize) {
      style.fontSize = component.style.fontSize + 'px'
    }
    if (component.style.bold) {
      style.fontWeight = 'bold'
    }
    if (component.style.italic) {
      style.fontStyle = 'italic'
    }
    if (component.style.align) {
      style.textAlign = component.style.align
    }
  }

  return style
}

// 从渲染树生成大纲和幻灯片
const generateFromRenderTree = (tree) => {
  const newOutlineItems = []
  const newSlides = []
  let slideNum = 1
  let sectionNum = 1

  console.log('🔍 解析渲染树:', tree)
  console.log('📋 树的结构:', JSON.stringify(tree, null, 2))

  // 获取主题信息
  const theme = tree?.themeTokens

  if (tree?.slides) {
    // 创建一个默认的大纲章节
    const outlineItem = {
      number: sectionNum++,
      title: tree.title || '演示文稿',
      expanded: true,
      children: []
    }

    tree.slides.forEach(slide => {
      console.log(`📄 处理幻灯片${slideNum}:`, slide)
      // 从第一个Title组件中提取标题
      let slideTitle = `页面${slideNum}`
      let processedComponents = []
      
      if (slide?.components) {
        const titleComponent = slide.components.find(c => c.type === 'Title')
        if (titleComponent?.props?.text) {
          slideTitle = titleComponent.props.text
        }
        console.log(`🎯 找到${slide.components.length}个组件`)
        
        // 处理组件，应用主题
        processedComponents = slide.components.map(component => {
          const processedComponent = { ...component }
          
          // 如果有主题但组件没有特定样式，应用主题默认样式
          if (theme && !processedComponent.style) {
            processedComponent.style = {}
          }
          
          // 应用主题颜色到组件
          if (theme && processedComponent.style) {
            // 根据组件类型应用主题颜色
            if (component.type === 'Title') {
              processedComponent.style.color = theme.colors?.text || '#111827'
              if (theme.typography?.fontFamily) {
                processedComponent.style.fontFamily = theme.typography.fontFamily
              }
            } else if (component.type === 'Subtitle') {
              processedComponent.style.color = theme.colors?.muted || '#4B5563'
              if (theme.typography?.fontFamily) {
                processedComponent.style.fontFamily = theme.typography.fontFamily
              }
            } else if (component.type === 'Text') {
              processedComponent.style.color = theme.colors?.text || '#111827'
              if (theme.typography?.fontFamily) {
                processedComponent.style.fontFamily = theme.typography.fontFamily
              }
            }
          }
          
          return processedComponent
        })
      }

      // 添加到大纲
      outlineItem.children.push({
        pageNumber: slideNum,
        title: slideTitle
      })

      // 确定幻灯片背景
      let slideBackground = slide.background
      if (!slideBackground) {
        if (slideNum === 1) {
          // 首页使用渐变背景
          slideBackground = 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
        } else if (theme) {
          // 使用主题背景
          slideBackground = theme.colors?.surface || 'white'
        } else {
          slideBackground = 'white'
        }
      }

      // 添加到幻灯片
      newSlides.push({
        number: slideNum,
        title: slideTitle,
        components: processedComponents,
        background: slideBackground,
        width: slide.width || 1280,
        height: slide.height || 720,
        theme: theme
      })

      slideNum++
    })

    newOutlineItems.push(outlineItem)
  }

  console.log('✅ 生成的幻灯片:', newSlides)
  return { outlineItems: newOutlineItems, slides: newSlides }
}

// 初始化数据
const initData = async () => {
  // 检查路由查询参数中是否有id
  const id = route.query.id
  
  if (id) {
    presentationId.value = id
    
    try {
      // 获取渲染树
      const tree = await apiService.getRenderTree(id)
      renderTree.value = tree
      
      // 从渲染树生成数据
      const { outlineItems: newOutline, slides: newSlides } = generateFromRenderTree(tree)
      outlineItems.value = newOutline
      slides.value = newSlides
      
      // 设置标题
      if (tree?.meta?.title) {
        projectTitle.value = tree.meta.title
      }
      
      console.log('接收到的渲染树:', tree)
    } catch (error) {
      console.error('加载演示文稿失败:', error)
      showToast('加载演示文稿失败，请稍后重试')
      // 使用默认数据
      useDefaultData()
    }
  } else {
    // 使用默认数据
    useDefaultData()
  }
}

const useDefaultData = () => {
  outlineItems.value = [
    {
      number: 1,
      title: '封面',
      expanded: true,
      children: [{ pageNumber: 1, title: '产品发布会' }]
    },
    {
      number: 2,
      title: '目录',
      expanded: false,
      children: [{ pageNumber: 2, title: '目录' }]
    },
    {
      number: 3,
      title: '第一章：产品介绍',
      expanded: true,
      children: [
        { pageNumber: 3, title: '产品概述' },
        { pageNumber: 4, title: '核心功能' },
        { pageNumber: 5, title: '技术优势' }
      ]
    }
  ]
  
  slides.value = [
    { number: 1, title: '产品发布会', background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' },
    { number: 2, title: '目录', background: 'white' },
    { number: 3, title: '产品概述', background: 'white' },
    { number: 4, title: '核心功能', background: 'white' },
    { number: 5, title: '技术优势', background: 'white' }
  ]
  
  projectTitle.value = '2024年度产品发布会'
}

// 画布缩放
const zoom = ref(100)
const canvasStyle = computed(() => ({
  transform: `scale(${zoom.value / 100})`,
  transformOrigin: 'center center'
}))

// AI 聊天
const aiInput = ref('')
const chatMessages = ref([])
const showGeneratingToast = ref(false)

const quickActions = [
  { text: '优化内容', icon: 'magic' },
  { text: '生成图片', icon: 'image' },
  { text: '调整风格', icon: 'palette' },
  { text: '补充数据', icon: 'chartBar' }
]

// 状态栏
const lastSaved = ref('刚刚')

// 方法
const toggleOutlineItem = (index) => {
  outlineItems.value[index].expanded = !outlineItems.value[index].expanded
}

const selectPage = (pageNumber) => {
  currentPage.value = pageNumber
}

const addPage = () => {
  const newNumber = slides.value.length + 1
  
  // 添加到幻灯片
  slides.value.push({
    number: newNumber,
    title: '新页面',
    background: 'white'
  })
  
  // 添加到大纲（在最后一个章节中）
  if (outlineItems.value.length > 0) {
    const lastItem = outlineItems.value[outlineItems.value.length - 1]
    if (!lastItem.children) {
      lastItem.children = []
    }
    lastItem.children.push({
      pageNumber: newNumber,
      title: '新页面'
    })
    lastItem.expanded = true
  }
  
  showToast('已添加新页面')
}

const zoomOut = () => {
  if (zoom.value > 50) zoom.value -= 10
}

const zoomIn = () => {
  if (zoom.value < 200) zoom.value += 10
}

const saveProject = async () => {
  isSaved.value = false
  
  if (presentationId.value) {
    try {
      // 这里可以调用后端的更新API
      showToast('保存成功')
      isSaved.value = true
      lastSaved.value = '刚刚'
    } catch (error) {
      console.error('保存失败:', error)
      showToast('保存失败，请稍后重试')
      isSaved.value = true
    }
  } else {
    // 没有ID，模拟保存
    setTimeout(() => {
      isSaved.value = true
      lastSaved.value = '刚刚'
      showToast('保存成功')
    }, 1000)
  }
}

const shareProject = () => {
  showToast('分享链接已复制到剪贴板')
}

const playPresentation = () => {
  showToast('开始演示模式')
}

const exportPresentation = async () => {
  if (!presentationId.value) {
    showToast('请先创建演示文稿')
    return
  }
  
  try {
    showToast('正在导出...')
    await apiService.exportPptx(presentationId.value)
    showToast('导出成功！文件已下载')
  } catch (error) {
    console.error('导出失败:', error)
    showToast('导出失败，请稍后重试')
  }
}

const undo = () => showToast('已撤销')
const redo = () => showToast('已重做')

const saveTitle = () => {
  if (projectTitle.value.trim()) {
    showToast('标题已保存')
  }
}

const autoResize = (e) => {
  const textarea = e.target
  textarea.style.height = 'auto'
  textarea.style.height = Math.min(textarea.scrollHeight, 100) + 'px'
}

const sendMessage = () => {
  const message = aiInput.value.trim()
  if (!message) return
  
  chatMessages.value.push({ type: 'user', content: message })
  aiInput.value = ''
  
  showGeneratingToast.value = true
  
  setTimeout(() => {
    showGeneratingToast.value = false
    const response = generateAIResponse(message)
    chatMessages.value.push({ type: 'ai', content: response })
  }, 1500)
}

const sendQuickMessage = (text) => {
  aiInput.value = text
  sendMessage()
}

const generateAIResponse = (userMessage) => {
  const responses = {
    '优化': '我已经为您优化了当前页面的内容，使其更加简洁有力。主要改进包括：\n\n1. 标题更加醒目\n2. 要点更加精炼\n3. 添加了数据支撑',
    '图片': '根据您的内容，我建议使用以下配图：\n\n1. 产品展示图 - 突出核心功能\n2. 数据图表 - 展示增长趋势\n3. 场景图 - 展示应用场景',
    '风格': '我为您准备了3种风格方案：\n\n1. 商务蓝 - 专业稳重\n2. 科技紫 - 创新前卫\n3. 简约白 - 清爽现代\n\n您喜欢哪一种？',
    '数据': '我为您补充了以下数据：\n\n• 市场规模：预计2025年达到1000亿\n• 增长率：年复合增长率25%\n• 用户满意度：95%的用户给予好评',
    'default': '我理解您的需求。让我为您处理这个问题。请稍等片刻，我正在分析最佳方案...'
  }
  
  for (const key in responses) {
    if (userMessage.includes(key)) {
      return responses[key]
    }
  }
  
  return responses['default']
}

const showToast = (message) => {
  // 简单的 toast 实现
  const toast = document.createElement('div')
  toast.className = 'editor-toast'
  toast.innerHTML = `
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
      <path d="M22 11.08V12C21.9988 14.1564 21.3005 16.2547 20.0093 17.9818C18.7182 19.709 16.9033 20.9725 14.8354 21.5839C12.7674 22.1953 10.5573 22.1219 8.53447 21.3746C6.51168 20.6273 4.78465 19.2461 3.61096 17.4371C2.43727 15.628 1.87979 13.4881 2.02168 11.3363C2.16356 9.18455 2.99721 7.13631 4.39828 5.49706C5.79935 3.85781 7.69279 2.71537 9.79619 2.24013C11.8996 1.7649 14.1003 1.98232 16.07 2.85999" stroke-linecap="round" stroke-linejoin="round"/>
      <path d="M22 4L12 14.01L9 11.01" stroke-linecap="round" stroke-linejoin="round"/>
    </svg>
    <span>${message}</span>
  `
  toast.style.cssText = `
    position: fixed;
    bottom: 48px;
    left: 50%;
    transform: translateX(-50%);
    background: var(--gray-800);
    color: white;
    padding: 12px 24px;
    border-radius: 8px;
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 14px;
    box-shadow: 0 10px 15px rgba(0,0,0,0.2);
    z-index: 9999;
    opacity: 0;
    transition: opacity 0.3s ease;
  `
  
  document.body.appendChild(toast)
  
  requestAnimationFrame(() => {
    toast.style.opacity = '1'
  })
  
  setTimeout(() => {
    toast.style.opacity = '0'
    setTimeout(() => toast.remove(), 300)
  }, 3000)
}

// 键盘快捷键
const handleKeydown = (e) => {
  // Ctrl/Cmd + S 保存
  if ((e.ctrlKey || e.metaKey) && e.key === 's') {
    e.preventDefault()
    saveProject()
  }
  
  // Ctrl/Cmd + Z 撤销
  if ((e.ctrlKey || e.metaKey) && e.key === 'z') {
    e.preventDefault()
    undo()
  }
  
  // Ctrl/Cmd + Shift + Z 重做
  if ((e.ctrlKey || e.metaKey) && e.shiftKey && e.key === 'z') {
    e.preventDefault()
    redo()
  }
}

// 自动保存
let autoSaveInterval

onMounted(() => {
  // 初始化数据
  initData()
  
  document.addEventListener('keydown', handleKeydown)
  
  // 每30秒自动保存
  autoSaveInterval = setInterval(() => {
    if (!isSaved.value) {
      saveProject()
    }
  }, 30000)
})

onUnmounted(() => {
  document.removeEventListener('keydown', handleKeydown)
  clearInterval(autoSaveInterval)
})
</script>

<style scoped>
.editor-page {
  height: 100vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

/* 顶部工具栏 */
.editor-header {
  height: 56px;
  background: white;
  border-bottom: 1px solid var(--gray-200);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 var(--space-4);
  flex-shrink: 0;
}

.header-left {
  display: flex;
  align-items: center;
  gap: var(--space-4);
}

.project-info {
  display: flex;
  align-items: center;
  gap: var(--space-3);
}

.project-title-input {
  font-size: 16px;
  font-weight: 600;
  color: var(--gray-800);
  border: none;
  background: transparent;
  padding: var(--space-2);
  border-radius: var(--radius-md);
  width: 300px;
  transition: all 0.2s ease;
}

.project-title-input:hover {
  background: var(--gray-100);
}

.project-title-input:focus {
  background: white;
  box-shadow: 0 0 0 2px var(--primary-200);
}

.project-status {
  font-size: 12px;
  color: var(--gray-500);
  display: flex;
  align-items: center;
  gap: var(--space-1);
}

.project-status.saved {
  color: var(--success-500);
}

.header-right {
  display: flex;
  align-items: center;
  gap: var(--space-3);
}

.user-avatar {
  width: 32px;
  height: 32px;
  border-radius: var(--radius-full);
  overflow: hidden;
  border: 2px solid var(--gray-200);
}

.user-avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

/* 编辑器主体 */
.editor-container {
  flex: 1;
  display: flex;
  overflow: hidden;
}

/* 左侧边栏 */
.editor-sidebar {
  width: 280px;
  background: var(--gray-50);
  border-right: 1px solid var(--gray-200);
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
}

.sidebar-tabs {
  display: flex;
  border-bottom: 1px solid var(--gray-200);
}

.sidebar-tab {
  flex: 1;
  padding: var(--space-3) 0;
  font-size: 13px;
  font-weight: 500;
  color: var(--gray-600);
  background: transparent;
  border: none;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-2);
  transition: all 0.2s ease;
}

.sidebar-tab:hover {
  color: var(--gray-800);
  background: var(--gray-100);
}

.sidebar-tab.active {
  color: var(--primary-600);
  background: white;
  border-bottom: 2px solid var(--primary-500);
}

.sidebar-content {
  flex: 1;
  overflow-y: auto;
  padding: var(--space-4);
}

/* 大纲树 */
.outline-tree {
  margin-bottom: var(--space-4);
}

.outline-item {
  margin-bottom: var(--space-1);
}

.outline-header {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-2) var(--space-3);
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all 0.2s ease;
}

.outline-header:hover {
  background: var(--gray-200);
}

.toggle-icon {
  color: var(--gray-500);
  width: 16px;
  text-align: center;
}

.outline-number {
  font-size: 12px;
  font-weight: 600;
  color: var(--gray-500);
  min-width: 20px;
}

.outline-title {
  font-size: 13px;
  font-weight: 500;
  color: var(--gray-700);
  flex: 1;
}

.outline-children {
  margin-left: var(--space-6);
  margin-top: var(--space-1);
}

.outline-item-page {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-2) var(--space-3);
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all 0.2s ease;
}

.outline-item-page:hover {
  background: var(--gray-200);
}

.outline-item-page.active {
  background: var(--primary-100);
}

.outline-item-page.active .page-number {
  color: var(--primary-600);
}

.outline-item-page.active .page-title {
  color: var(--primary-700);
  font-weight: 600;
}

.page-number {
  font-size: 11px;
  color: var(--gray-400);
  min-width: 20px;
}

.page-title {
  font-size: 13px;
  color: var(--gray-600);
}

.add-page-btn {
  width: 100%;
  padding: var(--space-3);
  font-size: 13px;
  font-weight: 500;
  color: var(--gray-600);
  background: transparent;
  border: 1px dashed var(--gray-300);
  border-radius: var(--radius-md);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-2);
  transition: all 0.2s ease;
}

.add-page-btn:hover {
  border-color: var(--primary-400);
  color: var(--primary-600);
  background: var(--primary-50);
}

/* 页面缩略图 */
.slides-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: var(--space-3);
}

.slide-thumb {
  cursor: pointer;
}

.slide-thumb-preview {
  position: relative;
  aspect-ratio: 16/9;
  border-radius: var(--radius-md);
  border: 2px solid transparent;
  overflow: hidden;
  transition: all 0.2s ease;
}

.slide-thumb:hover .slide-thumb-preview {
  border-color: var(--primary-300);
}

.slide-thumb.active .slide-thumb-preview {
  border-color: var(--primary-500);
  box-shadow: 0 0 0 3px var(--primary-100);
}

.slide-number {
  position: absolute;
  top: var(--space-2);
  left: var(--space-2);
  font-size: 10px;
  font-weight: 600;
  color: var(--gray-500);
  background: rgba(255, 255, 255, 0.9);
  padding: 2px 6px;
  border-radius: var(--radius-sm);
}

.slide-thumb-title {
  display: block;
  font-size: 12px;
  color: var(--gray-600);
  margin-top: var(--space-2);
  text-align: center;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* 画布区域 */
.editor-canvas-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: var(--gray-100);
  overflow: hidden;
}

.canvas-wrapper {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--space-8);
  overflow: auto;
}

.slide-canvas {
  background: white;
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-xl);
  overflow: hidden;
  flex-shrink: 0;
  transition: transform 0.2s ease;
}

.slide-content {
  width: 100%;
  height: 100%;
  position: relative;
}

/* 组件通用样式 */
.slide-component {
  box-sizing: border-box;
  display: flex;
  align-items: center;
  justify-content: flex-start;
  overflow: hidden;
}

.component-title {
  width: 100%;
  height: 100%;
  font-size: 48px;
  font-weight: 700;
  line-height: 1.2;
  color: inherit;
  display: flex;
  align-items: center;
}

.component-subtitle {
  width: 100%;
  height: 100%;
  font-size: 28px;
  line-height: 1.4;
  color: inherit;
  display: flex;
  align-items: center;
}

.component-text {
  width: 100%;
  height: 100%;
  font-size: 20px;
  line-height: 1.6;
  color: inherit;
  white-space: pre-wrap;
  display: flex;
  align-items: flex-start;
}

.component-bullet-list {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: flex-start;
  padding-top: 8px;
}

.component-bullet-list ul {
  margin: 0;
  padding-left: 28px;
  font-size: 20px;
  line-height: 2;
}

.component-bullet-list li {
  margin-bottom: 8px;
}

.component-quote {
  width: 100%;
  height: 100%;
  border-left: 5px solid #667eea;
  padding-left: 24px;
  font-size: 22px;
  font-style: italic;
  color: #4a5568;
  display: flex;
  align-items: center;
}

.component-divider {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.component-divider hr {
  width: 100%;
  border: none;
  border-top: 3px solid #e2e8f0;
}

.component-image {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}

.component-image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.component-other {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f7fafc;
  color: #718096;
  font-size: 14px;
  border: 2px dashed #cbd5e0;
  border-radius: 8px;
  font-weight: 500;
}

.slide-layout-title {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  text-align: center;
}

.slide-title {
  font-size: 48px;
  font-weight: 700;
  color: var(--gray-800);
  margin-bottom: var(--space-4);
}

.slide-subtitle {
  font-size: 24px;
  color: var(--gray-600);
  margin-bottom: var(--space-8);
}

.slide-date {
  font-size: 16px;
  color: var(--gray-500);
}

/* 画布工具栏 */
.canvas-toolbar {
  height: 48px;
  background: white;
  border-top: 1px solid var(--gray-200);
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-4);
  padding: 0 var(--space-4);
}

.toolbar-group {
  display: flex;
  align-items: center;
  gap: var(--space-1);
}

.toolbar-btn {
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--radius-md);
  color: var(--gray-600);
  background: transparent;
  border: none;
  cursor: pointer;
  transition: all 0.2s ease;
  gap: var(--space-1);
}

.toolbar-btn:hover {
  background: var(--gray-100);
  color: var(--gray-800);
}

.toolbar-divider {
  width: 1px;
  height: 24px;
  background: var(--gray-200);
}

.zoom-level {
  font-size: 13px;
  font-weight: 500;
  color: var(--gray-700);
  min-width: 50px;
  text-align: center;
}

.page-indicator {
  font-size: 13px;
  color: var(--gray-600);
}

/* AI助手面板 */
.editor-ai-panel {
  width: 320px;
  background: white;
  border-left: 1px solid var(--gray-200);
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
}

.ai-panel-header {
  padding: var(--space-4);
  border-bottom: 1px solid var(--gray-200);
  display: flex;
  align-items: center;
  gap: var(--space-3);
}

.ai-avatar {
  width: 44px;
  height: 44px;
  background: linear-gradient(135deg, var(--primary-500) 0%, var(--primary-600) 100%);
  border-radius: var(--radius-lg);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
}

.ai-info {
  flex: 1;
}

.ai-name {
  font-size: 15px;
  font-weight: 600;
  color: var(--gray-800);
  margin-bottom: 2px;
}

.ai-status {
  font-size: 12px;
  color: var(--gray-500);
  display: flex;
  align-items: center;
  gap: var(--space-1);
}

.status-dot {
  width: 8px;
  height: 8px;
  background: var(--success-500);
  border-radius: var(--radius-full);
  animation: pulse 2s infinite;
}

.ai-chat-container {
  flex: 1;
  overflow-y: auto;
  padding: var(--space-4);
}

.ai-welcome {
  margin-bottom: var(--space-4);
}

.ai-message {
  display: flex;
  gap: var(--space-3);
}

.ai-avatar-small {
  width: 32px;
  height: 32px;
  background: var(--primary-500);
  border-radius: var(--radius-md);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  flex-shrink: 0;
}

.message-content {
  flex: 1;
  background: var(--gray-100);
  padding: var(--space-3);
  border-radius: var(--radius-lg);
  border-top-left-radius: var(--space-1);
}

.message-content p {
  font-size: 13px;
  color: var(--gray-700);
  margin-bottom: var(--space-2);
  white-space: pre-line;
}

.message-content ul {
  margin: 0;
  padding-left: var(--space-4);
}

.message-content li {
  font-size: 13px;
  color: var(--gray-600);
  margin-bottom: var(--space-1);
}

.chat-messages {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}

.message {
  display: flex;
  gap: var(--space-3);
}

.message.user {
  flex-direction: row-reverse;
}

.message.user .message-content {
  background: var(--primary-500);
  color: white;
  border-top-left-radius: var(--radius-lg);
  border-top-right-radius: var(--space-1);
}

.message.user .message-content p {
  color: white;
}

/* 快捷操作 */
.ai-quick-actions {
  padding: var(--space-3) var(--space-4);
  border-top: 1px solid var(--gray-200);
  background: var(--gray-50);
}

.quick-actions-label {
  font-size: 12px;
  font-weight: 500;
  color: var(--gray-500);
  margin-bottom: var(--space-2);
  display: block;
}

.quick-actions-list {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2);
}

.quick-action-btn {
  padding: var(--space-2) var(--space-3);
  font-size: 12px;
  font-weight: 500;
  color: var(--gray-600);
  background: white;
  border: 1px solid var(--gray-200);
  border-radius: var(--radius-md);
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: var(--space-1);
  transition: all 0.2s ease;
}

.quick-action-btn:hover {
  border-color: var(--primary-400);
  color: var(--primary-600);
  background: var(--primary-50);
}

/* AI输入区域 */
.ai-input-area {
  padding: var(--space-3) var(--space-4);
  border-top: 1px solid var(--gray-200);
}

.input-wrapper {
  display: flex;
  gap: var(--space-2);
  background: var(--gray-100);
  border-radius: var(--radius-lg);
  padding: var(--space-2);
}

.ai-input {
  flex: 1;
  border: none;
  background: transparent;
  font-size: 13px;
  color: var(--gray-700);
  resize: none;
  max-height: 100px;
  padding: var(--space-1);
  font-family: inherit;
}

.ai-input::placeholder {
  color: var(--gray-500);
}

.ai-send-btn {
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--primary-500);
  color: white;
  border: none;
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all 0.2s ease;
  flex-shrink: 0;
}

.ai-send-btn:hover {
  background: var(--primary-600);
}

/* 底部状态栏 */
.editor-footer {
  height: 32px;
  background: var(--gray-800);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 var(--space-4);
  flex-shrink: 0;
}

.footer-info {
  font-size: 12px;
  color: var(--gray-400);
}

/* Toast提示 */
.toast {
  position: fixed;
  bottom: 48px;
  left: 50%;
  transform: translateX(-50%) translateY(100px);
  background: var(--gray-800);
  color: white;
  padding: var(--space-3) var(--space-5);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-lg);
  opacity: 0;
  transition: all 0.3s ease;
  z-index: 3000;
}

.toast.show {
  transform: translateX(-50%) translateY(0);
  opacity: 1;
}

.toast-content {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  font-size: 14px;
}

.spinner {
  width: 16px;
  height: 16px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top-color: white;
  border-radius: var(--radius-full);
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

@keyframes pulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.5;
  }
}

/* 响应式 */
@media (max-width: 1200px) {
  .editor-sidebar {
    width: 240px;
  }
  
  .editor-ai-panel {
    width: 280px;
  }
  
  .slide-canvas {
    width: 800px;
    height: 450px;
  }
}

@media (max-width: 1024px) {
  .editor-sidebar {
    display: none;
  }
  
  .editor-ai-panel {
    position: fixed;
    right: -320px;
    top: 56px;
    bottom: 32px;
    transition: right 0.3s ease;
    z-index: 100;
  }
  
  .editor-ai-panel.open {
    right: 0;
  }
  
  .slide-canvas {
    width: 720px;
    height: 405px;
  }
}

@media (max-width: 768px) {
  .slide-canvas {
    width: 100%;
    max-width: 600px;
    height: auto;
    aspect-ratio: 16/9;
  }
  
  .header-right .btn-secondary {
    display: none;
  }
  
  .canvas-toolbar {
    gap: var(--space-2);
  }
  
  .toolbar-divider {
    display: none;
  }
}
</style>
