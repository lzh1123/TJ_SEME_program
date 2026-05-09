<template>
  <div class="templates-page">
    <AppHeader />
    <div class="container">
      <h1>模板库</h1>
      <p>浏览我们精选的PPT模板</p>
    </div>
  </div>
</template>

<script setup>
import AppHeader from '../components/common/AppHeader.vue'
</script>

<style scoped>
.templates-page {
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
