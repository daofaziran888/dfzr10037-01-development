<template>
  <section class="page">
    <header class="page-head">
      <div>
        <h2>运营概览</h2>
        <p class="page-desc">汇总各业务模块的关键指标，先看总量再看异常。</p>
      </div>
    </header>
    <div class="stat-row">
      <article v-for="card in cards" :key="card.label" class="stat-card">
        <span class="stat-label">{{ card.label }}</span>
        <strong class="stat-value">{{ card.value }}</strong>
      </article>
    </div>
    <table class="data-table">
      <thead>
        <tr><th>业务模块</th><th>今日新增</th><th>待处理</th><th>异常量</th></tr>
      </thead>
      <tbody>
        <tr v-for="row in moduleRows" :key="row.name">
          <td>{{ row.name }}</td>
          <td>{{ row.created }}</td>
          <td>{{ row.pending }}</td>
          <td>{{ row.abnormal }}</td>
        </tr>
      </tbody>
    </table>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'

import { fetchJson } from '@/api/client'

type Overview = {
  cards: { label: string; value: number }[]
  modules: { name: string; created: number; pending: number; abnormal: number }[]
}

const cards = ref<Overview['cards']>([])
const moduleRows = ref<Overview['modules']>([])

onMounted(async () => {
  try {
    const payload = await fetchJson<Overview>('/api/overview')
    cards.value = payload.cards
    moduleRows.value = payload.modules
  } catch {
    cards.value = [{"label": "业务模块", "value": 0}, {"label": "今日新增", "value": 0}]
    moduleRows.value = [{"name": "实体抽取", "created": 0, "pending": 0, "abnormal": 0}, {"name": "关系建模", "created": 0, "pending": 0, "abnormal": 0}, {"name": "图谱构建", "created": 0, "pending": 0, "abnormal": 0}, {"name": "图谱搜索", "created": 0, "pending": 0, "abnormal": 0}, {"name": "实体链接", "created": 0, "pending": 0, "abnormal": 0}, {"name": "消岐融合", "created": 0, "pending": 0, "abnormal": 0}, {"name": "路径推理", "created": 0, "pending": 0, "abnormal": 0}, {"name": "子图探查", "created": 0, "pending": 0, "abnormal": 0}, {"name": "图谱演化", "created": 0, "pending": 0, "abnormal": 0}, {"name": "质量审计", "created": 0, "pending": 0, "abnormal": 0}, {"name": "元数据标注", "created": 0, "pending": 0, "abnormal": 0}, {"name": "分类体系", "created": 0, "pending": 0, "abnormal": 0}, {"name": "查询缓存", "created": 0, "pending": 0, "abnormal": 0}, {"name": "图谱索引", "created": 0, "pending": 0, "abnormal": 0}, {"name": "数据血缘", "created": 0, "pending": 0, "abnormal": 0}, {"name": "推荐引擎", "created": 0, "pending": 0, "abnormal": 0}, {"name": "实体归并", "created": 0, "pending": 0, "abnormal": 0}, {"name": "批量导入", "created": 0, "pending": 0, "abnormal": 0}, {"name": "图谱报告", "created": 0, "pending": 0, "abnormal": 0}, {"name": "图谱比对", "created": 0, "pending": 0, "abnormal": 0}, {"name": "定时任务", "created": 0, "pending": 0, "abnormal": 0}, {"name": "治理看板", "created": 0, "pending": 0, "abnormal": 0}]
  }
})
</script>
