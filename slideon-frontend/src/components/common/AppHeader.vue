<template>
  <header class="header" :style="headerStyle">
    <div class="container header-content">
      <div class="header-left">
        <router-link to="/" class="logo">
          <img src="/images/slideon-icon.png" alt="Slideon" class="logo-icon-img" />
          <span class="logo-text">Slideon</span>
        </router-link>
        <nav class="nav">
          <router-link 
            v-for="item in navItems" 
            :key="item.path"
            :to="item.path" 
            :class="['nav-link', { active: isActive(item.path) }]"
          >
            {{ item.name }}
          </router-link>
        </nav>
      </div>
      <div class="header-right">
        <div class="search-box">
          <IconBase name="search" :size="14" class="search-icon" />
          <input 
            type="text" 
            class="search-input" 
            placeholder="搜索..."
            v-model="searchQuery"
            @keypress.enter="handleSearch"
          >
        </div>
        <button class="btn btn-primary" @click="$emit('create-ppt')">
          <IconBase name="plus" :size="14" />
          新建PPT
        </button>
        <div class="user-avatar">
          <img :src="userAvatar" alt="用户头像">
        </div>
      </div>
    </div>
  </header>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import IconBase from '../icons/IconBase.vue'

const route = useRoute()
const searchQuery = ref('')
const scrollY = ref(0)

const navItems = [
  { name: '首页', path: '/' },
  { name: '模板库', path: '/templates' },
  { name: '我的PPT', path: '/dashboard' }
]

const userAvatar = 'https://api.dicebear.com/7.x/avataaars/svg?seed=user'

const isActive = (path) => {
  if (path === '/') {
    return route.path === '/'
  }
  return route.path.startsWith(path)
}

const headerStyle = computed(() => ({
  boxShadow: scrollY.value > 10 ? 'var(--shadow-md)' : 'var(--shadow-sm)'
}))

const handleScroll = () => {
  scrollY.value = window.scrollY
}

const handleSearch = () => {
  if (searchQuery.value.trim()) {
    // 处理搜索逻辑
    console.log('搜索:', searchQuery.value)
  }
}

onMounted(() => {
  window.addEventListener('scroll', handleScroll)
})

onUnmounted(() => {
  window.removeEventListener('scroll', handleScroll)
})

defineEmits(['create-ppt'])
</script>

<style scoped>
.header {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  height: 64px;
  background: white;
  border-bottom: 1px solid var(--gray-200);
  z-index: 1000;
  transition: box-shadow 0.2s ease;
}

.header-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 100%;
}

.header-left {
  display: flex;
  align-items: center;
  gap: var(--space-12);
}

.logo {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  font-size: 24px;
  font-weight: 700;
  color: var(--primary-600);
}

.logo-icon-img {
  width: 32px;
  height: 32px;
  vertical-align: middle;
}

.nav {
  display: flex;
  gap: var(--space-8);
}

.nav-link {
  font-size: 15px;
  font-weight: 500;
  color: var(--gray-600);
  padding: var(--space-2) 0;
  transition: color 0.2s ease;
  position: relative;
}

.nav-link:hover,
.nav-link.active {
  color: var(--primary-600);
}

.nav-link.active::after {
  content: '';
  position: absolute;
  bottom: -4px;
  left: 0;
  right: 0;
  height: 2px;
  background: var(--primary-500);
  border-radius: var(--radius-full);
}

.header-right {
  display: flex;
  align-items: center;
  gap: var(--space-4);
}

.search-box {
  position: relative;
  width: 240px;
}

.search-icon {
  position: absolute;
  left: var(--space-3);
  top: 50%;
  transform: translateY(-50%);
  color: var(--gray-400);
}

.search-input {
  width: 100%;
  height: 36px;
  padding: 0 var(--space-4) 0 var(--space-10);
  font-size: 13px;
  border: 1px solid var(--gray-200);
  border-radius: var(--radius-full);
  background: var(--gray-50);
  transition: all 0.2s ease;
}

.search-input:focus {
  background: white;
  border-color: var(--primary-300);
  box-shadow: 0 0 0 3px var(--primary-100);
}

.user-avatar {
  width: 36px;
  height: 36px;
  border-radius: var(--radius-full);
  overflow: hidden;
  cursor: pointer;
  border: 2px solid var(--gray-200);
  transition: border-color 0.2s ease;
}

.user-avatar:hover {
  border-color: var(--primary-300);
}

.user-avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

@media (max-width: 768px) {
  .nav {
    display: none;
  }
  
  .search-box {
    width: 160px;
  }
}
</style>
