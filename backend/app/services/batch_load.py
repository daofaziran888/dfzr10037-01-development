"""__NAME__领域服务：字段、状态和动作来自业务配置，数据处理骨架由基类复用。"""
from __future__ import annotations

from app.services.base import BaseModuleService


class BatchLoadService(BaseModuleService):
    MODULE = "batch_load"
    ENTITY = "导入任务"
    OPERATION_TERM = "导入"
    LIST_FIELDS = ["任务编号", "数据文件", "目标图谱", "映射规则", "校验模式", "导入行数", "跳过行数", "导入时间"]
    REQUIRED_FIELDS = ["任务编号", "数据文件", "目标图谱"]
    STATUS_ORDER = ["待执行", "导入中", "已完成", "部分跳过"]
    ACTION_RULES = {"启动导入": "导入中", "暂停导入": "已完成", "标记跳过": "部分跳过"}
    NEGATIVE_ACTIONS = []
