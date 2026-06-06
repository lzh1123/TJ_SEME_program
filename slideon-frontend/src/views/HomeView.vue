<template>
  <div class="home">
    <AppHeader @create-outline="openModal" />
    
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
import AppHeader from '../components/common/AppHeader.vue'
import OutlineModal from '../components/common/OutlineModal.vue'
import IconBase from '../components/icons/IconBase.vue'

const showModal = ref(false)

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
    icon: 'images',
    title: '丰富的幻灯片类型',
    desc: '支持15种幻灯片布局，覆盖封面、图表、时间线、SWOT等',
    iconStyle: { background: 'var(--warning-100)', color: 'var(--warning-600)' }
  },
  {
    icon: 'robot',
    title: '知识增强RAG',
    desc: '上传文档，AI基于您的资料生成个性化内容',
    iconStyle: { background: 'var(--info-100)', color: 'var(--info-600)' }
  }
]

const openModal = () => {
  showModal.value = true
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
@media (max-width: 1024px) {
  .features-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 768px) {
  .hero-title {
    font-size: 32px;
  }

  .features-grid {
    grid-template-columns: 1fr;
  }
}
</style>
