<template>
  <div class="eval-panel">
    <div class="eval-header">
      <h3>质量评估</h3>
      <button class="btn btn-sm btn-primary" @click="runEvaluation" :disabled="evaluating">
        <IconBase v-if="evaluating" name="spinner" :size="12" class="animate-spin" />
        开始评估
      </button>
    </div>

    <div v-if="result" class="eval-results">
      <RadarChart
        v-if="radarData"
        :axes="radarData.axes"
        :values="radarData.values"
        :maxVal="10"
        :size="260"
      />

      <div class="metrics-grid">
        <MetricCard
          label="结构完整性"
          :score="result.rule_metrics.structure_completeness"
          :maxScore="1"
          :detail="structureDetail"
        />
        <MetricCard
          label="信息密度"
          :score="result.rule_metrics.information_density?.score || 0"
          :maxScore="1"
          :detail="densityDetail"
        />
        <MetricCard
          label="内容多样性"
          :score="result.rule_metrics.content_diversity?.ttr || 0"
          :maxScore="1"
          :detail="diversityDetail"
        />
        <MetricCard
          v-if="result.rule_metrics.rag_recall != null"
          label="RAG 召回率"
          :score="result.rule_metrics.rag_recall"
          :maxScore="1"
        />
      </div>

      <div v-if="result.llm_judge_metrics" class="llm-scores">
        <h4>AI 综合评分</h4>
        <div class="metrics-grid">
          <MetricCard
            label="结构合理性"
            :score="result.llm_judge_metrics.structure_rationality || 0"
            :maxScore="10"
          />
          <MetricCard
            label="事实准确率"
            :score="result.llm_judge_metrics.fact_accuracy || 0"
            :maxScore="10"
          />
          <MetricCard
            label="逻辑连贯性"
            :score="result.llm_judge_metrics.logical_coherence || 0"
            :maxScore="10"
          />
          <MetricCard
            label="内容深度"
            :score="result.llm_judge_metrics.content_depth || 0"
            :maxScore="10"
          />
        </div>
      </div>

      <div class="overall-score">
        <span class="overall-label">综合评分</span>
        <span class="overall-value">{{ result.overall_score }}</span>
        <span class="overall-unit">/ 10</span>
      </div>

      <div v-if="result.suggestions?.length" class="suggestions">
        <h4>改进建议</h4>
        <ul>
          <li v-for="(s, i) in result.suggestions" :key="i">{{ s }}</li>
        </ul>
      </div>
    </div>

    <div v-else-if="!evaluating" class="eval-empty">
      <IconBase name="chart" :size="40" />
      <p>点击「开始评估」对当前大纲进行质量分析</p>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import IconBase from '../icons/IconBase.vue'
import RadarChart from './RadarChart.vue'
import MetricCard from './MetricCard.vue'
import { apiService } from '../../services/api.js'

const props = defineProps({
  presentationId: { type: String, default: '' }
})

const result = ref(null)
const evaluating = ref(false)

const radarData = computed(() => {
  if (!result.value) return null
  const r = result.value
  const axes = ['结构', '信息密度', '多样性', '结构合理', '逻辑']
  const values = [
    (r.rule_metrics.structure_completeness || 0) * 10,
    (r.rule_metrics.information_density?.score || 0) * 10,
    (r.rule_metrics.content_diversity?.ttr || 0) * 10,
    r.llm_judge_metrics?.structure_rationality || 0,
    r.llm_judge_metrics?.logical_coherence || 0,
  ]
  return { axes, values }
})

const structureDetail = computed(() => {
  if (!result.value) return ''
  return `得分: ${(result.value.rule_metrics.structure_completeness * 100).toFixed(0)}%`
})

const densityDetail = computed(() => {
  const d = result.value?.rule_metrics?.information_density
  if (!d) return ''
  return `平均 ${d.avg_bullets_per_slide} 要点/页, ${d.avg_words_per_slide} 词/页`
})

const diversityDetail = computed(() => {
  const d = result.value?.rule_metrics?.content_diversity
  if (!d) return ''
  return `${d.unique_terms} 不同词 / ${d.total_terms} 总词数`
})

async function runEvaluation() {
  evaluating.value = true
  try {
    result.value = await apiService.evaluatePresentation(props.presentationId, {
      enableLLMJudge: true
    })
  } catch (e) {
    console.error('Evaluation failed:', e)
  } finally {
    evaluating.value = false
  }
}
</script>

<style scoped>
.eval-panel { padding:20px; }
.eval-header { display:flex; align-items:center; justify-content:space-between; margin-bottom:20px; }
.eval-header h3 { font-size:16px; font-weight:600; color:#1f2937; margin:0; }
.eval-empty { text-align:center; padding:40px 20px; color:#9ca3af; }
.eval-empty p { font-size:14px; margin-top:12px; }
.eval-results { display:flex; flex-direction:column; gap:20px; }
.metrics-grid { display:grid; grid-template-columns:1fr 1fr; gap:10px; }
.llm-scores h4 { font-size:14px; font-weight:600; color:#374151; margin:0 0 10px; }
.overall-score { display:flex; align-items:baseline; justify-content:center; gap:8px; padding:20px; background:linear-gradient(135deg,#6366f1,#8b5cf6); border-radius:12px; color:white; }
.overall-label { font-size:14px; opacity:.9; }
.overall-value { font-size:36px; font-weight:700; }
.overall-unit { font-size:14px; opacity:.7; }
.suggestions { background:#fffbeb; border:1px solid #fcd34d; border-radius:10px; padding:16px; }
.suggestions h4 { font-size:14px; font-weight:600; color:#92400e; margin:0 0 8px; }
.suggestions ul { margin:0; padding-left:20px; }
.suggestions li { font-size:13px; color:#78350f; margin-bottom:4px; }
</style>
