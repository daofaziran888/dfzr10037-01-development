"""__NAME__领域服务：字段、状态和动作来自业务配置，数据处理骨架由基类复用。"""
from __future__ import annotations

from app.services.base import BaseModuleService


class QueryCacheService(BaseModuleService):
    MODULE = "query_cache"
    ENTITY = "缓存条目"
    OPERATION_TERM = "存储"
    LIST_FIELDS = ["条目编号", "查询模板", "结果哈希", "命中次数", "TTL秒数", "存储大小", "最后命中", "缓存状态"]
    REQUIRED_FIELDS = ["条目编号", "查询模板", "结果哈希"]
    STATUS_ORDER = ["有效", "即将过期", "已失效", "已淘汰"]
    ACTION_RULES = {"主动预热": "有效", "即时失效": "已失效"}
    NEGATIVE_ACTIONS = []
