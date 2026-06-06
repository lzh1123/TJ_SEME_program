<template>
  <div class="outline-editor-page">
    <!-- 顶部工具栏 -->
    <header class="editor-header">
      <div class="header-left">
        <button class="btn btn-ghost btn-icon" @click="goBack" title="返回上一页">
          <IconBase name="arrowLeft" :size="18" />
        </button>
        <router-link to="/" class="btn btn-ghost btn-icon" title="返回主页">
          <IconBase name="home" :size="18" />
        </router-link>
        <div class="header-title-group">
          <label class="header-label">大纲标题</label>
          <input
            type="text"
            class="title-input"
            v-model="dsl.title"
            placeholder="输入大纲标题"
          />
        </div>
        <span class="slide-count-badge">{{ dsl.slides.length }} 页</span>
      </div>
      <div class="header-right">
        <div class="download-dropdown">
          <button class="btn btn-secondary" @click.stop="showDownloadMenu = !showDownloadMenu">
            <IconBase name="download" :size="14" />
            下载
          </button>
          <div class="download-menu" v-if="showDownloadMenu">
            <button @click="downloadOutline('json')">
              <IconBase name="fileCode" :size="14" />
              下载 JSON
            </button>
            <button @click="downloadOutline('md')">
              <IconBase name="fileAlt" :size="14" />
              下载 Markdown
            </button>
          </div>
        </div>
        <button class="btn btn-secondary" @click="saveOutline" :disabled="isSaving">
          <IconBase name="save" :size="14" />
          {{ isSaving ? '保存中...' : '保存' }}
        </button>
        <button class="btn btn-primary" @click="generatePPT" :disabled="isGenerating">
          <IconBase v-if="isGenerating" name="spinner" :size="14" class="animate-spin" />
          <IconBase v-else name="magic" :size="14" />
          {{ isGenerating ? '生成中...' : '生成PPT' }}
        </button>
      </div>
    </header>

    <!-- 主体内容 -->
    <div class="editor-body">
      <!-- 左侧：大纲树 -->
      <aside class="outline-sidebar">
        <div class="sidebar-header">
          <h3>大纲结构</h3>
          <button class="btn btn-sm btn-primary" @click="addSlide()">
            <IconBase name="plus" :size="12" />
            添加页
          </button>
        </div>
        <div class="slide-list">
          <div
            v-for="(slide, index) in dsl.slides"
            :key="slide.id || index"
            :class="['slide-item', { active: selectedIndex === index }]"
            @click="selectSlide(index)"
          >
            <div class="slide-index">{{ index + 1 }}</div>
            <div class="slide-preview">
              <span class="slide-type-badge">{{ getIntentLabel(slide.intent) }}</span>
              <span class="slide-mini-title">{{ slide.title || '未命名' }}</span>
            </div>
            <div class="slide-item-actions">
              <button
                class="mini-btn"
                :disabled="index === 0"
                @click.stop="moveSlide(index, -1)"
                title="上移"
              >
                <IconBase name="chevronUp" :size="12" />
              </button>
              <button
                class="mini-btn"
                :disabled="index === dsl.slides.length - 1"
                @click.stop="moveSlide(index, 1)"
                title="下移"
              >
                <IconBase name="chevronDown" :size="12" />
              </button>
              <button
                class="mini-btn danger"
                :disabled="dsl.slides.length <= 1"
                @click.stop="removeSlide(index)"
                title="删除"
              >
                <IconBase name="trash" :size="12" />
              </button>
            </div>
          </div>
        </div>
        <div class="sidebar-footer">
          <span class="sidebar-hint">共 {{ dsl.slides.length }} 页</span>
        </div>
      </aside>

      <!-- 右侧：编辑区域 -->
      <main class="edit-area" v-if="selectedSlide">
        <div class="edit-panel">
          <!-- 基本信息 -->
          <div class="edit-section">
            <h4 class="section-heading">基本信息</h4>
            <div class="form-row">
              <label class="form-label-sm">页面标题</label>
              <input type="text" class="input" v-model="selectedSlide.title" placeholder="输入页面标题" />
            </div>
            <div class="form-row">
              <label class="form-label-sm">页面类型</label>
              <select class="input" v-model="selectedSlide.intent" @change="onIntentChange">
                <option v-for="opt in intentOptions" :key="opt.value" :value="opt.value">{{ opt.label }}</option>
              </select>
            </div>
          </div>

          <!-- cover -->
          <div class="edit-section" v-if="selectedSlide.intent === 'cover'">
            <h4 class="section-heading">封面内容</h4>
            <div class="form-row"><label class="form-label-sm">副标题</label><input class="input" v-model="selectedSlide.subtitle" placeholder="副标题" /></div>
            <div class="form-row"><label class="form-label-sm">标语</label><input class="input" v-model="selectedSlide.tagline" placeholder="标语" /></div>
            <div class="form-row">
              <label class="form-label-sm">亮点</label>
              <div class="list-editor">
                <div v-for="(h, hi) in (selectedSlide.highlights || [])" :key="hi" class="list-item-row">
                  <input class="input" v-model="selectedSlide.highlights[hi]" placeholder="亮点内容" />
                  <button class="mini-btn danger" @click="selectedSlide.highlights.splice(hi,1)"><IconBase name="trash" :size="12" /></button>
                </div>
                <button class="btn btn-sm btn-secondary" @click="if(!selectedSlide.highlights)selectedSlide.highlights=[];selectedSlide.highlights.push('')"><IconBase name="plus" :size="12" /> 添加</button>
              </div>
            </div>
          </div>

          <!-- agenda -->
          <div class="edit-section" v-else-if="selectedSlide.intent === 'agenda'">
            <h4 class="section-heading">议程内容</h4>
            <div class="form-row">
              <label class="form-label-sm">议程项</label>
              <div class="list-editor">
                <div v-for="(item, ii) in (selectedSlide.items || [])" :key="ii" class="list-item-row">
                  <input class="input" v-model="selectedSlide.items[ii]" placeholder="议程项内容" />
                  <button class="mini-btn danger" @click="selectedSlide.items.splice(ii,1)"><IconBase name="trash" :size="12" /></button>
                </div>
                <button class="btn btn-sm btn-secondary" @click="if(!selectedSlide.items)selectedSlide.items=[];selectedSlide.items.push('')"><IconBase name="plus" :size="12" /> 添加</button>
              </div>
            </div>
          </div>

          <!-- text -->
          <div class="edit-section" v-else-if="selectedSlide.intent === 'text'">
            <h4 class="section-heading">文本内容</h4>
            <div class="form-row">
              <label class="form-label-sm">要点列表</label>
              <div class="list-editor">
                <div v-for="(b, bi) in (selectedSlide.bullets || [])" :key="bi" class="list-item-row">
                  <input class="input" v-model="selectedSlide.bullets[bi]" placeholder="要点内容" />
                  <button class="mini-btn danger" @click="selectedSlide.bullets.splice(bi,1)"><IconBase name="trash" :size="12" /></button>
                </div>
                <button class="btn btn-sm btn-secondary" @click="if(!selectedSlide.bullets)selectedSlide.bullets=[];selectedSlide.bullets.push('')"><IconBase name="plus" :size="12" /> 添加</button>
              </div>
            </div>
            <div class="form-row">
              <label class="form-label-sm">段落</label>
              <div class="list-editor">
                <div v-for="(p, pi) in (selectedSlide.paragraphs || [])" :key="pi" class="list-item-row">
                  <textarea class="input textarea-sm" v-model="selectedSlide.paragraphs[pi]" placeholder="段落内容" rows="3"></textarea>
                  <button class="mini-btn danger" @click="selectedSlide.paragraphs.splice(pi,1)"><IconBase name="trash" :size="12" /></button>
                </div>
                <button class="btn btn-sm btn-secondary" @click="if(!selectedSlide.paragraphs)selectedSlide.paragraphs=[];selectedSlide.paragraphs.push('')"><IconBase name="plus" :size="12" /> 添加</button>
              </div>
            </div>
          </div>

          <!-- chart -->
          <div class="edit-section" v-else-if="selectedSlide.intent === 'chart'">
            <h4 class="section-heading">图表配置</h4>
            <div class="form-row">
              <label class="form-label-sm">图表类型</label>
              <select class="input" v-model="selectedSlide.chart.chartType">
                <option value="bar">柱状图</option>
                <option value="line">折线图</option>
                <option value="pie">饼图</option>
              </select>
            </div>
            <div class="form-row">
              <label class="form-label-sm">标签（逗号分隔）</label>
              <input class="input" :value="(selectedSlide.chart.labels||[]).join(',')" @input="selectedSlide.chart.labels = $event.target.value.split(',').map(s=>s.trim()).filter(Boolean)" placeholder="标签" />
            </div>
            <div v-for="(series, si) in (selectedSlide.chart.series || [])" :key="si" class="series-row">
              <input class="input" v-model="series.name" placeholder="系列名称" style="flex:1" />
              <input class="input" :value="(series.values||[]).join(',')" @input="series.values=$event.target.value.split(',').map(Number)" placeholder="值（逗号分隔）" style="flex:2" />
              <button class="mini-btn danger" @click="removeChartSeries(si)"><IconBase name="trash" :size="12" /></button>
            </div>
            <button class="btn btn-sm btn-secondary" @click="addChartSeries"><IconBase name="plus" :size="12" /> 添加系列</button>
          </div>

          <!-- quote -->
          <div class="edit-section" v-else-if="selectedSlide.intent === 'quote'">
            <h4 class="section-heading">引用内容</h4>
            <div class="form-row"><label class="form-label-sm">引用文字</label><textarea class="input textarea-sm" v-model="selectedSlide.quote" rows="4" placeholder="引用文字"></textarea></div>
            <div class="form-row"><label class="form-label-sm">作者</label><input class="input" v-model="selectedSlide.author" placeholder="作者" /></div>
          </div>

          <!-- kpi -->
          <div class="edit-section" v-else-if="selectedSlide.intent === 'kpi'">
            <h4 class="section-heading">KPI指标</h4>
            <div v-for="(item, ki) in (selectedSlide.items || [])" :key="ki" class="kpi-row">
              <input class="input" v-model="item.label" placeholder="指标名称" style="flex:2" />
              <input class="input" v-model="item.value" placeholder="数值" style="flex:1" />
              <input class="input" v-model="item.unit" placeholder="单位" style="flex:1" />
              <input class="input" v-model="item.delta" placeholder="变化" style="flex:1" />
              <button class="mini-btn danger" @click="removeKpiItem(ki)"><IconBase name="trash" :size="12" /></button>
            </div>
            <button class="btn btn-sm btn-secondary" @click="addKpiItem"><IconBase name="plus" :size="12" /> 添加指标</button>
          </div>

          <!-- timeline -->
          <div class="edit-section" v-else-if="selectedSlide.intent === 'timeline'">
            <h4 class="section-heading">时间线事件</h4>
            <div v-for="(event, ei) in (selectedSlide.events || [])" :key="ei" class="event-row">
              <input class="input" v-model="event.date" placeholder="日期" style="flex:1" />
              <input class="input" v-model="event.label" placeholder="事件名称" style="flex:2" />
              <input class="input" v-model="event.detail" placeholder="详情" style="flex:2" />
              <button class="mini-btn danger" @click="removeTimelineEvent(ei)"><IconBase name="trash" :size="12" /></button>
            </div>
            <button class="btn btn-sm btn-secondary" @click="addTimelineEvent"><IconBase name="plus" :size="12" /> 添加事件</button>
          </div>

          <!-- comparison -->
          <div class="edit-section" v-else-if="selectedSlide.intent === 'comparison'">
            <h4 class="section-heading">对比内容</h4>
            <div class="comparison-row">
              <div class="comparison-side">
                <label class="form-label-sm">左侧</label>
                <input class="input" v-model="selectedSlide.left.title" placeholder="左侧标题" style="margin-bottom:8px" />
                <div class="list-editor">
                  <div v-for="(b, bi) in (selectedSlide.left.bullets || [])" :key="bi" class="list-item-row">
                    <input class="input" v-model="selectedSlide.left.bullets[bi]" placeholder="要点" />
                    <button class="mini-btn danger" @click="selectedSlide.left.bullets.splice(bi,1)"><IconBase name="trash" :size="12" /></button>
                  </div>
                  <button class="btn btn-sm btn-secondary" @click="if(!selectedSlide.left.bullets)selectedSlide.left.bullets=[];selectedSlide.left.bullets.push('')"><IconBase name="plus" :size="12" /> 添加</button>
                </div>
              </div>
              <div class="comparison-side">
                <label class="form-label-sm">右侧</label>
                <input class="input" v-model="selectedSlide.right.title" placeholder="右侧标题" style="margin-bottom:8px" />
                <div class="list-editor">
                  <div v-for="(b, bi) in (selectedSlide.right.bullets || [])" :key="bi" class="list-item-row">
                    <input class="input" v-model="selectedSlide.right.bullets[bi]" placeholder="要点" />
                    <button class="mini-btn danger" @click="selectedSlide.right.bullets.splice(bi,1)"><IconBase name="trash" :size="12" /></button>
                  </div>
                  <button class="btn btn-sm btn-secondary" @click="if(!selectedSlide.right.bullets)selectedSlide.right.bullets=[];selectedSlide.right.bullets.push('')"><IconBase name="plus" :size="12" /> 添加</button>
                </div>
              </div>
            </div>
          </div>

          <!-- swot -->
          <div class="edit-section" v-else-if="selectedSlide.intent === 'swot'">
            <h4 class="section-heading">SWOT分析</h4>
            <div class="form-row">
              <label class="form-label-sm">优势 (S)</label>
              <div class="list-editor">
                <div v-for="(s, si) in (selectedSlide.swot?.strengths || [])" :key="si" class="list-item-row">
                  <input class="input" v-model="selectedSlide.swot.strengths[si]" placeholder="优势" />
                  <button class="mini-btn danger" @click="selectedSlide.swot.strengths.splice(si,1)"><IconBase name="trash" :size="12" /></button>
                </div>
                <button class="btn btn-sm btn-secondary" @click="ensureSwot();selectedSlide.swot.strengths.push('')"><IconBase name="plus" :size="12" /> 添加</button>
              </div>
            </div>
            <div class="form-row">
              <label class="form-label-sm">劣势 (W)</label>
              <div class="list-editor">
                <div v-for="(w, wi) in (selectedSlide.swot?.weaknesses || [])" :key="wi" class="list-item-row">
                  <input class="input" v-model="selectedSlide.swot.weaknesses[wi]" placeholder="劣势" />
                  <button class="mini-btn danger" @click="selectedSlide.swot.weaknesses.splice(wi,1)"><IconBase name="trash" :size="12" /></button>
                </div>
                <button class="btn btn-sm btn-secondary" @click="ensureSwot();selectedSlide.swot.weaknesses.push('')"><IconBase name="plus" :size="12" /> 添加</button>
              </div>
            </div>
            <div class="form-row">
              <label class="form-label-sm">机会 (O)</label>
              <div class="list-editor">
                <div v-for="(o, oi) in (selectedSlide.swot?.opportunities || [])" :key="oi" class="list-item-row">
                  <input class="input" v-model="selectedSlide.swot.opportunities[oi]" placeholder="机会" />
                  <button class="mini-btn danger" @click="selectedSlide.swot.opportunities.splice(oi,1)"><IconBase name="trash" :size="12" /></button>
                </div>
                <button class="btn btn-sm btn-secondary" @click="ensureSwot();selectedSlide.swot.opportunities.push('')"><IconBase name="plus" :size="12" /> 添加</button>
              </div>
            </div>
            <div class="form-row">
              <label class="form-label-sm">威胁 (T)</label>
              <div class="list-editor">
                <div v-for="(t, ti) in (selectedSlide.swot?.threats || [])" :key="ti" class="list-item-row">
                  <input class="input" v-model="selectedSlide.swot.threats[ti]" placeholder="威胁" />
                  <button class="mini-btn danger" @click="selectedSlide.swot.threats.splice(ti,1)"><IconBase name="trash" :size="12" /></button>
                </div>
                <button class="btn btn-sm btn-secondary" @click="ensureSwot();selectedSlide.swot.threats.push('')"><IconBase name="plus" :size="12" /> 添加</button>
              </div>
            </div>
          </div>

          <!-- roadmap -->
          <div class="edit-section" v-else-if="selectedSlide.intent === 'roadmap'">
            <h4 class="section-heading">路线图阶段</h4>
            <div v-for="(phase, pi) in (selectedSlide.phases || [])" :key="pi" class="phase-row">
              <input class="input" v-model="phase.name" placeholder="阶段名称" style="flex:2" />
              <input class="input" v-model="phase.timeframe" placeholder="时间范围" style="flex:1" />
              <input class="input" :value="(phase.deliverables||[]).join('; ')" @input="phase.deliverables=$event.target.value.split(';').map(s=>s.trim()).filter(Boolean)" placeholder="交付物（分号分隔）" style="flex:3" />
              <button class="mini-btn danger" @click="removeRoadmapPhase(pi)"><IconBase name="trash" :size="12" /></button>
            </div>
            <button class="btn btn-sm btn-secondary" @click="addRoadmapPhase"><IconBase name="plus" :size="12" /> 添加阶段</button>
          </div>

          <!-- process_flow -->
          <div class="edit-section" v-else-if="selectedSlide.intent === 'process_flow'">
            <h4 class="section-heading">流程步骤</h4>
            <div v-for="(step, si) in (selectedSlide.steps || [])" :key="si" class="step-row">
              <input class="input" v-model="step.name" placeholder="步骤名称" style="flex:2" />
              <input class="input" v-model="step.detail" placeholder="详情" style="flex:3" />
              <button class="mini-btn danger" @click="removeProcessStep(si)"><IconBase name="trash" :size="12" /></button>
            </div>
            <button class="btn btn-sm btn-secondary" @click="addProcessStep"><IconBase name="plus" :size="12" /> 添加步骤</button>
          </div>

          <!-- multi_column -->
          <div class="edit-section" v-else-if="selectedSlide.intent === 'multi_column'">
            <h4 class="section-heading">多列内容</h4>
            <div v-for="(col, ci) in (selectedSlide.columns || [])" :key="ci" class="column-row">
              <input class="input" v-model="col.title" placeholder="列标题" style="flex:2" />
              <input class="input" :value="(col.bullets||[]).join('; ')" @input="col.bullets=$event.target.value.split(';').map(s=>s.trim()).filter(Boolean)" placeholder="要点（分号分隔）" style="flex:3" />
              <button class="mini-btn danger" @click="removeColumn(ci)"><IconBase name="trash" :size="12" /></button>
            </div>
            <button class="btn btn-sm btn-secondary" @click="addColumn"><IconBase name="plus" :size="12" /> 添加列</button>
          </div>

          <!-- architecture -->
          <div class="edit-section" v-else-if="selectedSlide.intent === 'architecture'">
            <h4 class="section-heading">架构层次</h4>
            <div v-for="(layer, li) in (selectedSlide.layers || [])" :key="li" class="layer-row">
              <input class="input" v-model="layer.name" placeholder="层次名称" style="flex:1" />
              <input class="input" :value="(layer.items||[]).join('; ')" @input="layer.items=$event.target.value.split(';').map(s=>s.trim()).filter(Boolean)" placeholder="项目（分号分隔）" style="flex:3" />
              <button class="mini-btn danger" @click="removeLayer(li)"><IconBase name="trash" :size="12" /></button>
            </div>
            <button class="btn btn-sm btn-secondary" @click="addLayer"><IconBase name="plus" :size="12" /> 添加层次</button>
          </div>

          <!-- divider -->
          <div class="edit-section" v-else-if="selectedSlide.intent === 'divider'">
            <h4 class="section-heading">分隔页内容</h4>
            <div class="form-row"><label class="form-label-sm">副标题</label><input class="input" v-model="selectedSlide.subtitle" placeholder="副标题" /></div>
          </div>

          <!-- team -->
          <div class="edit-section" v-else-if="selectedSlide.intent === 'team'">
            <h4 class="section-heading">团队成员</h4>
            <div v-for="(member, mi) in (selectedSlide.members || [])" :key="mi" class="member-row">
              <input class="input" v-model="member.name" placeholder="姓名" style="flex:1" />
              <input class="input" v-model="member.role" placeholder="角色" style="flex:1" />
              <input class="input" :value="(member.highlights||[]).join('; ')" @input="member.highlights=$event.target.value.split(';').map(s=>s.trim()).filter(Boolean)" placeholder="亮点（分号分隔）" style="flex:2" />
              <button class="mini-btn danger" @click="removeTeamMember(mi)"><IconBase name="trash" :size="12" /></button>
            </div>
            <button class="btn btn-sm btn-secondary" @click="addTeamMember"><IconBase name="plus" :size="12" /> 添加成员</button>
          </div>

          <!-- 备注（通用） -->
          <div class="edit-section">
            <h4 class="section-heading">备注</h4>
            <div v-for="(note, ni) in (selectedSlide.notes || [])" :key="ni" class="note-row">
              <input class="input" v-model="selectedSlide.notes[ni]" :placeholder="`备注 ${ni+1}`" />
              <button class="mini-btn danger" @click="selectedSlide.notes.splice(ni,1)"><IconBase name="trash" :size="12" /></button>
            </div>
            <button class="btn btn-sm btn-secondary" @click="addNote"><IconBase name="plus" :size="12" /> 添加备注</button>
          </div>
        </div>
      </main>

      <!-- 空状态 -->
      <div class="edit-empty" v-if="!selectedSlide && dsl.slides.length === 0">
        <IconBase name="file" :size="48" />
        <p>点击左侧「添加页」创建第一页</p>
      </div>
    </div>

    <!-- Toast -->
    <Teleport to="body">
      <div v-if="toastMessage" class="toast-overlay" @click="toastMessage=''">
        <div class="toast-box" :class="toastType">
          <IconBase :name="toastType==='success'?'check':'infoCircle'" :size="16" />
          <span>{{ toastMessage }}</span>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import IconBase from '../components/icons/IconBase.vue'
import { useOutlineStore } from '../stores/outlineStore.js'
import { apiService } from '../services/api.js'
import { new_id } from '../utils/ids.js'

const route = useRoute()
const router = useRouter()
const outlineStore = useOutlineStore()

const dsl = ref({ title: '未命名大纲', audience: '通用受众', tone: '清晰、教学', theme: 'paper_light', slides: [] })
const selectedIndex = ref(0)
const isSaving = ref(false)
const isGenerating = ref(false)
const toastMessage = ref('')
const toastType = ref('success')
const outlineId = ref(null)
const showDownloadMenu = ref(false)

const selectedSlide = computed(() => {
  if (dsl.value.slides.length === 0) return null
  if (selectedIndex.value >= dsl.value.slides.length) selectedIndex.value = Math.max(0, dsl.value.slides.length - 1)
  return dsl.value.slides[selectedIndex.value] || null
})

const intentOptions = [
  { value: 'cover', label: '封面 (Cover)' }, { value: 'agenda', label: '议程 (Agenda)' },
  { value: 'text', label: '文本 (Text)' }, { value: 'chart', label: '图表 (Chart)' },
  { value: 'quote', label: '引用 (Quote)' }, { value: 'kpi', label: 'KPI指标 (KPI)' },
  { value: 'timeline', label: '时间线 (Timeline)' }, { value: 'comparison', label: '对比 (Comparison)' },
  { value: 'swot', label: 'SWOT分析 (SWOT)' }, { value: 'roadmap', label: '路线图 (Roadmap)' },
  { value: 'process_flow', label: '流程 (Process Flow)' }, { value: 'multi_column', label: '多列 (Multi Column)' },
  { value: 'architecture', label: '架构图 (Architecture)' }, { value: 'divider', label: '分隔页 (Divider)' },
  { value: 'team', label: '团队 (Team)' }
]

const getIntentLabel = (intent) => (intentOptions.find(o => o.value === intent) || { label: intent }).label.split(' ')[0]

const allowedFieldsByIntent = {
  cover: ['id','intent','section','title','notes','subtitle','tagline','highlights'],
  agenda: ['id','intent','section','title','notes','items'],
  text: ['id','intent','section','title','notes','paragraphs','bullets'],
  timeline: ['id','intent','section','title','notes','events'],
  kpi: ['id','intent','section','title','notes','items'],
  comparison: ['id','intent','section','title','notes','left','right'],
  swot: ['id','intent','section','title','notes','swot'],
  roadmap: ['id','intent','section','title','notes','phases'],
  process_flow: ['id','intent','section','title','notes','steps'],
  chart: ['id','intent','section','title','notes','chart'],
  multi_column: ['id','intent','section','title','notes','columns'],
  architecture: ['id','intent','section','title','notes','layers'],
  quote: ['id','intent','section','title','notes','quote','author'],
  divider: ['id','intent','section','title','notes','subtitle'],
  team: ['id','intent','section','title','notes','members']
}

const defaultSlideByIntent = {
  cover: { title:'新封面', intent:'cover', highlights:[], subtitle:'', tagline:'' },
  agenda: { title:'新议程', intent:'agenda', items:[] },
  text: { title:'新页面', intent:'text', bullets:[], paragraphs:[] },
  chart: { title:'新图表', intent:'chart', chart:{ chartType:'bar', labels:[], series:[] } },
  quote: { title:'新引用', intent:'quote', quote:'', author:'' },
  kpi: { title:'新KPI', intent:'kpi', items:[] },
  timeline: { title:'新时间线', intent:'timeline', events:[] },
  comparison: { title:'新对比', intent:'comparison', left:{ title:'', bullets:[] }, right:{ title:'', bullets:[] } },
  swot: { title:'新SWOT', intent:'swot', swot:{ strengths:[], weaknesses:[], opportunities:[], threats:[] } },
  roadmap: { title:'新路线图', intent:'roadmap', phases:[] },
  process_flow: { title:'新流程', intent:'process_flow', steps:[] },
  multi_column: { title:'新多列', intent:'multi_column', columns:[] },
  architecture: { title:'新架构', intent:'architecture', layers:[] },
  divider: { title:'新分隔页', intent:'divider', subtitle:'' },
  team: { title:'新团队', intent:'team', members:[] }
}

function normalizeSlide(slide) {
  const s = { ...slide }
  s.id = s.id || new_id('slide')
  s.section = s.section || ''
  s.notes = s.notes || []
  const def = defaultSlideByIntent[s.intent] || defaultSlideByIntent['text']
  Object.keys(def).forEach(k => {
    if (!['id','intent','title'].includes(k) && s[k] === undefined) {
      s[k] = JSON.parse(JSON.stringify(def[k]))
    }
  })
  if (s.intent === 'kpi') s.items = (s.items||[]).map(item => typeof item === 'string' ? { label:item, value:'' } : item)
  return s
}

onMounted(() => {
  const id = route.query.id
  outlineId.value = id
  if (id) {
    const loaded = outlineStore.getOutline(id)
    if (loaded) {
      loaded.slides = (loaded.slides||[]).map(normalizeSlide)
      dsl.value = loaded
      if (dsl.value.slides.length > 0) selectedIndex.value = 0
    }
  }
})

function showToast(msg, type='success') {
  toastMessage.value = msg
  toastType.value = type
  setTimeout(() => { toastMessage.value = '' }, 2500)
}

function toMarkdown(dsl) {
  const lines = []
  lines.push(`# ${dsl.title || '未命名大纲'}`)
  lines.push('')
  if (dsl.audience) lines.push(`> 受众：${dsl.audience}　|　风格：${dsl.tone || '—'}　|　主题：${dsl.theme || '—'}`)
  lines.push('')

  dsl.slides.forEach((slide, i) => {
    const label = getIntentLabel(slide.intent)
    lines.push(`## ${i + 1}. ${slide.title || '未命名'}（${label}）`)
    lines.push('')

    switch (slide.intent) {
      case 'cover':
        if (slide.subtitle) lines.push(`- **副标题**：${slide.subtitle}`)
        if (slide.tagline) lines.push(`- **标语**：${slide.tagline}`)
        if (slide.highlights?.length) {
          lines.push('- **亮点**：')
          slide.highlights.forEach(h => lines.push(`  - ${h}`))
        }
        break
      case 'agenda':
        if (slide.items?.length) {
          lines.push('- **议程项**：')
          slide.items.forEach(item => lines.push(`  - ${typeof item === 'string' ? item : item.text || item.label || ''}`))
        }
        break
      case 'text':
        if (slide.bullets?.length) {
          lines.push('### 要点')
          slide.bullets.forEach(b => lines.push(`- ${typeof b === 'string' ? b : b.text || ''}`))
          lines.push('')
        }
        if (slide.paragraphs?.length) {
          lines.push('### 段落')
          slide.paragraphs.forEach(p => lines.push(`${typeof p === 'string' ? p : p.text || ''}`))
          lines.push('')
        }
        break
      case 'chart':
        if (slide.chart) {
          lines.push(`- **图表类型**：${slide.chart.chartType || 'bar'}`)
          if (slide.chart.labels?.length) lines.push(`- **标签**：${slide.chart.labels.join(', ')}`)
          if (slide.chart.series?.length) {
            lines.push('- **数据系列**：')
            slide.chart.series.forEach(s => lines.push(`  - ${s.name}: ${(s.values || []).join(', ')}`))
          }
        }
        break
      case 'quote':
        if (slide.quote) lines.push(`> ${slide.quote}`)
        if (slide.author) lines.push(`— ${slide.author}`)
        break
      case 'kpi':
        if (slide.items?.length) {
          lines.push('| 指标 | 数值 | 单位 | 变化 |')
          lines.push('|------|------|------|------|')
          slide.items.forEach(item => lines.push(`| ${item.label || ''} | ${item.value || ''} | ${item.unit || ''} | ${item.delta || ''} |`))
        }
        break
      case 'timeline':
        if (slide.events?.length) {
          lines.push('| 日期 | 事件 | 详情 |')
          lines.push('|------|------|------|')
          slide.events.forEach(e => lines.push(`| ${e.date || ''} | ${e.label || ''} | ${e.detail || ''} |`))
        }
        break
      case 'comparison':
        if (slide.left) {
          lines.push(`- **${slide.left.title || '左侧'}**：${(slide.left.bullets || []).join('；')}`)
        }
        if (slide.right) {
          lines.push(`- **${slide.right.title || '右侧'}**：${(slide.right.bullets || []).join('；')}`)
        }
        break
      case 'swot':
        if (slide.swot) {
          const s = slide.swot
          if (s.strengths?.length) { lines.push('- **优势 (S)**：'); s.strengths.forEach(x => lines.push(`  - ${x}`)) }
          if (s.weaknesses?.length) { lines.push('- **劣势 (W)**：'); s.weaknesses.forEach(x => lines.push(`  - ${x}`)) }
          if (s.opportunities?.length) { lines.push('- **机会 (O)**：'); s.opportunities.forEach(x => lines.push(`  - ${x}`)) }
          if (s.threats?.length) { lines.push('- **威胁 (T)**：'); s.threats.forEach(x => lines.push(`  - ${x}`)) }
        }
        break
      case 'roadmap':
        if (slide.phases?.length) {
          slide.phases.forEach(p => {
            lines.push(`- **${p.name || ''}**${p.timeframe ? `（${p.timeframe}）` : ''}`)
            if (p.deliverables?.length) p.deliverables.forEach(d => lines.push(`  - ${d}`))
          })
        }
        break
      case 'process_flow':
        if (slide.steps?.length) {
          slide.steps.forEach((s, si) => lines.push(`${si + 1}. **${s.name || ''}**${s.detail ? ' — ' + s.detail : ''}`))
        }
        break
      case 'multi_column':
        if (slide.columns?.length) {
          slide.columns.forEach(col => {
            lines.push(`- **${col.title || ''}**：${(col.bullets || []).join('；')}`)
          })
        }
        break
      case 'architecture':
        if (slide.layers?.length) {
          slide.layers.forEach(l => lines.push(`- **${l.name || ''}**：${(l.items || []).join('、')}`))
        }
        break
      case 'divider':
        if (slide.subtitle) lines.push(`- **副标题**：${slide.subtitle}`)
        break
      case 'team':
        if (slide.members?.length) {
          slide.members.forEach(m => {
            lines.push(`- **${m.name || ''}**${m.role ? ` — ${m.role}` : ''}`)
            if (m.highlights?.length) m.highlights.forEach(h => lines.push(`  - ${h}`))
          })
        }
        break
    }

    if (slide.notes?.length) {
      lines.push('')
      lines.push('> 备注：' + slide.notes.join('；'))
    }
    lines.push('')
  })

  return lines.join('\n')
}

function downloadOutline(format) {
  showDownloadMenu.value = false

  const filename = (dsl.value.title || '大纲').replace(/[\\/:*?"<>|]/g, '_')

  if (format === 'json') {
    const json = JSON.stringify(dsl.value, null, 2)
    const blob = new Blob([json], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${filename}.json`
    a.click()
    URL.revokeObjectURL(url)
    showToast('JSON 下载成功')
  } else if (format === 'md') {
    const md = toMarkdown(dsl.value)
    const blob = new Blob([md], { type: 'text/markdown' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${filename}.md`
    a.click()
    URL.revokeObjectURL(url)
    showToast('Markdown 下载成功')
  }
}

function saveOutline() {
  isSaving.value = true
  try {
    if (outlineId.value) {
      outlineStore.saveOutline(outlineId.value, dsl.value)
    } else {
      const { id } = outlineStore.createOutline(dsl.value)
      outlineId.value = id
      router.replace({ path: '/outline-editor', query: { id } })
    }
    showToast('保存成功')
  } catch(e) { showToast('保存失败: '+e.message, 'error') }
  finally { isSaving.value = false }
}

async function generatePPT() {
  if (!dsl.value.title.trim()) { showToast('请先输入大纲标题','error'); return }
  if (outlineId.value) outlineStore.saveOutline(outlineId.value, dsl.value)
  else { const { id } = outlineStore.createOutline(dsl.value); outlineId.value = id; router.replace({ path:'/outline-editor', query:{ id } }) }

  isGenerating.value = true
  try {
    const cleanSlides = dsl.value.slides.map(s => {
      const clean = { id:s.id, intent:s.intent, section:s.section, title:s.title, notes:s.notes||[] }
      const fields = allowedFieldsByIntent[s.intent] || []
      fields.forEach(f => { if (!['id','intent','section','title','notes'].includes(f) && s[f]!==undefined) clean[f] = JSON.parse(JSON.stringify(s[f])) })
      return clean
    })
    const renderTree = await apiService.compileOutline(dsl.value.title, { ...dsl.value, slides: cleanSlides }, dsl.value.theme)
    const presId = new_id('pres')
    const bundle = { meta:{ id:presId, topic:dsl.value.title, createdAt:new Date().toISOString(), updatedAt:new Date().toISOString(), version:1 }, dsl:{ ...dsl.value, slides:cleanSlides }, renderTree }
    // Save to both window (immediate) and sessionStorage (survives back navigation)
    window.__presentationBundle = bundle
    try { sessionStorage.setItem('slideon_pres_' + presId, JSON.stringify(bundle)) } catch {}
    router.push({ path:'/editor', query:{ id:presId } })
  } catch(e) { showToast('生成PPT失败: '+e.message, 'error') }
  finally { isGenerating.value = false }
}

function selectSlide(i) { selectedIndex.value = i }
function addSlide(intent='text') {
  dsl.value.slides.push(normalizeSlide({ ...(defaultSlideByIntent[intent]||defaultSlideByIntent['text']), id:new_id('slide') }))
  selectedIndex.value = dsl.value.slides.length - 1
}
function removeSlide(i) { if(dsl.value.slides.length<=1){showToast('至少需要保留一页','error');return}; dsl.value.slides.splice(i,1); if(selectedIndex.value>=dsl.value.slides.length)selectedIndex.value=dsl.value.slides.length-1 }
function moveSlide(i,d) { const ni=i+d; if(ni<0||ni>=dsl.value.slides.length)return; const s=dsl.value.slides[i]; dsl.value.slides.splice(i,1); dsl.value.slides.splice(ni,0,s); selectedIndex.value=ni }
function onIntentChange() {
  if(!selectedSlide.value)return
  const cur=selectedSlide.value; const def=defaultSlideByIntent[cur.intent]||defaultSlideByIntent['text']
  Object.keys(cur).forEach(k=>{ if(!['id','intent','section','title','notes','_expanded','_editing'].includes(k)) delete cur[k] })
  Object.keys(def).forEach(k=>{ if(!['id','intent','title'].includes(k)) cur[k]=JSON.parse(JSON.stringify(def[k])) })
}

function addNote() { if(selectedSlide.value){ if(!selectedSlide.value.notes)selectedSlide.value.notes=[]; selectedSlide.value.notes.push('') } }
function addKpiItem() { if(selectedSlide.value){ if(!selectedSlide.value.items)selectedSlide.value.items=[]; selectedSlide.value.items.push({label:'',value:'',unit:'',delta:''}) } }
function removeKpiItem(i) { if(selectedSlide.value)selectedSlide.value.items.splice(i,1) }
function addTimelineEvent() { if(selectedSlide.value){ if(!selectedSlide.value.events)selectedSlide.value.events=[]; selectedSlide.value.events.push({date:'',label:'',detail:''}) } }
function removeTimelineEvent(i) { if(selectedSlide.value)selectedSlide.value.events.splice(i,1) }
function addChartSeries() { if(selectedSlide.value&&selectedSlide.value.chart){ if(!selectedSlide.value.chart.series)selectedSlide.value.chart.series=[]; selectedSlide.value.chart.series.push({name:'',values:[]}) } }
function removeChartSeries(i) { if(selectedSlide.value&&selectedSlide.value.chart)selectedSlide.value.chart.series.splice(i,1) }
function ensureSwot() { if(selectedSlide.value&&!selectedSlide.value.swot)selectedSlide.value.swot={strengths:[],weaknesses:[],opportunities:[],threats:[]} }
function addRoadmapPhase() { if(selectedSlide.value){ if(!selectedSlide.value.phases)selectedSlide.value.phases=[]; selectedSlide.value.phases.push({name:'',timeframe:'',deliverables:[]}) } }
function removeRoadmapPhase(i) { if(selectedSlide.value)selectedSlide.value.phases.splice(i,1) }
function addProcessStep() { if(selectedSlide.value){ if(!selectedSlide.value.steps)selectedSlide.value.steps=[]; selectedSlide.value.steps.push({name:'',detail:''}) } }
function removeProcessStep(i) { if(selectedSlide.value)selectedSlide.value.steps.splice(i,1) }
function addColumn() { if(selectedSlide.value){ if(!selectedSlide.value.columns)selectedSlide.value.columns=[]; selectedSlide.value.columns.push({title:'',bullets:[]}) } }
function removeColumn(i) { if(selectedSlide.value)selectedSlide.value.columns.splice(i,1) }
function addLayer() { if(selectedSlide.value){ if(!selectedSlide.value.layers)selectedSlide.value.layers=[]; selectedSlide.value.layers.push({name:'',items:[]}) } }
function removeLayer(i) { if(selectedSlide.value)selectedSlide.value.layers.splice(i,1) }
function addTeamMember() { if(selectedSlide.value){ if(!selectedSlide.value.members)selectedSlide.value.members=[]; selectedSlide.value.members.push({name:'',role:'',highlights:[]}) } }
function removeTeamMember(i) { if(selectedSlide.value)selectedSlide.value.members.splice(i,1) }

function goBack() {
  if (window.history.length > 1) {
    router.back()
  } else {
    router.push('/dashboard')
  }
}
function handleKeydown(e) { if((e.ctrlKey||e.metaKey)&&e.key==='s'){ e.preventDefault(); saveOutline() } }
function handleDocumentClick(e) {
  if (!e.target.closest('.download-dropdown')) showDownloadMenu.value = false
}
onMounted(() => {
  window.addEventListener('keydown', handleKeydown)
  document.addEventListener('click', handleDocumentClick)
})
</script>

<style scoped>
.outline-editor-page { height:100vh; overflow:hidden; display:flex; flex-direction:column; }
.editor-header { height:56px; background:white; border-bottom:1px solid #e5e7eb; display:flex; align-items:center; justify-content:space-between; padding:0 16px; flex-shrink:0; }
.header-left { display:flex; align-items:center; gap:12px; }
.header-title-group { display:flex; flex-direction:column; }
.header-label { font-size:11px; color:#6b7280; font-weight:500; }
.title-input { font-size:16px; font-weight:600; color:#1f2937; border:none; background:transparent; padding:4px 8px; border-radius:6px; width:320px; outline:none; }
.title-input:hover, .title-input:focus { background:#f3f4f6; }
.slide-count-badge { font-size:12px; color:#6b7280; background:#f3f4f6; padding:4px 10px; border-radius:999px; font-weight:500; }
.header-right { display:flex; align-items:center; gap:8px; }
.download-dropdown { position:relative; }
.download-menu { position:absolute; top:100%; right:0; margin-top:4px; background:white; border:1px solid #e5e7eb; border-radius:8px; box-shadow:0 10px 25px rgba(0,0,0,.12); overflow:hidden; z-index:100; min-width:160px; }
.download-menu button { display:flex; align-items:center; gap:8px; width:100%; padding:10px 16px; border:none; background:transparent; font-size:13px; color:#374151; cursor:pointer; white-space:nowrap; }
.download-menu button:hover { background:#f3f4f6; color:#1f2937; }
.editor-body { flex:1; display:flex; overflow:hidden; }
.outline-sidebar { width:280px; background:#f9fafb; border-right:1px solid #e5e7eb; display:flex; flex-direction:column; flex-shrink:0; }
.sidebar-header { display:flex; align-items:center; justify-content:space-between; padding:16px; border-bottom:1px solid #e5e7eb; }
.sidebar-header h3 { font-size:14px; font-weight:600; color:#1f2937; margin:0; }
.slide-list { flex:1; overflow-y:auto; padding:8px; display:flex; flex-direction:column; gap:4px; }
.slide-item { display:flex; align-items:center; gap:8px; padding:10px 12px; border-radius:8px; cursor:pointer; transition:all .15s; border:1px solid transparent; }
.slide-item:hover { background:#e5e7eb; }
.slide-item.active { background:#dbeafe; border-color:#93c5fd; }
.slide-index { width:24px; height:24px; border-radius:50%; background:#6366f1; color:white; font-size:11px; font-weight:600; display:flex; align-items:center; justify-content:center; flex-shrink:0; }
.slide-preview { flex:1; min-width:0; display:flex; flex-direction:column; gap:2px; }
.slide-type-badge { font-size:10px; color:#6366f1; background:#eef2ff; padding:1px 6px; border-radius:4px; align-self:flex-start; font-weight:500; }
.slide-mini-title { font-size:13px; color:#374151; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; font-weight:500; }
.slide-item-actions { display:flex; gap:2px; opacity:0; transition:opacity .15s; }
.slide-item:hover .slide-item-actions { opacity:1; }
.mini-btn { width:24px; height:24px; display:flex; align-items:center; justify-content:center; border:none; background:transparent; color:#6b7280; border-radius:4px; cursor:pointer; }
.mini-btn:hover { background:#d1d5db; color:#1f2937; }
.mini-btn:disabled { opacity:.3; cursor:not-allowed; }
.mini-btn.danger:hover { background:#fee2e2; color:#ef4444; }
.sidebar-footer { padding:12px 16px; border-top:1px solid #e5e7eb; }
.sidebar-hint { font-size:12px; color:#9ca3af; }
.edit-area { flex:1; overflow-y:auto; padding:24px; background:#fff; }
.edit-panel { max-width:720px; }
.edit-section { margin-bottom:24px; padding-bottom:20px; border-bottom:1px solid #f3f4f6; }
.section-heading { font-size:15px; font-weight:600; color:#1f2937; margin:0 0 12px; }
.form-row { margin-bottom:12px; }
.form-label-sm { display:block; font-size:12px; font-weight:600; color:#6b7280; margin-bottom:4px; text-transform:uppercase; letter-spacing:.5px; }
.list-editor { display:flex; flex-direction:column; gap:6px; margin-bottom:8px; }
.list-item-row { display:flex; align-items:center; gap:6px; }
.textarea-sm { min-height:60px; resize:vertical; padding:8px 12px; font-family:inherit; font-size:14px; }
.comparison-row { display:grid; grid-template-columns:1fr 1fr; gap:16px; }
.comparison-side { padding:12px; background:#f9fafb; border-radius:8px; border:1px solid #e5e7eb; }
.series-row,.kpi-row,.event-row,.phase-row,.step-row,.column-row,.layer-row,.member-row,.note-row { display:flex; align-items:center; gap:6px; margin-bottom:6px; }
.edit-empty { flex:1; display:flex; flex-direction:column; align-items:center; justify-content:center; color:#9ca3af; gap:12px; }
.edit-empty p { font-size:14px; }
.toast-overlay { position:fixed; top:80px; left:0; right:0; display:flex; justify-content:center; z-index:3000; pointer-events:none; }
.toast-box { display:flex; align-items:center; gap:8px; padding:10px 20px; background:#1f2937; color:white; border-radius:8px; font-size:14px; box-shadow:0 10px 25px rgba(0,0,0,.15); animation:slideUp .3s; pointer-events:auto; cursor:pointer; }
.toast-box.success { border-left:3px solid #10b981; }
.toast-box.error { border-left:3px solid #ef4444; }
.animate-spin { animation:spin 1s linear infinite; }
@keyframes slideUp { from{opacity:0;transform:translateY(-10px)} to{opacity:1;transform:translateY(0)} }
@keyframes spin { to{transform:rotate(360deg)} }
@media(max-width:1024px){ .outline-sidebar{width:220px} .title-input{width:200px} }
@media(max-width:768px){ .outline-sidebar{width:100%;max-height:200px;border-right:none;border-bottom:1px solid #e5e7eb} .editor-body{flex-direction:column} .edit-area{padding:16px} }
</style>
