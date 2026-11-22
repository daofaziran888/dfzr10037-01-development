<template>
  <section class="page" data-module="lineage_impact">
    <header class="page-head">
      <div>
        <h2>血缘影响分析</h2>
        <p class="page-desc">
          从待下线的血缘边出发，按最近影响层列出下游实体；只有全链路已确认的实体计入确认影响，
          仅待验证路径支撑的实体标为待验证支路，取证时一并带出待查血缘。
        </p>
      </div>
      <div class="page-actions">
        <button class="btn" data-testid="impact-query" type="button" @click="reload">重新分析</button>
        <button class="btn primary" data-testid="impact-sample" type="button" @click="submitSample" :disabled="submitting">
          {{ submitting ? '提交中…' : '生成分层影响样本' }}
        </button>
      </div>
    </header>

    <form class="filter-bar" @submit.prevent="reload">
      <label class="filter-item">
        <span>源头实体</span>
        <input v-model="source" data-testid="impact-source" placeholder="留空则取待下线链路的上游实体" />
      </label>
      <label class="filter-item">
        <span>待下线链路编号</span>
        <input v-model="exclude" data-testid="impact-exclude" placeholder="多个用逗号分隔，留空取已废弃链路" />
      </label>
      <button class="btn" type="submit">查询</button>
      <button class="btn ghost" type="button" @click="reset">重置条件</button>
    </form>

    <p v-if="message" class="impact-message" data-testid="impact-message">{{ message }}</p>
    <p v-if="errorMessage" class="error-text">{{ errorMessage }}</p>

    <div v-if="analysis" class="stat-row">
      <article class="stat-card">
        <span class="stat-label">受影响实体</span>
        <strong class="stat-value" data-testid="summary-total">{{ analysis.摘要.实体总数 }}</strong>
      </article>
      <article class="stat-card">
        <span class="stat-label">确认影响</span>
        <strong class="stat-value" data-testid="summary-confirmed">{{ analysis.摘要.确认影响数 }}</strong>
      </article>
      <article class="stat-card">
        <span class="stat-label">待验证支路</span>
        <strong class="stat-value" data-testid="summary-pending">{{ analysis.摘要.待验证支路数 }}</strong>
      </article>
      <article class="stat-card">
        <span class="stat-label">口径冲突</span>
        <strong class="stat-value" data-testid="summary-conflict">{{ analysis.摘要.口径冲突数 }}</strong>
      </article>
      <article class="stat-card">
        <span class="stat-label">循环回边</span>
        <strong class="stat-value" data-testid="summary-cycle">{{ analysis.摘要.循环回边数 }}</strong>
      </article>
    </div>

    <section v-if="analysis" class="impact-block">
      <h3>待下线链路</h3>
      <p v-if="!analysis.下线链路.length" class="empty-state">按当前条件没有待下线链路</p>
      <table v-else class="data-table" data-testid="departing-table">
        <thead>
          <tr><th>链路编号</th><th>上游实体</th><th>下游实体</th><th>状态</th><th>剔除方式</th></tr>
        </thead>
        <tbody>
          <tr v-for="edge in analysis.下线链路" :key="edge.链路编号">
            <td>{{ edge.链路编号 }}</td>
            <td>{{ edge.上游实体 }}</td>
            <td>{{ edge.下游实体 }}</td>
            <td>{{ edge.状态 }}</td>
            <td>{{ edge.剔除方式 }}</td>
          </tr>
        </tbody>
      </table>
    </section>

    <section v-if="analysis" class="impact-block">
      <h3>分层影响视图</h3>
      <p class="impact-hint">
        源头实体：{{ analysis.源头实体 }}；分层：{{ layerText(analysis) }}
      </p>
      <table class="data-table" data-testid="impact-table">
        <thead>
          <tr>
            <th>实体</th>
            <th>最近影响层</th>
            <th>影响判定</th>
            <th>确认口径</th>
            <th>取证链路</th>
            <th>待查血缘</th>
            <th>确认/待验证路径</th>
            <th>下线前链路</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="entity in analysis.实体"
            :key="entity.实体"
            :data-testid="`impact-row-${entity.实体}`"
            :data-verdict="entity.影响判定"
          >
            <td>{{ entity.实体 }}</td>
            <td>{{ entity.最近影响层 }}</td>
            <td>
              <span :class="['impact-badge', entity.影响判定 === '确认影响' ? 'confirmed' : 'pending']">
                {{ entity.影响判定 }}
              </span>
              <span v-if="entity.确认口径冲突" class="impact-badge conflict">口径冲突</span>
            </td>
            <td>{{ entity.确认口径 }}</td>
            <td class="impact-chain">{{ entity.证据链路.join(' → ') }}</td>
            <td class="impact-chain" :data-testid="`pending-${entity.实体}`">
              {{ entity.待查血缘.length ? entity.待查血缘.map((edge) => edge.链路编号).join('、') : '—' }}
            </td>
            <td>{{ entity.确认路径数 }} / {{ entity.待验证路径数 }}</td>
            <td class="impact-chain">
              {{ entity.下线前链路 ? entity.下线前链路.证据链路.join(' → ') : '—' }}
            </td>
          </tr>
          <tr v-if="!analysis.实体.length">
            <td colspan="8" class="empty-state">按当前条件没有可到达的下游实体</td>
          </tr>
        </tbody>
      </table>
      <p v-if="conflictText" class="impact-hint" data-testid="conflict-note">{{ conflictText }}</p>
    </section>

    <section v-if="analysis && analysis.循环.length" class="impact-block">
      <h3>循环回边</h3>
      <ul class="impact-list" data-testid="cycle-list">
        <li v-for="cycle in analysis.循环" :key="cycle.链路编号">
          {{ cycle.说明 }}（源层 {{ cycle.源层 }} → 目标层 {{ cycle.目标层 }}）
        </li>
      </ul>
    </section>

    <section class="impact-block">
      <h3>质量审计待办</h3>
      <p v-if="!qualityTodo.length" class="empty-state" data-testid="quality-empty">
        暂无由影响样本同步的质量审计待办
      </p>
      <div v-for="report in qualityTodo" :key="report.id" class="impact-report" :data-testid="`quality-report-${report.报告编号}`">
        <div class="impact-report-head">
          <strong>{{ report.报告编号 }}</strong>
          <span>{{ report.审计范围 }}</span>
          <span>状态：{{ report.status }}</span>
          <span>影响样本：{{ report.影响样本编号 }}</span>
        </div>
        <p class="impact-hint">
          确认影响 {{ report.确认影响.length }} 个；待验证支路 {{ report.待验证支路.length }} 个；
          口径冲突 {{ report.口径冲突.length }} 个。
        </p>
        <h4>整改清单</h4>
        <table class="data-table" data-testid="rectification-table">
          <thead>
            <tr><th>整改编号</th><th>整改类型</th><th>实体</th><th>整改动作</th><th>待查血缘</th><th>状态</th></tr>
          </thead>
          <tbody>
            <tr v-for="item in report.整改清单" :key="item.整改编号">
              <td>{{ item.整改编号 }}</td>
              <td>{{ item.整改类型 }}</td>
              <td>{{ item.实体 }}</td>
              <td>{{ item.整改动作 }}</td>
              <td class="impact-chain">
                {{ item.待查血缘.length ? item.待查血缘.map((edge) => edge.链路编号).join('、') : '—' }}
              </td>
              <td>{{ item.状态 }}</td>
            </tr>
          </tbody>
        </table>
        <h4>取证记录</h4>
        <table class="data-table" data-testid="evidence-table">
          <thead>
            <tr><th>实体</th><th>最近影响层</th><th>影响判定</th><th>当前链路</th><th>待查血缘</th><th>下线前链路</th><th>取证说明</th></tr>
          </thead>
          <tbody>
            <tr v-for="record in report.取证记录" :key="record.实体">
              <td>{{ record.实体 }}</td>
              <td>{{ record.最近影响层 }}</td>
              <td>{{ record.影响判定 }}</td>
              <td class="impact-chain">{{ record.当前链路.join(' → ') || '—' }}</td>
              <td class="impact-chain">{{ record.待查血缘.length ? record.待查血缘.join('、') : '—' }}</td>
              <td class="impact-chain">{{ record.下线前链路.join(' → ') || '—' }}</td>
              <td>{{ record.取证说明 }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>

    <footer class="page-foot">
      <span v-if="analysis">影响指纹：{{ analysis.指纹 }}</span>
      <span v-if="sampleLabel">{{ sampleLabel }}</span>
    </footer>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'

import {
  loadImpactAnalysis,
  loadQualityTodo,
  submitImpactSample,
} from '@/api/backend-service'
import type { ImpactAnalysis, ImpactQualityReport } from '@/data/types'

const source = ref('')
const exclude = ref('')
const analysis = ref<ImpactAnalysis | null>(null)
const qualityTodo = ref<ImpactQualityReport[]>([])
const message = ref('')
const errorMessage = ref('')
const submitting = ref(false)
const sampleLabel = ref('')

const conflictText = computed(() => {
  const conflicts = analysis.value?.摘要.口径冲突 ?? []
  if (!conflicts.length) return ''
  return `以下实体同时存在确认链路与待验证支路，确认口径冲突待裁决：${conflicts.join('、')}`
})

function layerText(payload: ImpactAnalysis) {
  return payload.分层
    .map((layer) => `第${layer.层}层 ${layer.实体.join('、')}`)
    .join('；')
}

function reset() {
  source.value = ''
  exclude.value = ''
  message.value = ''
  void reload()
}

async function reload() {
  errorMessage.value = ''
  message.value = ''
  try {
    analysis.value = await loadImpactAnalysis(source.value, exclude.value)
    qualityTodo.value = await loadQualityTodo()
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '影响分析读取失败'
  }
}

async function submitSample() {
  submitting.value = true
  errorMessage.value = ''
  message.value = ''
  try {
    const result = await submitImpactSample(source.value, exclude.value)
    message.value = result.message
    sampleLabel.value = `${result.duplicate ? '重复提交，未生效' : '本次生效'}：${result.sample.样本编号}`
    analysis.value = await loadImpactAnalysis(source.value, exclude.value)
    qualityTodo.value = await loadQualityTodo()
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '影响样本提交失败'
  } finally {
    submitting.value = false
  }
}

onMounted(reload)
</script>
