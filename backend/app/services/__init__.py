"""领域服务注册表：通用资源路由按模块 key 分派到独立业务服务。"""
from __future__ import annotations

from app.services.base import BaseModuleService
from app.services.entity_extract import EntityExtractService
from app.services.relation_model import RelationModelService
from app.services.graph_build import GraphBuildService
from app.services.graph_search import GraphSearchService
from app.services.entity_link import EntityLinkService
from app.services.disambig import DisambigService
from app.services.path_reason import PathReasonService
from app.services.subgraph_exp import SubgraphExpService
from app.services.graph_evolve import GraphEvolveService
from app.services.quality_audit import QualityAuditService
from app.services.metadata_tag import MetadataTagService
from app.services.taxonomy import TaxonomyService
from app.services.query_cache import QueryCacheService
from app.services.graph_index import GraphIndexService
from app.services.data_lineage import DataLineageService
from app.services.reco_engine import RecoEngineService
from app.services.entity_merge import EntityMergeService
from app.services.batch_load import BatchLoadService
from app.services.report_gen import ReportGenService
from app.services.graph_compare import GraphCompareService
from app.services.schedule_job import ScheduleJobService
from app.services.govern_dash import GovernDashService

SERVICES: dict[str, BaseModuleService] = {
    "entity_extract": EntityExtractService(),
    "relation_model": RelationModelService(),
    "graph_build": GraphBuildService(),
    "graph_search": GraphSearchService(),
    "entity_link": EntityLinkService(),
    "disambig": DisambigService(),
    "path_reason": PathReasonService(),
    "subgraph_exp": SubgraphExpService(),
    "graph_evolve": GraphEvolveService(),
    "quality_audit": QualityAuditService(),
    "metadata_tag": MetadataTagService(),
    "taxonomy": TaxonomyService(),
    "query_cache": QueryCacheService(),
    "graph_index": GraphIndexService(),
    "data_lineage": DataLineageService(),
    "reco_engine": RecoEngineService(),
    "entity_merge": EntityMergeService(),
    "batch_load": BatchLoadService(),
    "report_gen": ReportGenService(),
    "graph_compare": GraphCompareService(),
    "schedule_job": ScheduleJobService(),
    "govern_dash": GovernDashService(),
}


def service_for(module: str) -> BaseModuleService | None:
    return SERVICES.get(module)
