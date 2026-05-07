<template>
  <svg
    :width="size"
    :height="size"
    viewBox="0 0 24 24"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
    :class="['icon', `icon-${name}`]"
  >
    <component :is="iconComponent" />
  </svg>
</template>

<script setup>
import { computed } from 'vue'
import * as icons from './icons'

const props = defineProps({
  name: {
    type: String,
    required: true
  },
  size: {
    type: [Number, String],
    default: 24
  }
})

const iconComponent = computed(() => {
  return icons[props.name] || icons['help']
})
</script>

<style scoped>
.icon {
  display: inline-block;
  vertical-align: middle;
  flex-shrink: 0;
}
</style>
