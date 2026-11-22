import { request } from './client'
import { moduleMeta } from '@/data/modules'
import type {
  ActionResult,
  EntryRow,
  ImpactAnalysis,
  ImpactQualityReport,
  ImpactRectification,
  ImpactSampleResult,
  OverviewResult,
  PageResult,
} from '@/data/types'

export { moduleMeta }

export async function listEntries(
  key: string,
  filters: Record<string, string> = {},
): Promise<PageResult> {
  const query = new URLSearchParams(filters).toString()
  const response = await request(`/api/${key}?${query}`)
  if (!response.ok) throw new Error('业务数据读取失败')
  return await response.json()
}

export async function createEntry(
  key: string,
  values: Record<string, string>,
): Promise<ActionResult> {
  const response = await request(`/api/${key}`, {
    method: 'POST',
    body: JSON.stringify({ values }),
  })
  return await response.json()
}

export async function runAction(
  key: string,
  id: number,
  action: string,
): Promise<ActionResult> {
  const response = await request(`/api/${key}/${id}/actions`, {
    method: 'POST',
    body: JSON.stringify({ action }),
  })
  return await response.json()
}

export async function downloadEntries(
  key: string,
  filters: Record<string, string> = {},
): Promise<void> {
  const query = new URLSearchParams(filters).toString()
  const response = await request(`/api/${key}/export?${query}`)
  if (!response.ok) throw new Error('业务数据导出失败')
  const url = URL.createObjectURL(await response.blob())
  const anchor = document.createElement('a')
  anchor.href = url
  anchor.download = `${key}.csv`
  document.body.appendChild(anchor)
  anchor.click()
  document.body.removeChild(anchor)
  URL.revokeObjectURL(url)
}

export async function loadOverview(): Promise<OverviewResult> {
  const response = await request('/api/overview')
  if (!response.ok) throw new Error('运营概览读取失败')
  return await response.json()
}

export async function loadImpactAnalysis(
  source = '',
  exclude = '',
): Promise<ImpactAnalysis> {
  const query = new URLSearchParams()
  if (source.trim()) query.set('source', source.trim())
  if (exclude.trim()) query.set('exclude', exclude.trim())
  const suffix = query.toString()
  const response = await request(`/api/data_lineage/impact${suffix ? `?${suffix}` : ''}`)
  if (!response.ok) throw new Error('血缘影响分析读取失败')
  return await response.json()
}

export async function submitImpactSample(
  source = '',
  exclude = '',
): Promise<ImpactSampleResult> {
  const response = await request('/api/data_lineage/impact/samples', {
    method: 'POST',
    body: JSON.stringify({ source: source.trim() || null, exclude: exclude.trim() || null }),
  })
  if (!response.ok) throw new Error('影响样本提交失败')
  return await response.json()
}

export async function loadQualityTodo(): Promise<ImpactQualityReport[]> {
  const response = await request('/api/data_lineage/impact/quality-todo')
  if (!response.ok) throw new Error('质量审计待办读取失败')
  const payload = (await response.json()) as { items: ImpactQualityReport[] }
  return payload.items
}

export async function loadRectifications(sampleId = ''): Promise<ImpactRectification[]> {
  const query = sampleId.trim() ? `?sample_id=${encodeURIComponent(sampleId.trim())}` : ''
  const response = await request(`/api/data_lineage/impact/rectifications${query}`)
  if (!response.ok) throw new Error('整改清单读取失败')
  const payload = (await response.json()) as { items: ImpactRectification[] }
  return payload.items
}
