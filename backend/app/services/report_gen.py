"""__NAME__领域服务：字段、状态和动作来自业务配置，数据处理骨架由基类复用。"""
from __future__ import annotations

from app.services.base import BaseModuleService


class ReportGenService(BaseModuleService):
    MODULE = "report_gen"
    ENTITY = "图谱报表"
    OPERATION_TERM = "校验"
    LIST_FIELDS = ["报告编号", "报告类型", "数据范围", "图表配置", "输出格式", "生成周期", "分发列表", "最近生成"]
    REQUIRED_FIELDS = ["报告编号", "报告类型", "数据范围"]
    STATUS_ORDER = ["草稿", "生成中", "已生成", "生成失败"]
    ACTION_RULES = {"启动生成": "生成中", "中止生成": "已生成", "标记失败": "生成失败"}
    NEGATIVE_ACTIONS = []
