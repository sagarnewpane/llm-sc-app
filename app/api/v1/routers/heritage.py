from __future__ import annotations

from typing import Any, Optional

from fastapi import APIRouter, Query

from app.db.supabase_client import get_supabase
from app.schemas.dashboard import (
    CriticalFinding,
    ExecutiveSummaryResponse,
    EmotionalAnchorItem,
    EmotionalAnchorsResponse,
    HeritageHealthItem,
    HeritageHealthResponse,
    LLRecommendation,
    LLMRecommendationResponse,
    MetaPathItem,
    MetaPathResponse,
    MotifItem,
    MotifResponse,
    SacredSecularNetworkResponse,
    SemanticTrajectoryItem,
    SemanticTrajectoriesResponse,
    TemporalEvolutionResponse,
    TopInsight,
    DualEmotionResponse,
)

router = APIRouter(prefix="/heritage", tags=["heritage"])


def _get_metric(family: str, key: str) -> Any | None:
    sb = get_supabase()
    result = (
        sb.table("metrics_current")
        .select("metric_value")
        .eq("metric_family", family)
        .eq("metric_key", key)
        .execute()
    )
    if result.data:
        return result.data[0]["metric_value"]
    return None


@router.get("/executive-summary", response_model=ExecutiveSummaryResponse)
async def get_executive_summary() -> ExecutiveSummaryResponse:
    val = _get_metric("narratives", "executive_summary")
    if not val:
        return ExecutiveSummaryResponse(
            summary="", key_metrics={}, top_insights=[], critical_count=0, high_priority_count=0
        )
    insights = []
    for i in val.get("top_insights", []):
        insights.append(
            TopInsight(
                title=i.get("title", ""),
                priority=i.get("priority", "medium"),
                aspect=i.get("aspect", ""),
                negative_pct=i.get("negative_pct", 0),
                narrative=i.get("narrative", ""),
            )
        )
    return ExecutiveSummaryResponse(
        summary=val.get("summary", ""),
        key_metrics=val.get("key_metrics", {}),
        top_insights=insights,
        generated_for=val.get("generated_for", ""),
        critical_count=val.get("critical_count", 0),
        high_priority_count=val.get("high_priority_count", 0),
    )


@router.get("/health-report", response_model=HeritageHealthResponse)
async def get_heritage_health_report() -> HeritageHealthResponse:
    val = _get_metric("narratives", "heritage_health_report")
    if not val:
        return HeritageHealthResponse(items=[], total=0)
    items = []
    for h in val:
        items.append(
            HeritageHealthItem(
                title=h.get("title", ""),
                audience=h.get("audience", ""),
                category=h.get("category", ""),
                priority=h.get("priority", "medium"),
                narrative=h.get("narrative", ""),
                evidence=h.get("evidence"),
                recommended_actions=h.get("recommended_actions", []),
            )
        )
    return HeritageHealthResponse(items=items, total=len(items))


@router.get("/emotional-anchors", response_model=EmotionalAnchorsResponse)
async def get_emotional_anchors(
    limit: int = Query(20, ge=1, le=100),
) -> EmotionalAnchorsResponse:
    val = _get_metric("social_computing", "emotional_anchors")
    if not val:
        return EmotionalAnchorsResponse(anchors=[], total=0)
    val.sort(key=lambda x: x.get("co_mention_count", 0), reverse=True)
    val = val[:limit]
    items = [
        EmotionalAnchorItem(
            emotion=a.get("emotion", ""),
            anchored_type=a.get("anchored_type", ""),
            anchored_entity=a.get("anchored_entity", ""),
            co_mention_count=a.get("co_mention_count", 0),
        )
        for a in val
    ]
    return EmotionalAnchorsResponse(anchors=items, total=len(items))


@router.get("/semantic-trajectories", response_model=SemanticTrajectoriesResponse)
async def get_semantic_trajectories(
    trend: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=100),
) -> SemanticTrajectoriesResponse:
    val = _get_metric("social_computing", "semantic_trajectories")
    if not val:
        return SemanticTrajectoriesResponse(trajectories=[], total=0)
    if trend:
        val = [t for t in val if t.get("trend") == trend]
    val.sort(key=lambda x: x.get("total_mentions", 0), reverse=True)
    val = val[:limit]
    items = [
        SemanticTrajectoryItem(
            trend=t.get("trend", ""),
            entity_type=t.get("entity_type", ""),
            display_name=t.get("display_name", ""),
            total_mentions=t.get("total_mentions", 0),
            yearly_mentions=t.get("yearly_mentions", []),
        )
        for t in val
    ]
    return SemanticTrajectoriesResponse(trajectories=items, total=len(items))


@router.get("/meta-paths", response_model=MetaPathResponse)
async def get_meta_paths() -> MetaPathResponse:
    val = _get_metric("social_computing", "meta_path_analysis")
    if not val:
        return MetaPathResponse(top_patterns=[], total_paths=0)
    items = [
        MetaPathItem(
            source_type=p.get("source_type", ""),
            target_type=p.get("target_type", ""),
            path_count=p.get("path_count", 0),
        )
        for p in val.get("top_patterns", [])
    ]
    return MetaPathResponse(top_patterns=items, total_paths=sum(p.path_count for p in items))


@router.get("/motifs", response_model=MotifResponse)
async def get_motifs() -> MotifResponse:
    val = _get_metric("social_computing", "motif_mining")
    if not val:
        return MotifResponse(motifs=[], triad_count=0, unique_motif_types=0)
    items = [
        MotifItem(
            label=m.get("label", ""),
            count=m.get("count", 0),
            entity_types=m.get("entity_types", []),
        )
        for m in val.get("motifs", [])
    ]
    return MotifResponse(
        motifs=items,
        triad_count=val.get("triad_count", 0),
        unique_motif_types=val.get("unique_motif_types", 0),
    )


@router.get("/sacred-secular-network", response_model=SacredSecularNetworkResponse)
async def get_sacred_secular_network() -> SacredSecularNetworkResponse:
    val = _get_metric("social_computing", "sacred_secular_network")
    if not val:
        return SacredSecularNetworkResponse(
            edge_matrix=[], bridge_ratio=0, cross_domain_edges=0,
            sacred_sacred_edges=0, secular_secular_edges=0,
        )
    return SacredSecularNetworkResponse(
        edge_matrix=val.get("edge_matrix", []),
        bridge_ratio=val.get("bridge_ratio", 0),
        cross_domain_edges=val.get("cross_domain_edges", 0),
        sacred_sacred_edges=val.get("sacred_sacred_edges", 0),
        secular_secular_edges=val.get("secular_secular_edges", 0),
    )


@router.get("/temporal-evolution", response_model=TemporalEvolutionResponse)
async def get_temporal_evolution() -> TemporalEvolutionResponse:
    val = _get_metric("social_computing", "temporal_evolution")
    if not val:
        return TemporalEvolutionResponse(timeline=[], total_years=0)
    return TemporalEvolutionResponse(
        timeline=val.get("timeline", []),
        total_years=val.get("total_years", 0),
    )


@router.get("/dual-emotions", response_model=DualEmotionResponse)
async def get_dual_emotions() -> DualEmotionResponse:
    val = _get_metric("intelligence", "dual_emotion_reviews")
    if not val:
        return DualEmotionResponse(
            total_reviews=0, pct_of_reviews=0,
            dual_valence_entities=0, dual_emotion_review_count=0,
        )
    return DualEmotionResponse(
        total_reviews=val.get("total_reviews", 0),
        pct_of_reviews=val.get("pct_of_reviews", 0),
        dual_valence_entities=val.get("dual_valence_entities", 0),
        dual_emotion_review_count=val.get("dual_emotion_review_count", 0),
    )


@router.get("/llm-recommendations", response_model=LLMRecommendationResponse)
async def get_llm_recommendations() -> LLMRecommendationResponse:
    """Generate AI-powered heritage recommendations using LLM analysis of all site data."""
    from app.services.llm_recommendations import generate_recommendations
    result = generate_recommendations()
    return LLMRecommendationResponse(
        narrative_summary=result.get("narrative_summary", ""),
        critical_findings=[
            CriticalFinding(
                finding=f.get("finding", ""),
                explanation=f.get("explanation", ""),
                evidence=f.get("evidence", ""),
                impact=f.get("impact", ""),
                urgency=f.get("urgency", "medium"),
            )
            for f in result.get("critical_findings", [])
        ],
        recommendations=[
            LLRecommendation(
                title=r.get("title", ""),
                rationale=r.get("rationale", ""),
                expected_outcome=r.get("expected_outcome", ""),
                stakeholders=r.get("stakeholders", []),
                effort=r.get("effort", "medium"),
                timeline=r.get("timeline", "short_term"),
            )
            for r in result.get("recommendations", [])
        ],
        heritage_considerations=result.get("heritage_considerations", ""),
        error=result.get("error"),
    )
