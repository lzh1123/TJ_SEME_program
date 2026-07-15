<template>
  <div class="batch-eval-page">
    <header class="eval-page-header">
      <router-link to="/dashboard" class="btn btn-ghost btn-icon">
        <IconBase name="arrowLeft" :size="18" />
      </router-link>
      <h1>批量评估</h1>
    </header>

    <div class="eval-container">
      <section class="config-section">
        <h2>评估配置</h2>

        <div class="form-group">
          <label>评估主题（一行一个）</label>
          <textarea v-model="topicsText" rows="5" placeholder="新能源汽车行业分析
企业数字化转型战略
人工智能技术发展趋势"></textarea>
        </div>

        <div class="form-group">
          <label>RAG 配置</label>
          <div class="config-row">
            <label class="checkbox-label">
              <input type="checkbox" v-model="configs[0].useRag" /> RAG 启用 (配置A)
            </label>
            <label class="checkbox-label">
              <input type="checkbox" v-model="configs[1].useRag" /> RAG 启用 (配置B)
            </label>
          </div>
        </div>

        <div class="form-group">
          <label>评估指标</label>
          <div class="metric-checkboxes">
            <label v-for="m in availableMetrics" :key="m.value" class="checkbox-label">
              <input type="checkbox" :value="m.value" v-model="selectedMetrics" /> {{ m.label }}
            </label>
          </div>
        </div>

        <button class="btn btn-primary btn-lg" @click="runBatch" :disabled="running">
          <IconBase v-if="running" name="spinner" :size="16" class="animate-spin" />
          {{ running ? '评估中...' : '开始批量评估' }}
        </button>
      </section>

      <section v-if="batchResults" class="results-section">
        <h2>评估结果</h2>

        <div class="results-table-wrapper">
          <table class="results-table">
            <thead>
              <tr>
                <th>配置</th>
                <th>主题</th>
                <th>综合评分</th>
                <th>结构完整性</th>
                <th>信息密度</th>
                <th>RAG 召回率</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(r, i) in batchResults.results" :key="i">
                <td><span class="config-badge">{{ r.config }}</span></td>
                <td>{{ r.topic }}</td>
                <td><strong>{{ r.overall_score }}</strong></td>
                <td>{{ formatPct(r.rule_metrics?.structure_completeness) }}</td>
                <td>{{ formatPct(r.rule_metrics?.information_density?.score) }}</td>
                <td>{{ formatPct(r.rule_metrics?.rag_recall) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import IconBase from '../components/icons/IconBase.vue'
import { apiService } from '../services/api.js'

const topicsText = ref('新能源汽车行业分析\n企业数字化转型战略\n人工智能技术发展趋势')
const configs = ref([{ name: 'RAG_ON', useRag: true }, { name: 'RAG_OFF', useRag: false }])
const selectedMetrics = ref(['structure', 'density', 'bleu', 'rag_recall', 'llm_judge'])
const running = ref(false)
const batchResults = ref(null)

const availableMetrics = [
  { value: 'structure', label: '结构完整性' },
  { value: 'density', label: '信息密度' },
  { value: 'diversity', label: '内容多样性' },
  { value: 'bleu', label: 'BLEU 分数' },
  { value: 'rouge', label: 'ROUGE-L' },
  { value: 'rag_recall', label: 'RAG 召回率' },
  { value: 'llm_judge', label: 'LLM 评估' },
]

async function runBatch() {
  const topics = topicsText.value.split('\n').map(s => s.trim()).filter(Boolean)
  if (topics.length === 0) { alert('请输入至少一个评估主题'); return }

  running.value = true
  try {
    batchResults.value = await apiService.batchEvaluate({
      configs: configs.value.map(c => ({ name: c.name, use_rag: c.useRag })),
      topics,
      metrics: selectedMetrics.value,
      reference_texts: {}
    })
  } catch (e) {
    console.error('Batch evaluation failed:', e)
  } finally {
    running.value = false
  }
}

function formatPct(v) {
  if (v == null) return '—'
  return (v * 100).toFixed(1) + '%'
}
</script>

<style scoped>
.batch-eval-page { min-height:100vh; background:#f9fafb; }
.eval-page-header { display:flex; align-items:center; gap:12px; padding:16px 24px; background:white; border-bottom:1px solid #e5e7eb; position:sticky; top:0; z-index:10; }
.eval-page-header h1 { font-size:20px; font-weight:600; color:#1f2937; margin:0; }
.eval-container { max-width:900px; margin:0 auto; padding:32px 24px; display:flex; flex-direction:column; gap:32px; }
.config-section { background:white; border-radius:16px; padding:24px; border:1px solid #e5e7eb; }
.config-section h2, .results-section h2 { font-size:18px; font-weight:600; color:#1f2937; margin:0 0 20px; }
.form-group { margin-bottom:20px; }
.form-group label { display:block; font-size:13px; font-weight:600; color:#374151; margin-bottom:8px; }
.form-group textarea { width:100%; padding:12px; border:1px solid #d1d5db; border-radius:8px; font-size:14px; font-family:inherit; resize:vertical; }
.config-row, .metric-checkboxes { display:flex; gap:16px; flex-wrap:wrap; }
.checkbox-label { display:flex; align-items:center; gap:6px; font-size:14px; color:#374151; cursor:pointer; }
.results-section { background:white; border-radius:16px; padding:24px; border:1px solid #e5e7eb; }
.results-table-wrapper { overflow-x:auto; }
.results-table { width:100%; border-collapse:collapse; font-size:13px; }
.results-table th { text-align:left; padding:10px 12px; background:#f9fafb; color:#6b7280; font-weight:600; border-bottom:2px solid #e5e7eb; }
.results-table td { padding:10px 12px; border-bottom:1px solid #f3f4f6; color:#374151; }
.config-badge { display:inline-block; padding:2px 10px; background:#eef2ff; color:#4f46e5; border-radius:999px; font-size:12px; font-weight:500; }
</style>
