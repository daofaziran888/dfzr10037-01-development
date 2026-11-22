"""血缘影响分析接口：分析视图、分层影响样本落库与质量审计整改派发。"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse

from app.schemas import ImpactSamplePayload
from app.services import service_for
from app.services.data_lineage import DataLineageService

router = APIRouter(prefix="/api/data_lineage", tags=["血缘影响分析"])


def _lineage_service() -> DataLineageService:
    service = service_for("data_lineage")
    if not isinstance(service, DataLineageService):  # pragma: no cover - 注册表固定
        raise HTTPException(status_code=500, detail="数据血缘服务未注册")
    return service


@router.get("/impact")
def impact_analysis(
    source: str | None = Query(default=None),
    exclude: str | None = Query(default=None),
) -> dict[str, Any]:
    """按待下线链路查询下游影响：分层视图 + 确认影响 + 待验证支路 + 循环回边。"""
    return _lineage_service().impact_analysis(source=source, exclude=exclude)


@router.post("/impact/samples")
def submit_impact_sample(payload: ImpactSamplePayload) -> dict[str, Any]:
    """提交分层影响样本；同一图快照 + 同一下线口径只生效一次。"""
    result = _lineage_service().submit_impact_sample(
        source=payload.source,
        exclude=payload.exclude,
        sync_quality=payload.sync_quality,
    )
    return {
        "ok": True,
        "message": result["消息"],
        "duplicate": result["重复提交"],
        "effective": result["生效"],
        "sample": result["样本"],
    }


@router.get("/impact/samples")
def list_impact_samples() -> dict[str, Any]:
    items = _lineage_service().list_impact_samples()
    return {"items": items, "total": len(items)}


@router.get("/impact/samples/{sample_id}")
def get_impact_sample(sample_id: str) -> dict[str, Any]:
    sample = _lineage_service().get_impact_sample(sample_id)
    if sample is None:
        raise HTTPException(status_code=404, detail=f"影响样本 {sample_id} 不存在")
    return sample


@router.get("/impact/rectifications")
def list_rectifications(sample_id: str | None = Query(default=None)) -> dict[str, Any]:
    items = _lineage_service().impact_rectifications(sample_id)
    return {"items": items, "total": len(items), "sample_id": sample_id}


@router.get("/impact/quality-todo")
def quality_todo() -> JSONResponse:
    """质量审计待办：返回由影响样本同步过去、仍待处理的审计报告。"""
    rows = [
        row for row in service_for("quality_audit").list_entries(size=1_000_000)[0]
        if row.get("影响样本编号")
    ]
    return JSONResponse({
        "items": rows,
        "total": len(rows),
        "待办口径": "仅列出由血缘影响样本同步生成的质量审计报告",
    })
