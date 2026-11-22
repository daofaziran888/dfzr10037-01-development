"""数据血缘领域服务：链路查询、状态流转、跨模块联动与影响分析。

影响分析从“待下线”的血缘边出发，沿下游方向遍历可到达实体，输出分层样本。
判定口径刻意保持保守：
- 只有整条路径上的链路都已确认，实体才算“确认影响”；
- 仅由待验证/自动推导链路支撑的实体只算“待验证支路”，不能计入确认影响；
- 遍历按状态去重并在回边处终止，循环不会让样本无限增长；
- 同一实体无论被多少条路径到达，在分层样本和整改清单里只出现一次。
"""
from __future__ import annotations

import hashlib
from collections import defaultdict
from datetime import datetime
from typing import Any, Iterable

from app.services.base import BaseModuleService
from app.store import store

CONFIRMED = "已确认"
PENDING_STATUSES = ("待验证", "自动推导")
IMPACT_CONFIRMED = "确认影响"
IMPACT_PENDING = "待验证支路"


class DataLineageService(BaseModuleService):
    MODULE = "data_lineage"
    ENTITY = "血缘链路"
    OPERATION_TERM = "转换"
    LIST_FIELDS = ["链路编号", "上游实体", "下游实体", "转换描述", "关联字段", "影响层级", "链路类型", "最后更新"]
    REQUIRED_FIELDS = ["链路编号", "上游实体", "下游实体"]
    STATUS_ORDER = ["自动推导", "已确认", "待验证", "已废弃"]
    ACTION_RULES = {"确认链路": "已确认", "提交验证": "待验证", "废弃链路": "已废弃"}
    NEGATIVE_ACTIONS = []

    def __init__(self) -> None:
        # 影响样本按“来源 + 下线链路 + 图快照”指纹去重，重复提交只返回原样本。
        self._impact_samples: list[dict[str, Any]] = []
        self._impact_sample_index: dict[str, dict[str, Any]] = {}
        self._impact_rectifications: list[dict[str, Any]] = []

    # ===== 跨模块数据流实现 =====
    def run_action(self, entry_id: int, action: str) -> tuple[dict[str, Any] | None, str]:
        entry, message = super().run_action(entry_id, action)
        if entry is None:
            return entry, message
        # 链路 L12: data_lineage → graph_evolve（血缘变更记录触发演化记录）
        if entry.get("status") in ("已确认", "待验证"):
            evolve_msg = self._push_to_graph_evolve(entry)
            message += "；" + evolve_msg
        # 链路 L13: data_lineage → graph_compare（血缘链路触发图谱版本比对）
        if entry.get("status") in ("已确认", "待验证"):
            compare_msg = self._push_to_graph_compare(entry)
            message += "；" + compare_msg
        return entry, message

    def _push_to_graph_evolve(self, entry: dict[str, Any]) -> str:
        rows = store.rows("graph_evolve")
        next_id = max((int(r.get("id", 0)) for r in rows), default=0) + 1
        ev_entry: dict[str, Any] = {
            "id": next_id,
            "status": "已记录",
            "pending": True,
            "abnormal": False,
            "记录编号": f"GRAP-EVOL-{next_id:04d}",
            "变更类型": f"lineage-{entry.get('链路类型','')}",
            "影响实体": str(entry.get("下游实体", "")),
            "影响关系": str(entry.get("关联字段", "")),
            "版本标签": f"v{next_id}.0",
            "变更描述": f"血缘链路{entry.get('链路编号','')}已变更",
            "回滚版本": f"v{next_id-1}.0",
            "演化时间": str(entry.get("最后更新", "2026-11-18")),
        }
        rows.append(ev_entry)
        return f"已记录图谱演化 {ev_entry['记录编号']}"

    def _push_to_graph_compare(self, entry: dict[str, Any]) -> str:
        rows = store.rows("graph_compare")
        next_id = max((int(r.get("id", 0)) for r in rows), default=0) + 1
        cmp_entry: dict[str, Any] = {
            "id": next_id,
            "status": "待执行",
            "pending": True,
            "abnormal": False,
            "任务编号": f"GRAP-CMP-{next_id:04d}",
            "基准图": str(entry.get("上游实体", "")),
            "对比图": str(entry.get("下游实体", "")),
            "比对维度": "lineage-change-diff",
            "新增实体": "auto-calc",
            "删除实体": "auto-calc",
            "变更关系": "auto-calc",
            "比对时间": str(entry.get("最后更新", "2026-11-18")),
        }
        rows.append(cmp_entry)
        return f"已触发图谱比对 {cmp_entry['任务编号']}"

    # ===== 影响分析 =====
    @staticmethod
    def _normalize_excludes(exclude: Iterable[str] | str | None) -> list[str]:
        if exclude is None:
            return []
        values = [exclude] if isinstance(exclude, str) else list(exclude)
        codes: list[str] = []
        for value in values:
            for part in str(value).split(","):
                code = part.strip()
                if code and code not in codes:
                    codes.append(code)
        return codes

    def _lineage_rows(self) -> list[dict[str, Any]]:
        return [
            dict(row) for row in store.rows(self.MODULE)
            if str(row.get("上游实体", "")).strip() and str(row.get("下游实体", "")).strip()
        ]

    @staticmethod
    def _edge(row: dict[str, Any]) -> dict[str, Any]:
        status = str(row.get("status", ""))
        return {
            "id": row.get("id"),
            "链路编号": str(row.get("链路编号", "")),
            "上游实体": str(row.get("上游实体", "")),
            "下游实体": str(row.get("下游实体", "")),
            "转换描述": str(row.get("转换描述", "")),
            "关联字段": str(row.get("关联字段", "")),
            "链路类型": str(row.get("链路类型", "")),
            "状态": status,
            "确认": status == CONFIRMED,
            "已下线": status == "已废弃",
        }

    @staticmethod
    def _evidence_edge(edge: dict[str, Any], index: int) -> dict[str, Any]:
        return {
            "序号": index,
            "链路编号": edge["链路编号"],
            "上游实体": edge["上游实体"],
            "下游实体": edge["下游实体"],
            "状态": edge["状态"],
            "转换描述": edge["转换描述"],
            "关联字段": edge["关联字段"],
        }

    def _default_source(self, rows: list[dict[str, Any]], excludes: list[str]) -> str:
        # 优先以待下线链路的上游实体作为影响分析起点。
        for row in rows:
            code = str(row.get("链路编号", ""))
            if code in excludes or str(row.get("status", "")) == "已废弃":
                return str(row.get("上游实体", ""))
        return str(rows[0].get("上游实体", "")) if rows else ""

    def impact_analysis(
        self,
        source: str | None = None,
        exclude: Iterable[str] | str | None = None,
    ) -> dict[str, Any]:
        excludes = self._normalize_excludes(exclude)
        rows = self._lineage_rows()
        source_entity = (source or "").strip() or self._default_source(rows, excludes)

        departing_rows = [
            row for row in rows
            if str(row.get("status", "")) == "已废弃"
            or str(row.get("链路编号", "")) in excludes
            or str(row.get("id", "")) in excludes
        ]
        departing_codes = {str(row.get("链路编号", "")) for row in departing_rows}
        active_edges = [
            self._edge(row) for row in rows
            if str(row.get("status", "")) != "已废弃"
            and str(row.get("链路编号", "")) not in excludes
            and str(row.get("id", "")) not in excludes
        ]
        historical_edges = [self._edge(row) for row in rows]

        adjacency: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for edge in active_edges:
            adjacency[edge["上游实体"]].append(edge)
        for bucket in adjacency.values():
            bucket.sort(key=lambda item: (item["链路编号"], str(item["id"])))

        # 状态遍历：False=路径全部已确认，True=路径上至少有一段待验证。
        distances: dict[tuple[str, bool], int] = {(source_entity, False): 0}
        order: list[tuple[str, bool]] = [(source_entity, False)]
        pointer = 0
        while pointer < len(order):
            entity, reached_pending = order[pointer]
            pointer += 1
            for edge in adjacency.get(entity, []):
                target = edge["下游实体"]
                if target == source_entity:
                    continue
                next_pending = reached_pending or not edge["确认"]
                state = (target, next_pending)
                if state in distances:
                    continue
                distances[state] = distances[(entity, reached_pending)] + 1
                order.append(state)

        # 最短状态路径计数 + 待验证段数最少的前驱（用于取证路径）。
        counts: dict[tuple[str, bool], int] = {(source_entity, False): 1}
        pending_cost: dict[tuple[str, bool], int] = {(source_entity, False): 0}
        best_prev: dict[tuple[str, bool], tuple[tuple[str, bool], dict[str, Any]]] = {}
        for state in sorted(distances, key=lambda item: (distances[item], item[0], item[1])):
            entity, reached_pending = state
            base_count = counts.get(state, 0)
            base_cost = pending_cost.get(state, 0)
            if base_count == 0:
                continue
            for edge in adjacency.get(entity, []):
                target = edge["下游实体"]
                if target == source_entity:
                    continue
                next_pending = reached_pending or not edge["确认"]
                next_state = (target, next_pending)
                if distances.get(next_state) != distances[state] + 1:
                    continue
                counts[next_state] = min(999, counts.get(next_state, 0) + base_count)
                candidate_cost = base_cost + (0 if edge["确认"] else 1)
                previous = best_prev.get(next_state)
                if (
                    pending_cost.get(next_state, 1_000_000) > candidate_cost
                    or (
                        pending_cost.get(next_state, 1_000_000) == candidate_cost
                        and (previous is None or edge["链路编号"] < previous[1]["链路编号"])
                    )
                ):
                    pending_cost[next_state] = candidate_cost
                    best_prev[next_state] = (state, edge)

        def trace(state: tuple[str, bool]) -> list[dict[str, Any]]:
            path: list[dict[str, Any]] = []
            cursor = state
            guard = 0
            while cursor != (source_entity, False):
                guard += 1
                if guard > len(distances) + 1:
                    break
                step = best_prev.get(cursor)
                if step is None:
                    return []
                cursor, edge = step
                path.append(edge)
            return list(reversed(path))

        # 下线前的历史路径：用包含已废弃/被剔除链路的历史图求最短路，
        # 用来回答“这个实体此前走的是哪条链路”。
        historical_adjacency: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for edge in historical_edges:
            historical_adjacency[edge["上游实体"]].append(edge)
        for bucket in historical_adjacency.values():
            bucket.sort(key=lambda item: (item["链路编号"], str(item["id"])))
        historical_dist: dict[str, int] = {source_entity: 0}
        historical_prev: dict[str, dict[str, Any]] = {}
        queue = [source_entity]
        cursor = 0
        while cursor < len(queue):
            entity = queue[cursor]
            cursor += 1
            for edge in historical_adjacency.get(entity, []):
                target = edge["下游实体"]
                if target in historical_dist:
                    continue
                historical_dist[target] = historical_dist[entity] + 1
                historical_prev[target] = edge
                queue.append(target)

        def historical_trace(target: str) -> list[dict[str, Any]]:
            path: list[dict[str, Any]] = []
            entity = target
            while entity != source_entity:
                edge = historical_prev.get(entity)
                if edge is None:
                    return []
                path.append(edge)
                entity = edge["上游实体"]
            return list(reversed(path))

        entities: list[dict[str, Any]] = []
        layers: dict[int, list[str]] = defaultdict(list)
        for entity in sorted({key[0] for key in distances if key[0] != source_entity}):
            confirmed_dist = distances.get((entity, False))
            pending_dist = distances.get((entity, True))
            if confirmed_dist is None and pending_dist is None:
                continue
            nearest = min(
                distance for distance in (confirmed_dist, pending_dist) if distance is not None)
            layers[nearest].append(entity)

            confirmed_count = counts.get((entity, False), 0)
            pending_count = counts.get((entity, True), 0)
            is_confirmed = confirmed_dist is not None
            evidence_state = (entity, False) if is_confirmed else (entity, True)
            evidence_path = trace(evidence_state)
            evidence = [
                self._evidence_edge(edge, index + 1)
                for index, edge in enumerate(evidence_path)
            ]
            pending_segments = [
                self._evidence_edge(edge, index + 1)
                for index, edge in enumerate(edge for edge in evidence_path if not edge["确认"])
            ]

            pending_branch = None
            if pending_dist is not None:
                branch_path = trace((entity, True))
                pending_branch = {
                    "影响层": pending_dist,
                    "证据链路": [edge["链路编号"] for edge in branch_path],
                    "路径": [
                        self._evidence_edge(edge, index + 1)
                        for index, edge in enumerate(branch_path)
                    ],
                    "待查血缘": [
                        self._evidence_edge(edge, index + 1)
                        for index, edge in enumerate(
                            edge for edge in branch_path if not edge["确认"])
                    ],
                }

            previous_path = historical_trace(entity)
            previous_departed = [
                edge for edge in previous_path
                if edge["链路编号"] in departing_codes or edge["已下线"]
            ]
            previous = None
            if previous_departed:
                previous = {
                    "下线前影响层": historical_dist.get(entity),
                    "证据链路": [edge["链路编号"] for edge in previous_path],
                    "路径": [
                        self._evidence_edge(edge, index + 1)
                        for index, edge in enumerate(previous_path)
                    ],
                    "已下线链路": [edge["链路编号"] for edge in previous_departed],
                }

            conflict_reasons: list[str] = []
            if confirmed_dist is not None and pending_dist is not None:
                conflict_reasons.append(
                    "同一实体同时存在已确认链路与待验证支路，两条路径的确认口径不一致"
                )
            if previous is not None and not is_confirmed:
                conflict_reasons.append(
                    f"下线链路此前为确认口径（{'→'.join(previous['证据链路'])}），"
                    "撤链后仅剩待验证支路支撑"
                )

            entities.append({
                "实体": entity,
                "最近影响层": nearest,
                "确认影响层": confirmed_dist,
                "待验证影响层": pending_dist,
                "影响判定": IMPACT_CONFIRMED if is_confirmed else IMPACT_PENDING,
                "确认口径": "证据路径全链路已确认" if is_confirmed else "仅待验证路径支撑，不计入确认影响",
                "证据路径": evidence,
                "证据链路": [edge["链路编号"] for edge in evidence_path],
                "待查血缘": pending_segments,
                "待验证支路": pending_branch,
                "确认路径数": confirmed_count if is_confirmed else 0,
                "待验证路径数": pending_count,
                "路径总数": confirmed_count + pending_count,
                "下线前链路": previous,
                "确认口径冲突": bool(conflict_reasons),
                "冲突说明": "；".join(conflict_reasons),
            })

        entities.sort(key=lambda item: (item["最近影响层"], item["实体"]))

        # 回边：目标实体的最近层不高于当前实体，说明该边没有推进遍历。
        nearest_distance = {
            entity: min(
                distance for distance in (
                    distances.get((entity, False)), distances.get((entity, True))
                ) if distance is not None
            )
            for entity in {key[0] for key in distances}
        }
        cycles: list[dict[str, Any]] = []
        seen_cycle_edges: set[tuple[str, str, str]] = set()
        for edge in active_edges:
            source_layer = nearest_distance.get(edge["上游实体"])
            target_layer = nearest_distance.get(edge["下游实体"])
            if source_layer is None or target_layer is None:
                continue
            if target_layer > source_layer:
                continue
            key = (edge["上游实体"], edge["下游实体"], edge["链路编号"])
            if key in seen_cycle_edges:
                continue
            seen_cycle_edges.add(key)
            cycles.append({
                "链路编号": edge["链路编号"],
                "上游实体": edge["上游实体"],
                "下游实体": edge["下游实体"],
                "源层": source_layer,
                "目标层": target_layer,
                "说明": f"{edge['上游实体']}→{edge['下游实体']} 为回边，遍历在此终止，不重复展开",
            })

        confirmed_entities = [item["实体"] for item in entities if item["影响判定"] == IMPACT_CONFIRMED]
        pending_entities = [item["实体"] for item in entities if item["影响判定"] == IMPACT_PENDING]
        conflict_entities = [item["实体"] for item in entities if item["确认口径冲突"]]
        summary = {
            "源头实体": source_entity,
            "实体总数": len(entities),
            "分层数": len(layers),
            "确认影响数": len(confirmed_entities),
            "待验证支路数": len(pending_entities),
            "口径冲突数": len(conflict_entities),
            "循环回边数": len(cycles),
            "确认影响": confirmed_entities,
            "待验证支路": pending_entities,
            "口径冲突": conflict_entities,
        }

        return {
            "源头实体": source_entity,
            "下线链路": [
                {
                    "链路编号": str(row.get("链路编号", "")),
                    "上游实体": str(row.get("上游实体", "")),
                    "下游实体": str(row.get("下游实体", "")),
                    "状态": str(row.get("status", "")),
                    "剔除方式": "显式下线" if str(row.get("链路编号", "")) in excludes else "已废弃",
                }
                for row in departing_rows
            ],
            "排除链路": excludes,
            "摘要": summary,
            "分层": [
                {"层": layer, "实体": sorted(layers[layer])}
                for layer in sorted(layers)
            ],
            "实体": entities,
            "循环": cycles,
            "指纹": self._impact_fingerprint(source_entity, excludes, rows),
        }

    def _impact_fingerprint(
        self,
        source: str,
        excludes: list[str],
        rows: list[dict[str, Any]],
    ) -> str:
        snapshot = "|".join(
            f"{row.get('id')}:{row.get('链路编号')}:{row.get('status')}:"
            f"{row.get('上游实体')}>{{row.get('下游实体')}}"
            for row in sorted(rows, key=lambda item: str(item.get("链路编号", "")))
        )
        raw = f"{source}|{','.join(sorted(excludes))}|{snapshot}"
        return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:16]

    # ===== 分层影响样本与整改清单 =====
    def submit_impact_sample(
        self,
        source: str | None = None,
        exclude: Iterable[str] | str | None = None,
        sync_quality: bool = True,
    ) -> dict[str, Any]:
        analysis = self.impact_analysis(source=source, exclude=exclude)
        fingerprint = analysis["指纹"]
        existing = self._impact_sample_index.get(fingerprint)
        if existing is not None:
            return {
                "样本": existing,
                "重复提交": True,
                "生效": False,
                "消息": f"同一影响样本已提交过（{existing['样本编号']}），重复抽样不再生成新样本",
            }

        sample_id = f"IMPA-{len(self._impact_samples) + 1:04d}"
        sample: dict[str, Any] = {
            "样本编号": sample_id,
            "指纹": fingerprint,
            "来源实体": analysis["源头实体"],
            "下线链路": analysis["下线链路"],
            "下线链路编号": [
                item["链路编号"] for item in analysis["下线链路"]
            ],
            "排除链路": analysis["排除链路"],
            "摘要": analysis["摘要"],
            "分层": analysis["分层"],
            "实体": analysis["实体"],
            "循环": analysis["循环"],
            "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "重复提交": False,
            "生效": True,
        }
        sync_result = self._sync_quality_audit(sample) if sync_quality else None
        sample["质量审计同步"] = sync_result
        self._impact_samples.append(sample)
        self._impact_sample_index[fingerprint] = sample
        return {
            "样本": sample,
            "重复提交": False,
            "生效": True,
            "消息": (
                f"影响样本 {sample_id} 已生成并同步质量审计"
                if sync_result else f"影响样本 {sample_id} 已生成"
            ),
        }

    def _sync_quality_audit(self, sample: dict[str, Any]) -> dict[str, Any]:
        rectifications = self._build_rectifications(sample)
        rows = store.rows("quality_audit")
        next_id = max((int(row.get("id", 0)) for row in rows), default=0) + 1
        report_code = f"QUAL-IMPACT-{next_id:04d}"
        evidence_records = [
            {
                "实体": item["实体"],
                "最近影响层": item["最近影响层"],
                "影响判定": item["影响判定"],
                "当前链路": item["证据链路"],
                "待查血缘": [edge["链路编号"] for edge in item["待查血缘"]],
                "下线前链路": (
                    item["下线前链路"]["证据链路"] if item["下线前链路"] else []
                ),
                "取证说明": self._evidence_note(item),
            }
            for item in sample["实体"]
        ]
        row: dict[str, Any] = {
            "id": next_id,
            "status": "待审计",
            "pending": True,
            "abnormal": any(item["影响判定"] == IMPACT_PENDING for item in sample["实体"]),
            "报告编号": report_code,
            "审计范围": (
                f"血缘影响分析-{sample['来源实体']}"
                + (f"（下线{'、'.join(sample['下线链路编号'])}）"
                   if sample.get("下线链路编号") else "")
            ),
            "实体准确率": "待取证",
            "关系完整率": (
                f"{sample['摘要']['确认影响数']}/{sample['摘要']['实体总数']}"
            ),
            "冗余度": "重复提交已去重",
            "更新时效": "立即",
            "合规结论": "待审计",
            "审计时间": datetime.now().strftime("%Y-%m-%d"),
            "影响样本编号": sample["样本编号"],
            "分层影响样本": sample["分层"],
            "确认影响": sample["摘要"]["确认影响"],
            "待验证支路": sample["摘要"]["待验证支路"],
            "口径冲突": sample["摘要"]["口径冲突"],
            "整改清单": rectifications,
            "取证记录": evidence_records,
        }
        rows.append(row)
        self._impact_rectifications.extend(rectifications)
        return {
            "报告编号": report_code,
            "审计范围": row["审计范围"],
            "整改清单": rectifications,
            "取证记录": evidence_records,
        }

    def _evidence_note(self, item: dict[str, Any]) -> str:
        current = "→".join(item["证据链路"]) or "无"
        note = f"当前经 {current} 到达，判定为{item['影响判定']}"
        if item["待查血缘"]:
            note += "；需随取证核对待查血缘 " + "、".join(
                edge["链路编号"] for edge in item["待查血缘"])
        if item["下线前链路"]:
            note += "；此前经 " + "→".join(item["下线前链路"]["证据链路"]) + " 到达"
        return note

    def _build_rectifications(self, sample: dict[str, Any]) -> list[dict[str, Any]]:
        items: list[dict[str, Any]] = []
        seen: set[tuple[str, str]] = set()

        def append(item: dict[str, Any]) -> None:
            key = (item["整改类型"], item["实体"])
            if key in seen:
                return
            seen.add(key)
            items.append(item)

        for departed in sample["下线链路"]:
            append({
                "样本编号": sample["样本编号"],
                "整改类型": "下线链路复核",
                "实体": departed["下游实体"],
                "整改动作": f"复核待下线链路 {departed['链路编号']} 的下游影响范围",
                "涉及链路": [departed["链路编号"]],
                "待查血缘": [],
                "当前链路": [departed["链路编号"]],
                "下线前链路": [departed["链路编号"]],
                "取证说明": (
                    f"链路 {departed['链路编号']}（{departed['上游实体']}→"
                    f"{departed['下游实体']}）当前状态为{departed['状态']}，"
                    "需确认下线后下游是否仍有其他路径支撑"
                ),
                "状态": "待处理",
            })

        for item in sample["实体"]:
            if item["影响判定"] == IMPACT_CONFIRMED:
                append({
                    "样本编号": sample["样本编号"],
                    "整改类型": "影响复核",
                    "实体": item["实体"],
                    "整改动作": f"复核 {item['实体']} 的已确认下游链路口径",
                    "涉及链路": item["证据链路"],
                    "待查血缘": [],
                    "当前链路": item["证据链路"],
                    "下线前链路": (
                        item["下线前链路"]["证据链路"] if item["下线前链路"] else []
                    ),
                    "取证说明": self._evidence_note(item),
                    "状态": "待处理",
                })
            else:
                append({
                    "样本编号": sample["样本编号"],
                    "整改类型": "待验证取证",
                    "实体": item["实体"],
                    "整改动作": (
                        f"补验待查血缘 {item['待查血缘'][0]['链路编号'] if item['待查血缘'] else '—'}"
                        f" 后复核 {item['实体']} 的影响口径"
                    ),
                    "涉及链路": item["证据链路"],
                    "待查血缘": item["待查血缘"],
                    "当前链路": item["证据链路"],
                    "下线前链路": (
                        item["下线前链路"]["证据链路"] if item["下线前链路"] else []
                    ),
                    "取证说明": self._evidence_note(item),
                    "状态": "待处理",
                })
            if item["确认口径冲突"]:
                append({
                    "样本编号": sample["样本编号"],
                    "整改类型": "口径冲突裁决",
                    "实体": item["实体"],
                    "整改动作": f"裁决 {item['实体']} 的确认口径冲突并留痕",
                    "涉及链路": item["证据链路"],
                    "待查血缘": item["待查血缘"],
                    "当前链路": item["证据链路"],
                    "下线前链路": (
                        item["下线前链路"]["证据链路"] if item["下线前链路"] else []
                    ),
                    "取证说明": item["冲突说明"],
                    "状态": "待处理",
                })

        for index, item in enumerate(items, start=1):
            item["整改编号"] = f"RECT-{sample['样本编号'].split('-')[-1]}-{index:02d}"
        return items

    def list_impact_samples(self) -> list[dict[str, Any]]:
        return [self._sample_summary(sample) for sample in self._impact_samples]

    def get_impact_sample(self, sample_id: str) -> dict[str, Any] | None:
        for sample in self._impact_samples:
            if sample["样本编号"] == sample_id:
                return sample
        return None

    def impact_rectifications(self, sample_id: str | None = None) -> list[dict[str, Any]]:
        if not sample_id:
            return list(self._impact_rectifications)
        return [
            item for item in self._impact_rectifications
            if item["样本编号"] == sample_id
        ]

    @staticmethod
    def _sample_summary(sample: dict[str, Any]) -> dict[str, Any]:
        return {
            "样本编号": sample["样本编号"],
            "指纹": sample["指纹"],
            "来源实体": sample["来源实体"],
            "摘要": sample["摘要"],
            "生成时间": sample["生成时间"],
            "提取方式": "分层影响抽样",
        }

    def domain_snapshot(self) -> dict[str, Any]:
        base = super().domain_snapshot()
        base["cross_module_consumers"] = ["graph_evolve", "graph_compare", "quality_audit"]
        return base
