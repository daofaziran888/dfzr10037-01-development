"""__NAME__领域服务：字段、状态和动作来自业务配置，数据处理骨架由基类复用。"""
from __future__ import annotations

from app.services.base import BaseModuleService


class GraphIndexService(BaseModuleService):
    MODULE = "graph_index"
    ENTITY = "索引配置"
    OPERATION_TERM = "存储"
    LIST_FIELDS = ["索引编号", "目标属性", "索引类型", "覆盖实体", "存储体积", "构建耗时", "刷新周期", "最近重建"]
    REQUIRED_FIELDS = ["索引编号", "目标属性", "索引类型"]
    STATUS_ORDER = ["待构建", "构建中", "已生效", "索引异常"]
    ACTION_RULES = {"启动构建": "构建中", "重建索引": "已生效", "标记异常": "索引异常"}
    NEGATIVE_ACTIONS = []
