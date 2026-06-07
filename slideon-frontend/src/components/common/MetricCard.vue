<template>
  <div class="metric-card" :class="colorClass">
    <div class="metric-header">
      <span class="metric-label">{{ label }}</span>
      <span class="metric-score">{{ displayScore }}</span>
    </div>
    <div class="metric-bar">
      <div class="metric-fill" :style="{ width: fillPercent + '%' }"></div>
    </div>
    <div v-if="detail" class="metric-detail">{{ detail }}</div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  label: { type: String, required: true },
  score: { type: Number, default: 0 },
  maxScore: { type: Number, default: 10 },
  detail: { type: String, default: '' }
})

const fillPercent = computed(() => Math.min((props.score / props.maxScore) * 100, 100))
const displayScore = computed(() => {
  if (props.maxScore <= 1) return (props.score * 100).toFixed(0) + '%'
  if (Number.isInteger(props.score)) return String(props.score)
  return props.score.toFixed(1)
})

const colorClass = computed(() => {
  const pct = fillPercent.value
  if (pct >= 70) return 'good'
  if (pct >= 40) return 'warn'
  return 'poor'
})
</script>

<style scoped>
.metric-card { padding:12px 16px; border-radius:10px; background:#f9fafb; border:1px solid #e5e7eb; }
.metric-header { display:flex; justify-content:space-between; align-items:center; margin-bottom:8px; }
.metric-label { font-size:13px; font-weight:600; color:#374151; }
.metric-score { font-size:16px; font-weight:700; }
.metric-bar { height:6px; background:#e5e7eb; border-radius:3px; overflow:hidden; }
.metric-fill { height:100%; border-radius:3px; transition:width .5s ease; }
.metric-detail { font-size:11px; color:#9ca3af; margin-top:6px; }
.good .metric-score { color:#059669; }
.good .metric-fill { background:linear-gradient(90deg,#10b981,#34d399); }
.warn .metric-score { color:#d97706; }
.warn .metric-fill { background:linear-gradient(90deg,#f59e0b,#fbbf24); }
.poor .metric-score { color:#dc2626; }
.poor .metric-fill { background:linear-gradient(90deg,#ef4444,#f87171); }
</style>
