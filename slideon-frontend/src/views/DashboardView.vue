<template>
  <div class="dashboard-page">
    <AppHeader />
    <div class="container">
      <h1>我的PPT</h1>
      <p>管理您的所有PPT项目</p>
    </div>
  </div>
</template>

<script setup>
import AppHeader from '../components/common/AppHeader.vue'
</script>

<style scoped>
.dashboard-page {
  padding-top: 64px;
}

.container {
  padding: 40px var(--space-16);
}

h1 {
  font-size: 32px;
  font-weight: 700;
  color: var(--gray-800);
  margin-bottom: var(--space-4);
}

p {
  color: var(--gray-500);
}
</style>
