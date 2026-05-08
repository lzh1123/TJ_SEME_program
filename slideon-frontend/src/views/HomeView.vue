<template>
  <div class="home">
    <AppHeader @create-ppt="openModal" />
    
    <!-- Hero区域 -->
    <section class="hero">
      <div class="container">
        <div class="hero-content">
          <h1 class="hero-title">智能PPT生成，让创作更高效</h1>
          <p class="hero-subtitle">输入主题，AI自动生成专业大纲和内容</p>
          <button class="btn btn-primary btn-xl" @click="openModal">
            <IconBase name="magic" :size="24" />
            开始生成
          </button>
        </div>
      </div>
    </section>

    <!-- 功能特性 -->
    <section class="features">
      <div class="container">
        <div class="features-grid">
          <div 
            v-for="(feature, index) in features" 
            :key="index"
            class="feature-card"
            :style="{ animationDelay: index * 0.1 + 's' }"
          >
            <div class="feature-icon" :style="feature.iconStyle">
              <IconBase :name="feature.icon" :size="28" />
            </div>
            <h3 class="feature-title">{{ feature.title }}</h3>
            <p class="feature-desc">{{ feature.desc }}</p>
          </div>
        </div>
      </div>
    </section>

    <!-- 最近项目 -->
    <section class="recent-projects">
      <div class="container">
        <div class="section-header">
          <h2 class="section-title">最近项目</h2>
          <router-link to="/dashboard" class="section-link">
            查看全部 <IconBase name="arrowRight" :size="14" />
          </router-link>
        </div>
        <div class="projects-grid">
          <div 
            v-for="project in recentProjects" 
            :key="project.id"
            class="project-card"
            @click="openProject(project)"
          >
            <div class="project-thumbnail" :style="{ background: project.gradient }">
              <div class="project-overlay">
                <button class="btn btn-primary btn-sm" @click.stop="editProject(project)">
                  <IconBase name="edit" :size="12" />
                  编辑
                </button>
              </div>
            </div>
            <div class="project-info">
              <h3 class="project-title">{{ project.title }}</h3>
              <div class="project-meta">
                <span class="project-time">
                  <IconBase name="clock" :size="12" />
                  {{ project.time }}
                </span>
                <span class="project-status tag" :class="'tag-' + project.statusType">
                  {{ project.status }}
                </span>
              </div>
            </div>
          </div>
          <!-- 新建卡片 -->
          <div class="project-card project-card-new" @click="openModal">
            <div class="project-new-content">
              <div class="project-new-icon">
                <IconBase name="plus" :size="24" />
              </div>
              <span class="project-new-text">新建PPT</span>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- 热门模板 -->
    <section class="templates">
      <div class="container">
        <div class="section-header">
          <h2 class="section-title">热门模板</h2>
          <router-link to="/templates" class="section-link">
            浏览全部 <IconBase name="arrowRight" :size="14" />
          </router-link>
        </div>
        <div class="template-tabs">
          <button 
            v-for="tab in templateTabs" 
            :key="tab"
            :class="['tab-btn', { active: activeTab === tab }]"
            @click="activeTab = tab"
          >
            {{ tab }}
          </button>
        </div>
        <div class="templates-grid">
          <div 
            v-for="template in templates" 
            :key="template.id"
            class="template-card"
            @click="applyTemplate(template)"
          >
            <div class="template-preview" :style="{ background: template.gradient }">
              <div v-if="template.badge" class="template-badge">{{ template.badge }}</div>
            </div>
            <div class="template-info">
              <h4 class="template-name">{{ template.name }}</h4>
              <p class="template-usage">使用 {{ template.usage }} 次</p>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- 页脚 -->
    <footer class="footer">
      <div class="container">
        <div class="footer-content">
          <div class="footer-brand">
            <img src="/images/slideon-icon.png" alt="Slideon" class="logo-icon-img" />
            <span class="logo-text">Slideon</span>
            <p class="footer-desc">智能PPT生成，让创作更高效</p>
          </div>
          <div class="footer-links">
            <div class="footer-column">
              <h4>产品</h4>
              <a href="#">功能介绍</a>
              <a href="#">模板库</a>
              <a href="#">价格方案</a>
            </div>
            <div class="footer-column">
              <h4>支持</h4>
              <a href="#">帮助中心</a>
              <a href="#">使用教程</a>
              <a href="#">联系我们</a>
            </div>
            <div class="footer-column">
              <h4>关于</h4>
              <a href="#">关于我们</a>
              <a href="#">隐私政策</a>
              <a href="#">服务条款</a>
            </div>
          </div>
        </div>
        <div class="footer-bottom">
          <p>&copy; 2024 Slideon. All rights reserved.</p>
        </div>
      </div>
    </footer>

    <!-- AI大纲生成对话框 -->
    <OutlineModal v-model="showModal" />
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import AppHeader from '../components/common/AppHeader.vue'
import OutlineModal from '../components/common/OutlineModal.vue'
import IconBase from '../components/icons/IconBase.vue'

const router = useRouter()
const showModal = ref(false)
const activeTab = ref('全部')

const features = [
  {
    icon: 'robot',
    title: 'AI大纲生成',
    desc: '输入主题，AI智能分析并生成完整PPT大纲结构',
    iconStyle: { background: 'var(--primary-100)', color: 'var(--primary-600)' }
  },
  {
    icon: 'magic',
    title: '智能内容填充',
    desc: '基于大纲自动生成专业内容，支持多种风格',
    iconStyle: { background: 'var(--success-100)', color: 'var(--success-600)' }
  },
  {
    icon: 'thLarge',
    title: '丰富模板库',
    desc: '100+精美模板，覆盖商务、教育、创意等场景',
    iconStyle: { background: 'var(--warning-100)', color: 'var(--warning-600)' }
  },
  {
    icon: 'robot',
    title: '知识增强RAG',
    desc: '上传文档，AI基于您的资料生成个性化内容',
    iconStyle: { background: 'var(--info-100)', color: 'var(--info-600)' }
  }
]

const recentProjects = [
  {
    id: 1,
    title: '2024年度产品发布会',
    time: '2天前',
    status: '进行中',
    statusType: 'primary',
    gradient: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
  },
  {
    id: 2,
    title: '年终总结报告',
    time: '1周前',
    status: '已完成',
    statusType: 'success',
    gradient: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)'
  },
  {
    id: 3,
    title: '新员工培训计划',
    time: '2周前',
    status: '已完成',
    statusType: 'success',
    gradient: 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)'
  },
  {
    id: 4,
    title: '市场推广方案',
    time: '1月前',
    status: '已完成',
    statusType: 'success',
    gradient: 'linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)'
  }
]

const templateTabs = ['全部', '商务', '教育', '创意', '科技']

const templates = [
  { id: 1, name: '商务汇报', usage: '2,341', badge: '热门', gradient: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' },
  { id: 2, name: '产品发布', usage: '1,892', badge: '新品', gradient: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)' },
  { id: 3, name: '科技风', usage: '1,567', badge: '', gradient: 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)' },
  { id: 4, name: '教育培训', usage: '1,234', badge: '', gradient: 'linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)' }
]

const openModal = () => {
  showModal.value = true
}

const openProject = (project) => {
  console.log('打开项目:', project.title)
}

const editProject = (project) => {
  router.push('/editor/' + project.id)
}

const applyTemplate = (template) => {
  console.log('应用模板:', template.name)
  router.push('/editor')
}
</script>

<style scoped>
.home {
  padding-top: 64px;
}

/* Hero区域 */
.hero {
  padding: 80px 0;
  background: linear-gradient(180deg, white 0%, var(--gray-50) 100%);
  text-align: center;
}

.hero-content {
  max-width: 800px;
  margin: 0 auto;
}

.hero-title {
  font-size: 48px;
  font-weight: 700;
  color: var(--gray-800);
  line-height: 1.2;
  margin-bottom: var(--space-4);
  background: linear-gradient(135deg, var(--gray-800) 0%, var(--primary-600) 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.hero-subtitle {
  font-size: 18px;
  color: var(--gray-500);
  margin-bottom: var(--space-8);
}

.btn-xl {
  height: 64px;
  padding: 0 var(--space-10);
  font-size: 18px;
  font-weight: 600;
  gap: var(--space-3);
  box-shadow: var(--shadow-lg);
  transition: all 0.3s ease;
}

.btn-xl:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-xl);
}



/* 功能特性 */
.features {
  padding: 80px 0;
  background: white;
}

.features-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: var(--space-6);
}

.feature-card {
  text-align: center;
  padding: var(--space-8) var(--space-6);
  background: white;
  border-radius: var(--radius-xl);
  border: 1px solid var(--gray-100);
  transition: all 0.3s ease;
  animation: slideUp 0.5s ease backwards;
}

.feature-card:hover {
  transform: translateY(-4px);
  box-shadow: var(--shadow-lg);
  border-color: var(--primary-200);
}

.feature-icon {
  width: 64px;
  height: 64px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--radius-lg);
  margin: 0 auto var(--space-5);
}

.feature-title {
  font-size: 18px;
  font-weight: 600;
  color: var(--gray-800);
  margin-bottom: var(--space-2);
}

.feature-desc {
  font-size: 14px;
  color: var(--gray-500);
  line-height: 1.6;
}

/* 最近项目 */
.recent-projects {
  padding: 80px 0;
  background: var(--gray-50);
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--space-8);
}

.section-title {
  font-size: 24px;
  font-weight: 600;
  color: var(--gray-800);
}

.section-link {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  font-size: 14px;
  font-weight: 500;
  color: var(--primary-600);
  transition: color 0.2s ease;
}

.section-link:hover {
  color: var(--primary-700);
}

.projects-grid {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: var(--space-6);
}

.project-card {
  background: white;
  border-radius: var(--radius-lg);
  overflow: hidden;
  box-shadow: var(--shadow-md);
  transition: all 0.2s ease;
  cursor: pointer;
}

.project-card:hover {
  transform: translateY(-4px);
  box-shadow: var(--shadow-lg);
}

.project-thumbnail {
  position: relative;
  height: 135px;
  overflow: hidden;
}

.project-overlay {
  position: absolute;
  inset: 0;
  background: rgba(0, 0, 0, 0.4);
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  transition: opacity 0.2s ease;
}

.project-card:hover .project-overlay {
  opacity: 1;
}

.project-info {
  padding: var(--space-4);
}

.project-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--gray-800);
  margin-bottom: var(--space-2);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.project-meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.project-time {
  font-size: 12px;
  color: var(--gray-500);
  display: flex;
  align-items: center;
  gap: var(--space-1);
}

.project-status {
  font-size: 11px;
  padding: 2px 8px;
}

/* 新建项目卡片 */
.project-card-new {
  border: 2px dashed var(--gray-300);
  background: transparent;
  box-shadow: none;
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 219px;
}

.project-card-new:hover {
  border-color: var(--primary-400);
  background: var(--primary-50);
  transform: translateY(-4px);
}

.project-new-content {
  text-align: center;
}

.project-new-icon {
  width: 56px;
  height: 56px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--gray-100);
  border-radius: var(--radius-full);
  margin: 0 auto var(--space-3);
  color: var(--gray-500);
  transition: all 0.2s ease;
}

.project-card-new:hover .project-new-icon {
  background: var(--primary-100);
  color: var(--primary-600);
}

.project-new-text {
  font-size: 14px;
  font-weight: 500;
  color: var(--gray-600);
}

/* 热门模板 */
.templates {
  padding: 80px 0;
  background: white;
}

.template-tabs {
  display: flex;
  gap: var(--space-2);
  margin-bottom: var(--space-8);
}

.tab-btn {
  padding: var(--space-2) var(--space-5);
  font-size: 14px;
  font-weight: 500;
  color: var(--gray-600);
  background: transparent;
  border: none;
  border-radius: var(--radius-full);
  cursor: pointer;
  transition: all 0.2s ease;
}

.tab-btn:hover {
  color: var(--gray-800);
  background: var(--gray-100);
}

.tab-btn.active {
  color: var(--primary-600);
  background: var(--primary-50);
}

.templates-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: var(--space-6);
}

.template-card {
  cursor: pointer;
  transition: transform 0.2s ease;
}

.template-card:hover {
  transform: translateY(-4px);
}

.template-preview {
  position: relative;
  height: 160px;
  border-radius: var(--radius-lg);
  overflow: hidden;
  box-shadow: var(--shadow-md);
  margin-bottom: var(--space-3);
}

.template-badge {
  position: absolute;
  top: var(--space-3);
  right: var(--space-3);
  padding: var(--space-1) var(--space-3);
  font-size: 11px;
  font-weight: 600;
  color: white;
  background: var(--error-500);
  border-radius: var(--radius-full);
}

.template-info {
  padding: 0 var(--space-1);
}

.template-name {
  font-size: 15px;
  font-weight: 600;
  color: var(--gray-800);
  margin-bottom: var(--space-1);
}

.template-usage {
  font-size: 13px;
  color: var(--gray-500);
}

/* 页脚 */
.footer {
  padding: 60px 0 0;
  background: var(--gray-800);
  color: white;
}

.footer-content {
  display: flex;
  justify-content: space-between;
  margin-bottom: var(--space-12);
}

.footer-brand {
  max-width: 300px;
}

.footer-brand .logo-icon,
.footer-brand .logo-text {
  color: white;
  font-size: 24px;
  font-weight: 700;
}

.footer-brand .logo-icon {
  margin-right: var(--space-2);
}

.footer-brand .logo-icon-img {
  width: 32px;
  height: 32px;
  margin-right: var(--space-2);
  vertical-align: middle;
}

.footer-desc {
  margin-top: var(--space-3);
  font-size: 14px;
  color: var(--gray-400);
}

.footer-links {
  display: flex;
  gap: var(--space-16);
}

.footer-column h4 {
  font-size: 14px;
  font-weight: 600;
  margin-bottom: var(--space-4);
  color: white;
}

.footer-column a {
  display: block;
  font-size: 14px;
  color: var(--gray-400);
  margin-bottom: var(--space-3);
  transition: color 0.2s ease;
}

.footer-column a:hover {
  color: white;
}

.footer-bottom {
  padding: var(--space-6) 0;
  border-top: 1px solid var(--gray-700);
  text-align: center;
  font-size: 13px;
  color: var(--gray-500);
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

/* 响应式 */
@media (max-width: 1200px) {
  .projects-grid {
    grid-template-columns: repeat(4, 1fr);
  }
}

@media (max-width: 1024px) {
  .features-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .projects-grid {
    grid-template-columns: repeat(3, 1fr);
  }
  
  .templates-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .search-input-large {
    width: 400px;
  }
}

@media (max-width: 768px) {
  .hero-title {
    font-size: 32px;
  }
  
  .hero-search {
    flex-direction: column;
    align-items: center;
  }
  
  .search-input-large {
    width: 100%;
  }
  
  .features-grid {
    grid-template-columns: 1fr;
  }
  
  .projects-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .footer-content {
    flex-direction: column;
    gap: var(--space-8);
  }
  
  .footer-links {
    flex-wrap: wrap;
  }
}
</style>
