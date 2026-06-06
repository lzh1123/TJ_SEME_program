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
        </div>
      </div>
      <div class="header-right">
        <button class="btn btn-secondary btn-sm" @click="saveProject">
          <IconBase name="save" :size="14" />
          保存
        </button>
        <div class="user-avatar">
          <img :src="userAvatar" alt="用户头像">
        </div>
      </div>
    </header>

    <!-- 编辑器主体 -->
    <div class="editor-container">
      <!-- 左侧边栏 - 大纲 -->
      <aside class="editor-sidebar" v-show="sidebarVisible">
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
      <main class="editor-canvas-area" :class="{ 'sidebar-hidden': !sidebarVisible }">
        <button class="toggle-sidebar-btn" @click="sidebarVisible = !sidebarVisible" :title="sidebarVisible ? '隐藏边栏' : '显示边栏'">
          <IconBase name="chevronLeft" :size="20" :style="{ transform: sidebarVisible ? 'none' : 'rotate(180deg)' }" />
        </button>
        
        <div class="canvas-wrapper" ref="canvasWrapper">
          <div class="slide-canvas" :style="getCanvasStyle()">
            <div class="slide-content" :style="{ transform: `scale(${zoom / 100})`, transformOrigin: 'center center' }">
              <div v-if="currentSlide.components && currentSlide.components.length > 0">
                <div 
                  v-for="component in currentSlide.components" 
                  :key="component.id"
                  class="slide-component"
                  :style="getComponentStyle(component)"
                >
                  <!-- Title组件 -->
                  <div v-if="component.type === 'Title'" class="component-title" :style="getComponentInnerStyle(component)">
                    {{ component.props?.text || '' }}
                  </div>
                  <!-- Subtitle组件 -->
                  <div v-else-if="component.type === 'Subtitle'" class="component-subtitle" :style="getComponentInnerStyle(component)">
                    {{ component.props?.text || '' }}
                  </div>
                  <!-- Text组件 -->
                  <div v-else-if="component.type === 'Text'" class="component-text" :style="getComponentInnerStyle(component)">
                    {{ component.props?.text || '' }}
                  </div>
                  <!-- BulletList组件 -->
                  <div v-else-if="component.type === 'BulletList'" class="component-bullet-list" :style="getComponentInnerStyle(component)">
                    <ul>
                      <li v-for="(item, idx) in component.props?.items || []" :key="idx">{{ item }}</li>
                    </ul>
                  </div>
                  <!-- Quote组件 -->
                  <div v-else-if="component.type === 'Quote'" class="component-quote" :style="getComponentInnerStyle(component)">
                    <blockquote>{{ component.props?.quote || '' }}</blockquote>
                    <cite v-if="component.props?.author">— {{ component.props.author }}</cite>
                  </div>
                  <!-- Timeline组件 -->
                  <div v-else-if="component.type === 'Timeline'" class="component-timeline" :style="getComponentInnerStyle(component)">
                    <ul class="timeline-list">
                      <li v-for="(event, idx) in component.props?.events || []" :key="idx">
                        <span class="timeline-date" v-if="event.date">{{ event.date }}</span>
                        <span class="timeline-label">{{ event.label }}</span>
                        <span class="timeline-detail" v-if="event.detail">{{ event.detail }}</span>
                      </li>
                    </ul>
                  </div>
                  <!-- KpiCards组件 -->
                  <div v-else-if="component.type === 'KpiCards'" class="component-kpi-cards" :style="getComponentInnerStyle(component)">
                    <div class="kpi-cards-grid">
                      <div 
                        v-for="(item, idx) in component.props?.items || []" 
                        :key="idx" 
                        class="kpi-card"
                      >
                        <div class="kpi-value">{{ item.value }}<span class="kpi-unit" v-if="item.unit">{{ item.unit }}</span></div>
                        <div class="kpi-label">{{ item.label }}</div>
                        <div v-if="item.delta" class="kpi-delta" :class="item.delta.startsWith('-') ? 'negative' : 'positive'">
                          {{ item.delta }}
                        </div>
                      </div>
                    </div>
                  </div>
                  <!-- ComparisonTable组件 -->
                  <div v-else-if="component.type === 'ComparisonTable'" class="component-comparison" :style="getComponentInnerStyle(component)">
                    <div class="comparison-left">
                      <h3 v-if="component.props?.left?.title">{{ component.props.left.title }}</h3>
                      <ul v-if="component.props?.left?.bullets">
                        <li v-for="(bullet, idx) in component.props.left.bullets" :key="idx">{{ bullet }}</li>
                      </ul>
                    </div>
                    <div class="comparison-divider"></div>
                    <div class="comparison-right">
                      <h3 v-if="component.props?.right?.title">{{ component.props.right.title }}</h3>
                      <ul v-if="component.props?.right?.bullets">
                        <li v-for="(bullet, idx) in component.props.right.bullets" :key="idx">{{ bullet }}</li>
                      </ul>
                    </div>
                  </div>
                  <!-- Swot组件 -->
                  <div v-else-if="component.type === 'Swot'" class="component-swot" :style="getComponentInnerStyle(component)">
                    <div class="swot-grid">
                      <div class="swot-item swot-strengths" v-if="component.props?.strengths">
                        <h4>S: 优势</h4>
                        <ul><li v-for="(item, idx) in component.props.strengths" :key="idx">{{ item }}</li></ul>
                      </div>
                      <div class="swot-item swot-weaknesses" v-if="component.props?.weaknesses">
                        <h4>W: 劣势</h4>
                        <ul><li v-for="(item, idx) in component.props.weaknesses" :key="idx">{{ item }}</li></ul>
                      </div>
                      <div class="swot-item swot-opportunities" v-if="component.props?.opportunities">
                        <h4>O: 机会</h4>
                        <ul><li v-for="(item, idx) in component.props.opportunities" :key="idx">{{ item }}</li></ul>
                      </div>
                      <div class="swot-item swot-threats" v-if="component.props?.threats">
                        <h4>T: 威胁</h4>
                        <ul><li v-for="(item, idx) in component.props.threats" :key="idx">{{ item }}</li></ul>
                      </div>
                    </div>
                  </div>
                  <!-- Roadmap组件 -->
                  <div v-else-if="component.type === 'Roadmap'" class="component-roadmap" :style="getComponentInnerStyle(component)">
                    <div class="roadmap-phases">
                      <div v-for="(phase, idx) in component.props?.phases || []" :key="idx" class="roadmap-phase">
                        <div class="phase-header">
                          <h5>{{ phase.name }}</h5>
                          <span class="phase-timeframe">{{ phase.timeframe }}</span>
                        </div>
                        <ul class="phase-deliverables">
                          <li v-for="(item, dIdx) in phase.deliverables || []" :key="dIdx">{{ item }}</li>
                        </ul>
                      </div>
                    </div>
                  </div>
                  <!-- ProcessFlow组件 -->
                  <div v-else-if="component.type === 'ProcessFlow'" class="component-process-flow" :style="getComponentInnerStyle(component)">
                    <div class="process-steps">
                      <div v-for="(step, idx) in component.props?.steps || []" :key="idx" class="process-step">
                        <div class="step-number">{{ idx + 1 }}</div>
                        <div class="step-content">
                          <h5>{{ step.name }}</h5>
                          <p v-if="step.detail">{{ step.detail }}</p>
                        </div>
                      </div>
                    </div>
                  </div>
                  <!-- MultiColumn组件 -->
                  <div v-else-if="component.type === 'MultiColumn'" class="component-multi-column" :style="getComponentInnerStyle(component)">
                    <div class="columns-grid">
                      <div v-for="(column, idx) in component.props?.columns || []" :key="idx" class="column-item">
                        <h4 v-if="column.title">{{ column.title }}</h4>
                        <ul v-if="column.bullets">
                          <li v-for="(bullet, bIdx) in column.bullets" :key="bIdx">{{ bullet }}</li>
                        </ul>
                      </div>
                    </div>
                  </div>
                  <!-- Chart组件 -->
                  <div v-else-if="component.type === 'Chart'" class="component-chart" :style="getComponentInnerStyle(component)">
                    <div class="chart-container">
                      <div class="chart-title">{{ component.props?.chartType === 'bar' ? '柱状图' : '图表' }}</div>
                      <div class="chart-content" v-if="component.props?.series && component.props?.labels">
                        <div class="chart-legend">
                          <div v-for="(series, idx) in component.props.series" :key="idx" class="legend-item">
                            <span class="legend-color" :style="{ backgroundColor: getChartColor(idx) }"></span>
                            <span>{{ series.name }}</span>
                          </div>
                        </div>
                        <div class="chart-bars">
                          <div v-for="(label, labelIdx) in component.props.labels" :key="labelIdx" class="bar-group">
                            <div class="bar-label">{{ label }}</div>
                            <div class="bar-row">
                              <div 
                                v-for="(series, seriesIdx) in component.props.series" 
                                :key="seriesIdx" 
                                class="bar"
                                :style="{ 
                                  height: (series.values[labelIdx] ? (series.values[labelIdx] / getMaxValue(component.props.series)) * 100 : 0) + '%',
                                  backgroundColor: getChartColor(seriesIdx),
                                  width: (100 / component.props.series.length) + '%'
                                }"
                                :title="`${series.name}: ${series.values[labelIdx]}`"
                              >
                                {{ series.values[labelIdx] }}
                              </div>
                            </div>
                          </div>
                        </div>
                      </div>
                      <div v-else class="chart-placeholder">
                        <IconBase name="chartBar" :size="48" />
                        <p>图表数据加载中</p>
                      </div>
                    </div>
                  </div>
                  <!-- ArchitectureDiagram组件 -->
                  <div v-else-if="component.type === 'ArchitectureDiagram'" class="component-arch" :style="getComponentInnerStyle(component)">
                    <div class="arch-container">
                      <div 
                        v-for="(layer, layerIdx) in component.props?.layers || []" 
                        :key="layerIdx" 
                        class="arch-layer"
                      >
                        <div class="arch-layer-header">{{ layer.name }}</div>
                        <div class="arch-layer-items">
                          <div 
                            v-for="(item, itemIdx) in layer.items || []" 
                            :key="itemIdx" 
                            class="arch-item"
                          >
                            {{ item }}
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                  <!-- TeamCards组件 -->
                  <div v-else-if="component.type === 'TeamCards'" class="component-team-cards" :style="getComponentInnerStyle(component)">
                    <div class="team-cards-grid">
                      <div 
                        v-for="(member, idx) in component.props?.members || []" 
                        :key="idx" 
                        class="team-card"
                      >
                        <div class="team-avatar">
                          <IconBase name="user" :size="32" />
                        </div>
                        <div class="team-info">
                          <h5 class="team-name">{{ member.name || '成员' }}</h5>
                          <p class="team-role" v-if="member.role">{{ member.role }}</p>
                          <p class="team-bio" v-if="member.bio">{{ member.bio }}</p>
                        </div>
                      </div>
                    </div>
                  </div>
                  <!-- Divider组件 -->
                  <div v-else-if="component.type === 'Divider'" class="component-divider" :style="getComponentInnerStyle(component)">
                    <div class="divider-container">
                      <div v-if="component.props?.title" class="divider-title">{{ component.props.title }}</div>
                      <div v-if="component.props?.subtitle" class="divider-subtitle">{{ component.props.subtitle }}</div>
                    </div>
                  </div>
                  <!-- 其他组件 -->
                  <div v-else class="component-other">
                    [{{ component.type }}]
                  </div>
                </div>
              </div>
              <!-- 备用默认渲染 -->
              <div v-else class="slide-fallback">
                <div class="slide-layout-title">
                  <h1 class="slide-title">{{ currentSlide.title }}</h1>
                  <p class="slide-subtitle">{{ currentSlide.subtitle }}</p>
                </div>
              </div>
            </div>
          </div>
        </div>
        
        <!-- 画布工具栏 -->
        <div class="canvas-toolbar">
          <div class="toolbar-group">
            <button class="toolbar-btn" title="缩小" @click="zoomOut">
              <IconBase name="minus" :size="16" />
            </button>
            <button class="toolbar-btn" title="适应屏幕" @click="zoomToFit">
              <IconBase name="chevronDown" :size="16" :style="{ transform: 'rotate(-45deg)' }" />
            </button>
            <span class="zoom-level">{{ zoom }}%</span>
            <button class="toolbar-btn" title="放大" @click="zoomIn">
              <IconBase name="plus" :size="16" />
            </button>
          </div>
          <div class="toolbar-divider"></div>
          <div class="toolbar-group">
            <span class="page-indicator">{{ currentPage }} / {{ totalPages }}</span>
          </div>
        </div>
      </main>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { useRoute } from 'vue-router'
import IconBase from '../components/icons/IconBase.vue'
import { apiService } from '../services/api.js'

const route = useRoute()

// 项目信息
const projectTitle = ref('加载中...')
const userAvatar = 'https://api.dicebear.com/7.x/avataaars/svg?seed=user'
const presentationId = ref(null)
const canvasWrapper = ref(null)

// 左侧边栏
const sidebarVisible = ref(true)
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
    background: '#ffffff'
  }
})

// 缩放
const zoom = ref(100)
const MIN_ZOOM = 20
const MAX_ZOOM = 200

// 获取画布样式
const getCanvasStyle = () => {
  const slide = currentSlide.value
  const baseHeight = slide.height || 720
  // Calculate actual needed height from bottommost component
  let maxBottom = baseHeight
  for (const c of (slide.components || [])) {
    const bottom = (c.y || 0) + (c.h || 0)
    if (bottom > maxBottom) maxBottom = bottom
  }
  const contentHeight = Math.max(baseHeight, maxBottom + 56)
  return {
    width: (slide.width || 1280) + 'px',
    minHeight: baseHeight + 'px',
    height: contentHeight + 'px',
    background: slide.background || '#ffffff'
  }
}

// 获取组件样式
const getComponentStyle = (component) => {
  const style = {
    position: 'absolute',
    left: (component.x || 0) + 'px',
    top: (component.y || 0) + 'px',
    width: (component.w || 200) + 'px',
    height: (component.h || 100) + 'px',
    zIndex: component.z || 1,
    boxSizing: 'border-box',
    padding: '16px'
  }

  if (component.style) {
    if (component.style.color) style.color = component.style.color
    if (component.style.background) style.backgroundColor = component.style.background
    if (component.style.borderColor) {
      style.borderColor = component.style.borderColor
      style.borderWidth = (component.style.borderWidth || 1) + 'px'
      style.borderStyle = 'solid'
    }
    if (component.style.radius) style.borderRadius = component.style.radius + 'px'
    if (component.style.fontFamily) style.fontFamily = component.style.fontFamily
  }

  return style
}

// 获取组件内部样式
const getComponentInnerStyle = (component) => {
  const style = {}
  if (component.style) {
    if (component.style.fontSize) style.fontSize = component.style.fontSize + 'px'
    if (component.style.bold) style.fontWeight = 'bold'
    if (component.style.italic) style.fontStyle = 'italic'
    if (component.style.align) style.textAlign = component.style.align
    if (component.style.color) style.color = component.style.color
  }
  return style
}

// 获取图表颜色
const getChartColor = (index) => {
  const colors = ['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6', '#06B6D4']
  return colors[index % colors.length]
}

// 获取图表最大值
const getMaxValue = (series) => {
  let max = 0
  series.forEach(s => {
    if (s.values) {
      s.values.forEach(v => {
        if (v > max) max = v
      })
    }
  })
  return max || 1
}

// 从渲染树生成大纲和幻灯片
const generateFromRenderTree = (tree) => {
  const newOutlineItems = []
  const newSlides = []
  let slideNum = 1
  let sectionNum = 1

  console.log('解析渲染树:', tree)

  if (tree?.slides) {
    const outlineItem = {
      number: sectionNum++,
      title: tree.title || '演示文稿',
      expanded: true,
      children: []
    }

    tree.slides.forEach(slide => {
      let slideTitle = `页面${slideNum}`
      
      if (slide?.components) {
        const titleComponent = slide.components.find(c => c.type === 'Title')
        if (titleComponent?.props?.text) {
          slideTitle = titleComponent.props.text
        } else {
          // 查找其他可能包含标题的组件
          const subtitleComponent = slide.components.find(c => c.type === 'Subtitle')
          if (subtitleComponent?.props?.text) {
            slideTitle = subtitleComponent.props.text
          } else {
            const quoteComponent = slide.components.find(c => c.type === 'Quote')
            if (quoteComponent?.props?.quote) {
              slideTitle = quoteComponent.props.quote.length > 20 
                ? quoteComponent.props.quote.substring(0, 20) + '...' 
                : quoteComponent.props.quote
            }
          }
        }
      }

      outlineItem.children.push({
        pageNumber: slideNum,
        title: slideTitle
      })

      newSlides.push({
        number: slideNum,
        title: slideTitle,
        components: slide.components || [],
        background: slide.background || '#ffffff',
        width: slide.width || 1280,
        height: slide.height || 720
      })

      slideNum++
    })

    newOutlineItems.push(outlineItem)
  }

  console.log('生成的幻灯片:', newSlides)
  return { outlineItems: newOutlineItems, slides: newSlides }
}

// 初始化数据
const initData = async () => {
  const id = route.query.id
  
  // 先检查window.__presentationBundle是否存在
  if (window.__presentationBundle) {
    console.log('从window.__presentationBundle加载数据:', window.__presentationBundle)
    const bundle = window.__presentationBundle
    presentationId.value = id || bundle.meta?.id
    
    if (bundle.renderTree) {
      renderTree.value = bundle.renderTree
      const { outlineItems: newOutline, slides: newSlides } = generateFromRenderTree(bundle.renderTree)
      outlineItems.value = newOutline
      slides.value = newSlides
      if (bundle.renderTree?.title) projectTitle.value = bundle.renderTree.title
      else if (bundle.dsl?.title) projectTitle.value = bundle.dsl.title
      else if (bundle.meta?.topic) projectTitle.value = bundle.meta.topic
    } else if (bundle.dsl) {
      console.error('只有DSL没有renderTree，需要调用API生成')
      useDefaultData()
    }
    
    // 清除window上的数据
    delete window.__presentationBundle
    return
  }
  
  if (id) {
    presentationId.value = id
    try {
      const tree = await apiService.getRenderTree(id)
      renderTree.value = tree
      const { outlineItems: newOutline, slides: newSlides } = generateFromRenderTree(tree)
      outlineItems.value = newOutline
      slides.value = newSlides
      if (tree?.title) projectTitle.value = tree.title
      else if (tree?.meta?.title) projectTitle.value = tree.meta.title
      console.log('接收到的渲染树:', tree)
    } catch (error) {
      console.error('加载演示文稿失败:', error)
      useDefaultData()
    }
  } else {
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
    }
  ]
  slides.value = [
    { number: 1, title: '产品发布会', background: '#ffffff', components: [] }
  ]
  projectTitle.value = '演示文稿'
}

// 自动计算合适的缩放比例
const autoFit = () => {
  if (!canvasWrapper.value) return
  
  const wrapperRect = canvasWrapper.value.getBoundingClientRect()
  const slideWidth = currentSlide.value.width || 1280
  const slideHeight = currentSlide.value.height || 720
  
  const padding = 60
  const availableWidth = wrapperRect.width - padding * 2
  const availableHeight = wrapperRect.height - padding * 2
  
  const scaleX = availableWidth / slideWidth
  const scaleY = availableHeight / slideHeight
  
  const newZoom = Math.min(scaleX, scaleY, 1) * 100
  zoom.value = Math.max(MIN_ZOOM, Math.min(MAX_ZOOM, Math.round(newZoom)))
}

const zoomOut = () => {
  if (zoom.value > MIN_ZOOM) {
    zoom.value = Math.max(MIN_ZOOM, zoom.value - 10)
  }
}

const zoomIn = () => {
  if (zoom.value < MAX_ZOOM) {
    zoom.value = Math.min(MAX_ZOOM, zoom.value + 10)
  }
}

const zoomToFit = () => {
  autoFit()
}

// 操作方法
const toggleOutlineItem = (index) => {
  outlineItems.value[index].expanded = !outlineItems.value[index].expanded
}

const selectPage = (pageNumber) => {
  currentPage.value = pageNumber
}

const saveTitle = () => {}
const saveProject = () => {}

// 生命周期
onMounted(async () => {
  await initData()
  await nextTick()
  setTimeout(() => autoFit(), 100)
  
  window.addEventListener('resize', autoFit)
})

onUnmounted(() => {
  window.removeEventListener('resize', autoFit)
})

// 监听边栏显示状态变化，触发重新适应
watch(sidebarVisible, async () => {
  await nextTick()
  setTimeout(() => autoFit(), 100)
})

// 监听当前页变化，触发重新适应
watch(currentPage, async () => {
  await nextTick()
  setTimeout(() => autoFit(), 50)
})
</script>

<style scoped>
.editor-page {
  height: 100vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.editor-header {
  height: 56px;
  background: white;
  border-bottom: 1px solid #e5e7eb;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 16px;
  flex-shrink: 0;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.project-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.project-title-input {
  font-size: 16px;
  font-weight: 600;
  color: #1f2937;
  border: none;
  background: transparent;
  padding: 8px;
  border-radius: 6px;
  width: 300px;
}

.project-title-input:hover {
  background: #f3f4f6;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.user-avatar {
  width: 32px;
  height: 32px;
  border-radius: 999px;
  overflow: hidden;
  border: 2px solid #e5e7eb;
}

.user-avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.editor-container {
  flex: 1;
  display: flex;
  overflow: hidden;
}

.editor-sidebar {
  width: 280px;
  background: #f9fafb;
  border-right: 1px solid #e5e7eb;
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
}

.sidebar-tabs {
  display: flex;
  border-bottom: 1px solid #e5e7eb;
}

.sidebar-tab {
  flex: 1;
  padding: 12px 0;
  font-size: 13px;
  font-weight: 500;
  color: #4b5563;
  background: transparent;
  border: none;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

.sidebar-tab:hover {
  color: #1f2937;
  background: #f3f4f6;
}

.sidebar-tab.active {
  color: #3b82f6;
  background: white;
  border-bottom: 2px solid #3b82f6;
}

.sidebar-content {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
}

.outline-tree {
  margin-bottom: 16px;
}

.outline-item {
  margin-bottom: 4px;
}

.outline-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  border-radius: 6px;
  cursor: pointer;
}

.outline-header:hover {
  background: #e5e7eb;
}

.toggle-icon {
  color: #6b7280;
  width: 16px;
  text-align: center;
}

.outline-number {
  font-size: 12px;
  font-weight: 600;
  color: #6b7280;
  min-width: 20px;
}

.outline-title {
  font-size: 13px;
  font-weight: 500;
  color: #374151;
  flex: 1;
}

.outline-children {
  margin-left: 24px;
  margin-top: 4px;
}

.outline-item-page {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  border-radius: 6px;
  cursor: pointer;
}

.outline-item-page:hover {
  background: #e5e7eb;
}

.outline-item-page.active {
  background: #dbeafe;
}

.outline-item-page.active .page-number {
  color: #3b82f6;
}

.outline-item-page.active .page-title {
  color: #1d4ed8;
  font-weight: 600;
}

.page-number {
  font-size: 11px;
  color: #6b7280;
  min-width: 20px;
}

.page-title {
  font-size: 13px;
  color: #4b5563;
}

.slides-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 12px;
}

.slide-thumb {
  cursor: pointer;
}

.slide-thumb-preview {
  position: relative;
  aspect-ratio: 16/9;
  border-radius: 8px;
  border: 2px solid transparent;
  overflow: hidden;
}

.slide-thumb:hover .slide-thumb-preview {
  border-color: #93c5fd;
}

.slide-thumb.active .slide-thumb-preview {
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px #dbeafe;
}

.slide-number {
  position: absolute;
  top: 8px;
  left: 8px;
  font-size: 10px;
  font-weight: 600;
  color: #6b7280;
  background: rgba(255,255,255,0.9);
  padding: 2px 6px;
  border-radius: 4px;
}

.slide-thumb-title {
  display: block;
  font-size: 12px;
  color: #4b5563;
  margin-top: 8px;
  text-align: center;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.editor-canvas-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: #f3f4f6;
  overflow: hidden;
  position: relative;
}

.toggle-sidebar-btn {
  position: absolute;
  left: 8px;
  top: 50%;
  transform: translateY(-50%);
  width: 32px;
  height: 48px;
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #4b5563;
  z-index: 10;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}

.toggle-sidebar-btn:hover {
  background: #f9fafb;
  color: #1f2937;
}

.editor-canvas-area.sidebar-hidden .toggle-sidebar-btn {
  left: 8px;
}

.canvas-wrapper {
  flex: 1;
  display: flex;
  align-items: flex-start;
  justify-content: center;
  padding: 32px;
  overflow-y: auto;
  overflow-x: auto;
  background: #e5e7eb;
  background-image: radial-gradient(circle, #d1d5db 1px, transparent 1px);
  background-size: 20px 20px;
}

.slide-canvas {
  background: white;
  border-radius: 8px;
  box-shadow: 0 10px 25px -5px rgba(0,0,0,0.1), 0 0 0 1px rgba(0,0,0,0.05);
  overflow: visible;
  flex-shrink: 0;
  position: relative;
}

.slide-content {
  width: 100%;
  height: 100%;
  position: relative;
  box-sizing: border-box;
}

.slide-fallback {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.slide-layout-title {
  text-align: center;
}

.slide-title {
  font-size: 48px;
  font-weight: 700;
  color: #1f2937;
}

.slide-subtitle {
  font-size: 24px;
  color: #4b5563;
  margin-top: 16px;
}

/* 组件通用样式 */
.slide-component {
  box-sizing: border-box;
  overflow: visible;
  word-wrap: break-word;
  overflow-wrap: break-word;
}

.component-title {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  font-weight: bold;
}

.component-subtitle {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
}

.component-text {
  width: 100%;
  height: 100%;
  white-space: pre-wrap;
  line-height: 1.6;
  word-wrap: break-word;
  overflow-wrap: break-word;
}

.component-bullet-list {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: flex-start;
  padding-top: 8px;
  word-wrap: break-word;
  overflow-wrap: break-word;
}

.component-bullet-list ul {
  margin: 0;
  padding-left: 24px;
  line-height: 2;
}

.component-bullet-list li {
  margin-bottom: 8px;
  word-wrap: break-word;
  overflow-wrap: break-word;
  white-space: normal;
}

.component-quote {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  justify-content: center;
  padding: 30px !important;
}

.component-quote blockquote {
  margin: 0;
  font-size: 1.3em;
  line-height: 1.8;
  padding: 0 20px;
  position: relative;
}

.component-quote blockquote::before {
  content: '“';
  font-size: 4em;
  opacity: 0.3;
  position: absolute;
  left: 0;
  top: -10px;
  font-family: serif;
}

.component-quote cite {
  margin-top: 20px;
  font-style: normal;
  opacity: 0.9;
  font-size: 0.9em;
  text-align: right;
  padding-right: 20px;
}

/* Timeline组件 */
.component-timeline {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
}

.timeline-list {
  width: 100%;
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.timeline-list li {
  display: flex;
  flex-direction: column;
  gap: 4px;
  position: relative;
  padding-left: 44px;
}

.timeline-list li::before {
  content: '';
  position: absolute;
  left: 0;
  top: 4px;
  width: 20px;
  height: 20px;
  background: #3b82f6;
  border-radius: 50%;
}

.timeline-list li::after {
  content: '';
  position: absolute;
  left: 9px;
  top: 24px;
  width: 2px;
  height: calc(100% + 8px);
  background: #d1d5db;
}

.timeline-list li:last-child::after {
  display: none;
}

.timeline-date {
  font-size: 0.85em;
  font-weight: 600;
  color: #3b82f6;
}

.timeline-label {
  font-weight: 600;
}

.timeline-detail {
  opacity: 0.7;
  font-size: 0.9em;
}

/* KPI Cards组件 */
.component-kpi-cards {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.kpi-cards-grid {
  width: 100%;
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
}

.kpi-card {
  text-align: center;
  padding: 16px;
}

.kpi-value {
  font-size: 32px;
  font-weight: 700;
  color: #3b82f6;
  line-height: 1.1;
}

.kpi-unit {
  font-size: 0.6em;
  margin-left: 4px;
  color: #6b7280;
}

.kpi-label {
  margin-top: 8px;
  color: #4b5563;
}

.kpi-delta {
  margin-top: 4px;
  font-size: 0.85em;
  font-weight: 600;
}

.kpi-delta.positive { color: #10b981; }
.kpi-delta.negative { color: #ef4444; }

/* Comparison Table组件 */
.component-comparison {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: stretch;
  gap: 24px;
}

.comparison-left, .comparison-right {
  flex: 1;
  padding: 8px 0;
}

.comparison-left h3, .comparison-right h3 {
  margin: 0 0 12px 0;
  font-size: 1.1em;
  font-weight: 600;
}

.comparison-left ul, .comparison-right ul {
  margin: 0;
  padding-left: 20px;
}

.comparison-left li, .comparison-right li {
  margin-bottom: 8px;
  line-height: 1.5;
}

.comparison-divider {
  width: 2px;
  background: #e5e7eb;
  flex-shrink: 0;
}

/* Swot组件 */
.component-swot {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.swot-grid {
  width: 100%;
  height: 100%;
  display: grid;
  grid-template-columns: 1fr 1fr;
  grid-template-rows: 1fr 1fr;
  gap: 12px;
}

.swot-item {
  background: #f9fafb;
  padding: 16px;
  border-radius: 8px;
  overflow: auto;
}

.swot-item h4 {
  margin: 0 0 12px 0;
  font-size: 0.9em;
  font-weight: 700;
  text-transform: uppercase;
}

.swot-strengths { background: #dbeafe; color: #1d4ed8; }
.swot-weaknesses { background: #fef3c7; color: #92400e; }
.swot-opportunities { background: #d1fae5; color: #065f46; }
.swot-threats { background: #fee2e2; color: #991b1b; }

.swot-item ul {
  margin: 0;
  padding-left: 18px;
  font-size: 0.9em;
}

.swot-item li {
  margin-bottom: 6px;
}

/* Roadmap组件 */
.component-roadmap {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
}

.roadmap-phases {
  width: 100%;
  display: flex;
  gap: 16px;
}

.roadmap-phase {
  flex: 1;
  padding: 16px;
  background: #f9fafb;
  border-radius: 8px;
}

.phase-header {
  margin-bottom: 12px;
}

.phase-header h5 {
  margin: 0;
  font-size: 1em;
  font-weight: 600;
}

.phase-timeframe {
  display: inline-block;
  margin-top: 4px;
  font-size: 0.8em;
  color: #6b7280;
  background: #e5e7eb;
  padding: 2px 8px;
  border-radius: 4px;
}

.phase-deliverables {
  margin: 0;
  padding-left: 18px;
  font-size: 0.9em;
}

.phase-deliverables li {
  margin-bottom: 6px;
}

/* ProcessFlow组件 */
.component-process-flow {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
}

.process-steps {
  width: 100%;
  display: flex;
  gap: 16px;
}

.process-step {
  flex: 1;
  display: flex;
  gap: 12px;
  align-items: flex-start;
}

.step-number {
  width: 32px;
  height: 32px;
  background: #3b82f6;
  color: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  flex-shrink: 0;
}

.step-content {
  flex: 1;
}

.step-content h5 {
  margin: 0 0 8px 0;
  font-size: 1em;
  font-weight: 600;
}

.step-content p {
  margin: 0;
  font-size: 0.9em;
  opacity: 0.8;
}

/* MultiColumn组件 */
.component-multi-column {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
}

.columns-grid {
  width: 100%;
  display: flex;
  gap: 20px;
}

.column-item {
  flex: 1;
}

.column-item h4 {
  margin: 0 0 12px 0;
  font-size: 1em;
  font-weight: 600;
}

.column-item ul {
  margin: 0;
  padding-left: 18px;
  font-size: 0.9em;
}

.column-item li {
  margin-bottom: 8px;
}

/* Chart组件 */
.component-chart {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
}

.chart-container {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.chart-title {
  font-size: 1.1em;
  font-weight: 600;
  margin-bottom: 10px;
  text-align: center;
}

.chart-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.chart-legend {
  display: flex;
  flex-wrap: wrap;
  gap: 15px;
  justify-content: center;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 0.85em;
}

.legend-color {
  width: 12px;
  height: 12px;
  border-radius: 3px;
}

.chart-bars {
  flex: 1;
  display: flex;
  gap: 10px;
  align-items: flex-end;
  padding-bottom: 10px;
}

.bar-group {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  height: 100%;
}

.bar-label {
  font-size: 0.75em;
  text-align: center;
}

.bar-row {
  flex: 1;
  display: flex;
  align-items: flex-end;
  gap: 4px;
  width: 100%;
}

.bar {
  display: flex;
  align-items: flex-end;
  justify-content: center;
  font-size: 0.7em;
  color: white;
  padding: 2px;
  border-radius: 4px 4px 0 0;
  text-shadow: 0 0 2px rgba(0,0,0,0.5);
  min-height: 5px;
}

.chart-placeholder {
  text-align: center;
  color: #6b7280;
}

/* ArchitectureDiagram组件 */
.component-arch {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
}

.arch-container {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.arch-layer {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.arch-layer-header {
  font-size: 1.1em;
  font-weight: 700;
  color: #374151;
  padding-bottom: 8px;
  border-bottom: 2px solid #e5e7eb;
}

.arch-layer-items {
  flex: 1;
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
  align-items: flex-start;
}

.arch-item {
  background: #f3f4f6;
  padding: 10px 16px;
  border-radius: 8px;
  border: 1px solid #d1d5db;
  font-size: 0.95em;
  font-weight: 500;
  color: #1f2937;
  transition: all 0.2s ease;
}

.arch-item:hover {
  background: #e5e7eb;
  border-color: #9ca3af;
}

/* TeamCards组件 */
.component-team-cards {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  padding: 16px;
}

.team-cards-grid {
  width: 100%;
  height: 100%;
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
}

.team-card {
  display: flex;
  align-items: center;
  gap: 16px;
  background: #f9fafb;
  padding: 20px;
  border-radius: 12px;
  border: 1px solid #e5e7eb;
}

.team-avatar {
  width: 64px;
  height: 64px;
  border-radius: 50%;
  background: linear-gradient(135deg, #3b82f6, #8b5cf6);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  flex-shrink: 0;
}

.team-info {
  flex: 1;
  min-width: 0;
}

.team-name {
  margin: 0;
  font-size: 1.1em;
  font-weight: 600;
  color: #1f2937;
}

.team-role {
  margin: 4px 0 0 0;
  font-size: 0.9em;
  color: #3b82f6;
  font-weight: 500;
}

.team-bio {
  margin: 6px 0 0 0;
  font-size: 0.85em;
  color: #6b7280;
  line-height: 1.4;
}

/* Divider组件 */
.component-divider {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.divider-container {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 16px;
  text-align: center;
}

.divider-title {
  font-size: 2.2em;
  font-weight: 700;
  color: #1f2937;
  line-height: 1.2;
}

.divider-subtitle {
  font-size: 1.2em;
  color: #6b7280;
  line-height: 1.4;
}

.component-other {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f3f4f6;
  color: #6b7280;
  font-size: 14px;
  border: 2px dashed #d1d5db;
  border-radius: 8px;
  font-weight: 500;
}

.canvas-toolbar {
  height: 48px;
  background: white;
  border-top: 1px solid #e5e7eb;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 16px;
  padding: 0 16px;
}

.toolbar-group {
  display: flex;
  align-items: center;
  gap: 4px;
}

.toolbar-btn {
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 6px;
  color: #4b5563;
  background: transparent;
  border: none;
  cursor: pointer;
  gap: 4px;
}

.toolbar-btn:hover {
  background: #f3f4f6;
  color: #1f2937;
}

.toolbar-divider {
  width: 1px;
  height: 24px;
  background: #e5e7eb;
}

.zoom-level {
  font-size: 13px;
  font-weight: 500;
  color: #374151;
  min-width: 50px;
  text-align: center;
}

.page-indicator {
  font-size: 13px;
  color: #4b5563;
}
</style>
