# 知谱工坊 · 元数据知识图谱与智能探查平台

面向元数据实体抽取、关系建模、知识图谱构建、图谱搜索、实体链接、消岐融合、路径推理、子图探查与图谱演化追踪的元数据知识图谱与智能探查平台。

这是一个前后端分离的管理平台：前端 Vue 3 + Vite + TypeScript，后端 FastAPI（Python）。
两边各自独立启动，前端 dev server 已关掉自动打开页面，启动后按终端打印的地址手工打开。

## 目录结构

```text
.
├── frontend/                 Vue 3 + Vite + TypeScript 前端
│   ├── src/views/WorkbenchView.vue|tsx  全部模块共享工作台
│   ├── src/data/modules.ts              18个业务模块配置
│   ├── src/api/              统一请求封装
│   └── vite.config.ts        dev server 配置（open: false）
├── backend/                  FastAPI（Python） 后端
│   ├── app/routers/resource.py  通用查询/导出/登记/动作接口
│   ├── app/services/<key>.py    每个模块独立领域逻辑
│   ├── app/services/base.py     共享服务骨架
│   └── app/store.py          内存数据仓库与示例数据
├── .gitignore
└── docker-compose.yml
```

## 启动

### 后端

```bash
cd backend
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
./run.sh
```

健康检查：`curl http://127.0.0.1:8000/api/health`

### 前端

```bash
cd frontend
npm ci
npm run dev
```

前端默认监听 `http://127.0.0.1:5173/`，dev server 不会自动打开浏览器，
需要自己访问。`/api` 由 vite 代理到后端 `http://127.0.0.1:8000`。

## 业务模块

| 模块 | 目录 | 业务对象 | 主要字段 |
| --- | --- | --- | --- |
| 实体抽取 | `entity_extract` | 实体定义 | 实体编号、实体类型、数据来源 |
| 关系建模 | `relation_model` | 关系类型 | 关系编号、关系名、主体类型 |
| 图谱构建 | `graph_build` | 构建任务 | 任务编号、数据范围、图类型 |
| 图谱搜索 | `graph_search` | 搜索模板 | 模板编号、搜索类型、查询语法 |
| 实体链接 | `entity_link` | 链接规则 | 规则编号、源实体、目标实体 |
| 消岐融合 | `disambig` | 消岐配置 | 配置编号、歧义类型、候选实体 |
| 路径推理 | `path_reason` | 推理任务 | 任务编号、起始实体、目标实体 |
| 子图探查 | `subgraph_exp` | 探查配置 | 配置编号、探查种子、扩展策略 |
| 图谱演化 | `graph_evolve` | 演化记录 | 记录编号、变更类型、影响实体 |
| 质量审计 | `quality_audit` | 审计报告 | 报告编号、审计范围、实体准确率 |
| 元数据标注 | `metadata_tag` | 标注任务 | 任务编号、标注对象、标注类型 |
| 分类体系 | `taxonomy` | 分类树 | 分类编号、分类名称、父分类 |
| 查询缓存 | `query_cache` | 缓存条目 | 条目编号、查询模板、结果哈希 |
| 图谱索引 | `graph_index` | 索引配置 | 索引编号、目标属性、索引类型 |
| 数据血缘 | `data_lineage` | 血缘链路 | 链路编号、上游实体、下游实体 |
| 推荐引擎 | `reco_engine` | 推荐规则 | 规则编号、推荐场景、源实体 |
| 实体归并 | `entity_merge` | 归并任务 | 任务编号、源实体、目标实体 |
| 批量导入 | `batch_load` | 导入任务 | 任务编号、数据文件、目标图谱 |
| 图谱报告 | `report_gen` | 图谱报表 | 报告编号、报告类型、数据范围 |
| 图谱比对 | `graph_compare` | 比对任务 | 任务编号、基准图、对比图 |
| 定时任务 | `schedule_job` | 调度作业 | 作业编号、任务类型、关联图谱 |
| 治理看板 | `govern_dash` | 治理指标 | 指标编号、指标名称、评估对象 |

## 血缘影响分析

数据血缘的示例图刻意放了一个循环、两条确认路径和一条待验证支路：

```text
资产表 --DATA-1001(已废弃/直连)--> 主题表
资产表 --DATA-1002(已确认)--> 中间表A --DATA-1003(待验证)--> 主题表   # 待验证支路
主题表 --DATA-1004(已确认)--> 质量审计报告 --DATA-1005(已确认)--> 主题表  # 循环
主题表 --DATA-1006(已确认)--> 业务报表
资产表 --DATA-1007(已确认)--> 中间表B --DATA-1008(已确认)--> 下游宽表  # 确认路径一
资产表 --DATA-1009(已确认)--> 中间表C --DATA-1010(已确认)--> 下游宽表  # 确认路径二
```

入口：前端 `数据血缘 → 血缘影响分析`（`/data_lineage/impact`）；后端接口：

| 接口 | 说明 |
| --- | --- |
| `GET /api/data_lineage/impact?source=&exclude=` | 分层影响视图：每实体最近影响层、确认影响、待验证支路、循环回边 |
| `POST /api/data_lineage/impact/samples` | 提交分层影响样本并同步质量审计待办（同图同口径重复提交只生效一次） |
| `GET /api/data_lineage/impact/samples` | 已生效样本列表 |
| `GET /api/data_lineage/impact/rectifications?sample_id=` | 整改清单 |
| `GET /api/data_lineage/impact/quality-todo` | 由影响样本同步、仍待处理的质量审计报告 |

判定口径：

- 路径上每一段都是 `已确认`，实体才算**确认影响**；任一段为 `待验证`/`自动推导`，
  实体只算**待验证支路**，不得计入确认影响，取证时随行带出那段**待查血缘**。
- 遍历按 `(实体, 是否已经过待验证链路)` 去重，回边即终止，循环不会无限展开。
- 同一实体经多条路径到达只在一层出现一次，路径数分别统计确认路径与待验证路径。
- 撤掉直连（`exclude=DATA-1001`）后，主题表及其下游只剩 `DATA-1003` 支撑，
  会被标成待验证支路并给出「此前经 DATA-1001 到达」的取证链路。

## 约定

- 全部模块共享`frontend/src/views/WorkbenchView.vue|tsx`和一套资源路由。
- 每个模块仍保留独立`backend/app/services/<模块>.py`；纯前端保留
  `frontend/src/domain/<模块>.ts`，用于承载真实业务差异并维持36题位容量。
- 列表接口统一返回 `{ items, total, page, size }`，动作接口统一返回 `{ ok, message }`。
- 状态流转只允许在 `app/services` 里改，路由层不做业务判断。

领域：数据工程
子方向：数据分析与数据应用
