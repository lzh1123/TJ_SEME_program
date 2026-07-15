<template>
  <div class="radar-chart-container">
    <svg :viewBox="`0 0 ${size} ${size}`" :width="size" :height="size">
      <polygon
        v-for="level in 5"
        :key="level"
        :points="getPolygonPoints(level / 5)"
        fill="none"
        :stroke="level === 5 ? '#d1d5db' : '#e5e7eb'"
        stroke-width="1"
      />
      <line
        v-for="(_, i) in axes"
        :key="'axis-' + i"
        :x1="cx"
        :y1="cy"
        :x2="getPoint(i, 1).x"
        :y2="getPoint(i, 1).y"
        stroke="#e5e7eb"
        stroke-width="1"
      />
      <polygon
        :points="dataPoints"
        fill="rgba(99,102,241,0.2)"
        stroke="#6366f1"
        stroke-width="2"
      />
      <circle
        v-for="(_, i) in axes"
        :key="'dot-' + i"
        :cx="getPoint(i, values[i] / maxVal).x"
        :cy="getPoint(i, values[i] / maxVal).y"
        r="4"
        fill="#6366f1"
      />
      <text
        v-for="(axis, i) in axes"
        :key="'label-' + i"
        :x="getLabelPoint(i).x"
        :y="getLabelPoint(i).y"
        text-anchor="middle"
        dominant-baseline="middle"
        fill="#6b7280"
        font-size="11"
      >{{ axis }}</text>
    </svg>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  axes: { type: Array, required: true },
  values: { type: Array, required: true },
  maxVal: { type: Number, default: 10 },
  size: { type: Number, default: 300 }
})

const cx = computed(() => props.size / 2)
const cy = computed(() => props.size / 2)
const radius = computed(() => props.size * 0.35)

function getPoint(index, ratio) {
  const angle = (Math.PI * 2 * index) / props.axes.length - Math.PI / 2
  return {
    x: cx.value + radius.value * Math.cos(angle) * ratio,
    y: cy.value + radius.value * Math.sin(angle) * ratio
  }
}

function getLabelPoint(index) {
  return getPoint(index, 1.2)
}

function getPolygonPoints(ratio) {
  return Array.from({ length: props.axes.length }, (_, i) => {
    const p = getPoint(i, ratio)
    return `${p.x},${p.y}`
  }).join(' ')
}

const dataPoints = computed(() => {
  return Array.from({ length: props.axes.length }, (_, i) => {
    const v = Math.min((props.values[i] || 0) / props.maxVal, 1)
    const p = getPoint(i, v)
    return `${p.x},${p.y}`
  }).join(' ')
})
</script>

<style scoped>
.radar-chart-container { display:flex; justify-content:center; }
</style>
