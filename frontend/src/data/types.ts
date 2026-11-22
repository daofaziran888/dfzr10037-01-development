/** 纯前端数据层的公共类型：与全栈版后端返回的结构保持一致，换回后端时页面不用改。 */

export type EntryRow = {
  id: number
  status: string
  pending: boolean
  abnormal: boolean
  [field: string]: string | number | boolean
}

export type ModuleMeta = {
  key: string
  name: string
  entity: string
  desc: string
  fields: string[]
  statuses: string[]
  actions: string[]
  actionTargets: Record<string, string>
  metrics: string[]
}

export type PageResult = {
  items: EntryRow[]
  total: number
  page: number
  size: number
}

export type ActionResult = {
  ok: boolean
  message: string
}

export type OverviewResult = {
  cards: { label: string; value: number }[]
  modules: { name: string; created: number; pending: number; abnormal: number }[]
}

/** 血缘影响分析：后端 /api/data_lineage/impact 的返回结构。 */
export type ImpactEvidenceEdge = {
  序号: number
  链路编号: string
  上游实体: string
  下游实体: string
  状态: string
  转换描述: string
  关联字段: string
}

export type ImpactHistoricalPath = {
  下线前影响层: number | null
  证据链路: string[]
  路径: ImpactEvidenceEdge[]
  已下线链路: string[]
}

export type ImpactPendingBranch = {
  影响层: number
  证据链路: string[]
  路径: ImpactEvidenceEdge[]
  待查血缘: ImpactEvidenceEdge[]
}

export type ImpactEntity = {
  实体: string
  最近影响层: number
  确认影响层: number | null
  待验证影响层: number | null
  影响判定: string
  确认口径: string
  证据路径: ImpactEvidenceEdge[]
  证据链路: string[]
  待查血缘: ImpactEvidenceEdge[]
  待验证支路: ImpactPendingBranch | null
  确认路径数: number
  待验证路径数: number
  路径总数: number
  下线前链路: ImpactHistoricalPath | null
  确认口径冲突: boolean
  冲突说明: string
}

export type ImpactCycle = {
  链路编号: string
  上游实体: string
  下游实体: string
  源层: number
  目标层: number
  说明: string
}

export type ImpactSummary = {
  源头实体: string
  实体总数: number
  分层数: number
  确认影响数: number
  待验证支路数: number
  口径冲突数: number
  循环回边数: number
  确认影响: string[]
  待验证支路: string[]
  口径冲突: string[]
}

export type ImpactAnalysis = {
  源头实体: string
  下线链路: {
    链路编号: string
    上游实体: string
    下游实体: string
    状态: string
    剔除方式: string
  }[]
  排除链路: string[]
  摘要: ImpactSummary
  分层: { 层: number; 实体: string[] }[]
  实体: ImpactEntity[]
  循环: ImpactCycle[]
  指纹: string
}

export type ImpactRectification = {
  整改编号: string
  样本编号: string
  整改类型: string
  实体: string
  整改动作: string
  涉及链路: string[]
  待查血缘: ImpactEvidenceEdge[]
  当前链路: string[]
  下线前链路: string[]
  取证说明: string
  状态: string
}

export type ImpactEvidenceRecord = {
  实体: string
  最近影响层: number
  影响判定: string
  当前链路: string[]
  待查血缘: string[]
  下线前链路: string[]
  取证说明: string
}

export type ImpactQualityReport = {
  id: number
  status: string
  pending: boolean
  abnormal: boolean
  报告编号: string
  审计范围: string
  实体准确率: string
  关系完整率: string
  合规结论: string
  影响样本编号: string
  确认影响: string[]
  待验证支路: string[]
  口径冲突: string[]
  整改清单: ImpactRectification[]
  取证记录: ImpactEvidenceRecord[]
  [field: string]: unknown
}

export type ImpactSampleResult = {
  ok: boolean
  message: string
  duplicate: boolean
  effective: boolean
  sample: {
    样本编号: string
    指纹: string
    来源实体: string
    下线链路: ImpactAnalysis['下线链路']
    摘要: ImpactSummary
    分层: ImpactAnalysis['分层']
    实体: ImpactEntity[]
    循环: ImpactCycle[]
    质量审计同步?: {
      报告编号: string
      审计范围: string
      整改清单: ImpactRectification[]
      取证记录: ImpactEvidenceRecord[]
    } | null
  }
}
