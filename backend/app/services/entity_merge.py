"""__NAME__领域服务：字段、状态和动作来自业务配置，数据处理骨架由基类复用。"""
from __future__ import annotations

from app.services.base import BaseModuleService


class EntityMergeService(BaseModuleService):
    MODULE = "entity_merge"
    ENTITY = "归并任务"
    OPERATION_TERM = "去重"
    LIST_FIELDS = ["任务编号", "源实体", "目标实体", "归并策略", "冲突字段", "冲突裁决", "归并行数", "归并时间"]
    REQUIRED_FIELDS = ["任务编号", "源实体", "目标实体"]
    STATUS_ORDER = ["待归并", "归并中", "已完成", "冲突待决"]
    ACTION_RULES = {"启动归并": "归并中", "裁决冲突": "已完成", "确认完成": "冲突待决"}
    NEGATIVE_ACTIONS = []
