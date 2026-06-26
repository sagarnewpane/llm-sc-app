from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from app.db.supabase_client import get_supabase
from app.schemas.dashboard import (
    NetworkEdge,
    NetworkNode,
    RankingTableItem,
    RankingTableResponse,
    SemanticNetworkResponse,
    SiteAspectItem,
    SiteDetailResponse,
    SiteOverview,
    SiteRelatedEntity,
    SummaryStats,
    TopSiteItem,
    TopSitesResponse,
)

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/summary", response_model=SummaryStats)
async def get_summary_stats() -> SummaryStats:
    sb = get_supabase()

    kpi_result = (
        sb.table("metrics_current")
        .select("metric_value")
        .eq("metric_family", "overview")
        .eq("metric_key", "kpi_summary")
        .execute()
    )
    if not kpi_result.data:
        raise HTTPException(
            status_code=404,
            detail="Overview metrics not yet computed. Run the analytics pipeline first.",
        )
    kpi = kpi_result.data[0]["metric_value"]

    sentiment_result = (
        sb.table("metrics_current")
        .select("metric_value")
        .eq("metric_family", "overview")
        .eq("metric_key", "sentiment_share")
        .execute()
    )
    sentiment_rows = sentiment_result.data[0]["metric_value"] if sentiment_result.data else []
    positive_entry = next((s for s in sentiment_rows if s.get("sentiment_class") == "positive"), {})
    positive_count = positive_entry.get("count", 0)
    positive_pct = positive_entry.get("percentage", 0.0)

    network_result = (
        sb.table("metrics_current")
        .select("metric_value")
        .eq("metric_family", "intelligence")
        .eq("metric_key", "network_summary")
        .execute()
    )
    network = network_result.data[0]["metric_value"] if network_result.data else {}

    return SummaryStats(
        total_reviews=kpi.get("total_reviews", 0),
        avg_rating=kpi.get("avg_rating", 0.0),
        positive_count=positive_count,
        positive_pct=positive_pct,
        total_entities=network.get("total_entities", 0),
    )


@router.get("/top-sites", response_model=TopSitesResponse)
async def get_top_sites(
    ranking_type: str = Query("by_mention", description="by_mention, by_sentiment, combined"),
    entity_type: str = Query("PLACE", description="Entity type filter"),
    limit: int = Query(10, ge=1, le=50),
) -> TopSitesResponse:
    sb = get_supabase()

    result = (
        sb.table("entity_rankings")
        .select("*")
        .eq("ranking_type", ranking_type)
        .eq("entity_type", entity_type)
        .order("rank_position", desc=False)
        .limit(limit)
        .execute()
    )

    sites = [
        TopSiteItem(
            rank_position=r["rank_position"],
            display_name=r["display_name"],
            entity_type=r["entity_type"],
            score=r["score"],
            is_sacred=r["is_sacred"],
            metadata_=r.get("metadata"),
        )
        for r in (result.data or [])
    ]

    return TopSitesResponse(ranking_type=ranking_type, sites=sites)


@router.get("/sites/{site_id}", response_model=SiteDetailResponse)
async def get_site_detail(site_id: int) -> SiteDetailResponse:
    sb = get_supabase()

    entity_result = (
        sb.table("entities")
        .select("*")
        .eq("id", site_id)
        .eq("entity_type", "PLACE")
        .execute()
    )
    if not entity_result.data:
        raise HTTPException(status_code=404, detail="Site not found")

    entity = entity_result.data[0]
    canonical_name = entity["canonical_name"]

    sentiment_result = (
        sb.table("sentiments")
        .select("*")
        .eq("aspect", canonical_name)
        .execute()
    )
    sentiment = sentiment_result.data[0] if sentiment_result.data else None

    site = SiteOverview(
        entity_id=entity["id"],
        display_name=entity["display_name"],
        entity_type=entity["entity_type"],
        mention_count=entity.get("mention_count"),
        positive_count=sentiment.get("positive_count") if sentiment else None,
        negative_count=sentiment.get("negative_count") if sentiment else None,
        neutral_count=sentiment.get("neutral_count") if sentiment else None,
        avg_sentiment_score=sentiment.get("avg_sentiment_score") if sentiment else None,
    )

    mentions_result = (
        sb.table("entity_mentions")
        .select("review_id")
        .eq("entity_id", site_id)
        .limit(50)
        .execute()
    )
    review_ids = [m["review_id"] for m in (mentions_result.data or [])]

    aspects = []
    if review_ids:
        sentiments_result = (
            sb.table("sentiment_mentions")
            .select("*")
            .in_("review_id", review_ids)
            .order("sentiment_score", desc=True)
            .limit(20)
            .execute()
        )
        aspects = [
            SiteAspectItem(
                aspect_raw=s.get("aspect_raw"),
                sentiment_label=s.get("sentiment_label"),
                sentiment_score=s.get("sentiment_score"),
                evidence=s.get("evidence"),
            )
            for s in (sentiments_result.data or [])
        ]

    relations_result = (
        sb.table("relations")
        .select("*, target:entities!relations_target_entity_id_fkey(display_name, entity_type)")
        .eq("source_entity_id", site_id)
        .order("weight", desc=True)
        .limit(10)
        .execute()
    )
    related = [
        SiteRelatedEntity(
            display_name=r["target"]["display_name"],
            entity_type=r["target"]["entity_type"],
            relation_type=r["relation_type"],
            weight=r.get("weight"),
        )
        for r in (relations_result.data or [])
        if r.get("target")
    ]

    return SiteDetailResponse(site=site, top_aspects=aspects, related_entities=related)


@router.get("/semantic-network", response_model=SemanticNetworkResponse)
async def get_semantic_network(
    min_mentions: int = Query(5, ge=1),
    min_weight: int = Query(2, ge=1),
    limit: int = Query(200, ge=1, le=500),
) -> SemanticNetworkResponse:
    sb = get_supabase()

    nodes_result = (
        sb.table("entities")
        .select("id, display_name, entity_type, mention_count")
        .gt("mention_count", min_mentions)
        .order("mention_count", desc=True)
        .limit(limit)
        .execute()
    )
    nodes = [
        NetworkNode(
            id=e["id"],
            display_name=e["display_name"],
            entity_type=e["entity_type"],
            mention_count=e.get("mention_count") or 0,
        )
        for e in (nodes_result.data or [])
    ]

    node_ids = {n.id for n in nodes}
    edges_result = (
        sb.table("relations")
        .select("source_entity_id, target_entity_id, relation_type, weight")
        .gt("weight", min_weight)
        .order("weight", desc=True)
        .limit(limit * 2)
        .execute()
    )
    edges = [
        NetworkEdge(
            source=r["source_entity_id"],
            target=r["target_entity_id"],
            relation_type=r["relation_type"],
            weight=r.get("weight") or 0,
        )
        for r in (edges_result.data or [])
        if r["source_entity_id"] in node_ids and r["target_entity_id"] in node_ids
    ]

    return SemanticNetworkResponse(
        nodes=nodes,
        edges=edges,
        total_nodes=len(nodes),
        total_edges=len(edges),
    )
