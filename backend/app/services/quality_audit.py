"""__NAME__领域服务：字段、状态和动作来自业务配置，数据处理骨架由基类复用。"""
from __future__ import annotations

from app.services.base import BaseModuleService


class QualityAuditService(BaseModuleService):
    MODULE = "quality_audit"
    ENTITY = "审计报告"
    OPERATION_TERM = "校验"
    LIST_FIELDS = ["报告编号", "审计范围", "实体准确率", "关系完整率", "冗余度", "更新时效", "合规结论", "审计时间"]
    REQUIRED_FIELDS = ["报告编号", "审计范围", "实体准确率"]
    STATUS_ORDER = ["待审计", "审计中", "已通过", "需整改"]
    ACTION_RULES = {"发起审计": "审计中", "确认通过": "已通过", "指派整改": "需整改"}
    NEGATIVE_ACTIONS = []
