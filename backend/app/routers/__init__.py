"""业务路由汇总：所有模块共用一套资源路由，由领域服务完成分派。"""
from __future__ import annotations

from app.routers import impact, resource

# impact 的固定路径（/api/data_lineage/impact）必须先于动态资源路由注册，
# 否则会被 /api/{module}/{entry_id} 抢先匹配。
ROUTERS = [impact, resource]
