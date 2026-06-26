from __future__ import annotations

from typing import Any, Optional

from fastapi import APIRouter, HTTPException, Query

from app.db.supabase_client import get_supabase
from app.schemas.dashboard import (
    AspectAnalyticsItem,
    AspectRadarChartData,
    AspectRadarItem,
    AspectSegmentStats,
    AspectTrendChartData,
    AspectTrendPeriodPoint,
    AspectTrendYearPoint,
    CentralityChartData,
    CentralityItem,
    CommunityChartData,
    CommunityItem,
    EntityRankingChartData,
    EntityRankingItem,
    MonthlyReportData,
    PipelineActivityItem,
    PipelineActivityResponse,
    RankingTableItem,
    RankingTableResponse,
    SiteMonthlyReportResponse,
    StackedBarChartData,
    StackedBarChartSeries,
    SentimentAnalyticsResponse,
    TopEntitiesChartData,
    TopEntityItem,
    TrendAnalysisResponse,
    TrendDataPoint,
    VolumeTrendChartData,
    VolumeTrendPoint,
)

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/pipeline-activity", response_model=PipelineActivityResponse)
async def get_pipeline_activity(
    limit: int = Query(10, ge=1, le=100),
) -> PipelineActivityResponse:
    sb = get_supabase()
    activities: list[PipelineActivityItem] = []

    scrape_result = (
        sb.table("scrape_runs")
        .select("*")
        .order("scraped_at", desc=True)
        .limit(limit)
        .execute()
    )
    for sr in (scrape_result.data or []):
        activities.append(
            PipelineActivityItem(
                id=sr["id"],
                activity_type="scrape",
                run_id=sr.get("run_id"),
                status="completed",
                started_at=sr.get("scraped_at"),
                finished_at=sr.get("created_at"),
                total_reviews=sr.get("total_reviews"),
                new_reviews=sr.get("new_reviews"),
                details={"total_pages": sr.get("total_pages"), "storage_path": sr.get("storage_path")},
            )
        )

    analytics_result = (
        sb.table("analytics_runs")
        .select("*")
        .order("started_at", desc=True)
        .limit(limit)
        .execute()
    )
    for ar in (analytics_result.data or []):
        activities.append(
            PipelineActivityItem(
                id=ar["id"],
                activity_type="analytics",
                run_id=None,
                status=ar["status"],
                started_at=ar.get("started_at"),
                finished_at=ar.get("finished_at"),
                total_reviews=ar.get("review_count"),
                duration_seconds=ar.get("duration_seconds"),
                details={
                    "trigger_type": ar.get("trigger_type"),
                    "families_computed": ar.get("families_computed"),
                    "entity_count": ar.get("entity_count"),
                },
            )
        )

    activities.sort(key=lambda x: x.started_at or "", reverse=True)
    return PipelineActivityResponse(activities=activities[:limit], total=len(activities))


@router.get("/monthly-report/{site_id}", response_model=SiteMonthlyReportResponse)
async def get_site_monthly_report(
    site_id: int,
    year: int = Query(..., description="Year for the report"),
) -> SiteMonthlyReportResponse:
    sb = get_supabase()

    entity_result = (
        sb.table("entity_mentions")
        .select("review_id")
        .eq("entity_id", site_id)
        .limit(1)
        .execute()
    )
    if not entity_result.data:
        raise HTTPException(status_code=404, detail="Site not found")

    mentions_result = (
        sb.table("entity_mentions")
        .select("review_id")
        .eq("entity_id", site_id)
        .execute()
    )
    review_ids = [m["review_id"] for m in (mentions_result.data or [])]

    monthly_data: list[MonthlyReportData] = []
    if review_ids:
        reviews_result = (
            sb.table("cleaned_reviews")
            .select("year, month, rating, sentiment_class")
            .eq("year", year)
            .in_("review_id", review_ids)
            .execute()
        )
        month_map: dict[int, dict] = {}
        for r in (reviews_result.data or []):
            m = r["month"]
            if m not in month_map:
                month_map[m] = {"ratings": [], "positive": 0, "negative": 0, "count": 0}
            month_map[m]["count"] += 1
            if r.get("rating"):
                month_map[m]["ratings"].append(r["rating"])
            if r.get("sentiment_class") == "positive":
                month_map[m]["positive"] += 1
            elif r.get("sentiment_class") == "negative":
                month_map[m]["negative"] += 1

        for m in sorted(month_map.keys()):
            d = month_map[m]
            avg = round(sum(d["ratings"]) / max(len(d["ratings"]), 1), 2)
            monthly_data.append(
                MonthlyReportData(
                    year=year, month=m, review_count=d["count"],
                    avg_rating=avg, positive_count=d["positive"],
                    negative_count=d["negative"],
                )
            )

    aspects_result = (
        sb.table("aspect_metrics")
        .select("display_aspect, mention_count, positive_pct, negative_pct")
        .order("mention_count", desc=True)
        .limit(10)
        .execute()
    )

    return SiteMonthlyReportResponse(
        site_name=f"Site {site_id}",
        year=year,
        monthly_data=monthly_data,
        top_aspects=aspects_result.data or [],
    )


@router.get("/rankings", response_model=RankingTableResponse)
async def get_rankings(
    ranking_type: str = Query("by_mention"),
    limit: int = Query(50, ge=1, le=200),
) -> RankingTableResponse:
    sb = get_supabase()

    result = (
        sb.table("entity_rankings")
        .select("*")
        .eq("ranking_type", ranking_type)
        .order("rank_position", desc=False)
        .limit(limit)
        .execute()
    )

    rankings = [
        RankingTableItem(
            rank_position=r["rank_position"],
            display_name=r["display_name"],
            entity_type=r["entity_type"],
            score=r["score"],
            is_sacred=r["is_sacred"],
            metadata_=r.get("metadata"),
            computed_at=r["computed_at"],
        )
        for r in (result.data or [])
    ]

    return RankingTableResponse(ranking_type=ranking_type, rankings=rankings, total=len(rankings))


@router.get("/trends", response_model=TrendAnalysisResponse)
async def get_trend_analysis(
    granularity: str = Query("quarterly", description="monthly, quarterly, yearly"),
) -> TrendAnalysisResponse:
    sb = get_supabase()

    result = sb.table("cleaned_reviews").select("year, quarter, month, rating, sentiment_class").execute()
    rows = result.data or []

    if granularity == "yearly":
        groups: dict[int, dict] = {}
        for r in rows:
            y = r.get("year")
            if y is None:
                continue
            if y not in groups:
                groups[y] = {"ratings": [], "positive": 0, "count": 0}
            groups[y]["count"] += 1
            if r.get("rating"):
                groups[y]["ratings"].append(r["rating"])
            if r.get("sentiment_class") == "positive":
                groups[y]["positive"] += 1

        data = [
            TrendDataPoint(
                year=y, review_count=d["count"],
                avg_rating=round(sum(d["ratings"]) / max(len(d["ratings"]), 1), 2),
                positive_pct=round(d["positive"] * 100.0 / max(d["count"], 1), 1),
            )
            for y, d in sorted(groups.items())
        ]

    elif granularity == "monthly":
        groups = {}
        for r in rows:
            y, m = r.get("year"), r.get("month")
            if y is None or m is None:
                continue
            key = (y, m)
            if key not in groups:
                groups[key] = {"ratings": [], "positive": 0, "count": 0}
            groups[key]["count"] += 1
            if r.get("rating"):
                groups[key]["ratings"].append(r["rating"])
            if r.get("sentiment_class") == "positive":
                groups[key]["positive"] += 1

        data = [
            TrendDataPoint(
                year=y, month=m, review_count=d["count"],
                avg_rating=round(sum(d["ratings"]) / max(len(d["ratings"]), 1), 2),
                positive_pct=round(d["positive"] * 100.0 / max(d["count"], 1), 1),
            )
            for (y, m), d in sorted(groups.items())
        ]

    else:
        groups = {}
        for r in rows:
            y, q = r.get("year"), r.get("quarter")
            if y is None or q is None:
                continue
            key = (y, q)
            if key not in groups:
                groups[key] = {"ratings": [], "positive": 0, "count": 0}
            groups[key]["count"] += 1
            if r.get("rating"):
                groups[key]["ratings"].append(r["rating"])
            if r.get("sentiment_class") == "positive":
                groups[key]["positive"] += 1

        data = [
            TrendDataPoint(
                year=y, quarter=q, review_count=d["count"],
                avg_rating=round(sum(d["ratings"]) / max(len(d["ratings"]), 1), 2),
                positive_pct=round(d["positive"] * 100.0 / max(d["count"], 1), 1),
            )
            for (y, q), d in sorted(groups.items())
        ]

    return TrendAnalysisResponse(granularity=granularity, data=data)


@router.get("/sentiment", response_model=SentimentAnalyticsResponse)
async def get_sentiment_analytics(
    limit: int = Query(5, ge=1, le=200),
) -> SentimentAnalyticsResponse:
    sb = get_supabase()

    result = (
        sb.table("aspect_metrics")
        .select("*")
        .order("mention_count", desc=True)
        .limit(limit)
        .execute()
    )

    aspects = [
        AspectAnalyticsItem(
            display_aspect=a["display_aspect"],
            mention_count=a["mention_count"],
            positive_pct=a["positive_pct"],
            negative_pct=a["negative_pct"],
            neutral_pct=a["neutral_pct"],
            avg_sentiment_score=a.get("avg_sentiment_score"),
            trend_by_year=a.get("trend_by_year"),
            trend_by_period=a.get("trend_by_period"),
            by_trip_type=a.get("by_trip_type"),
            by_reviewer_type=a.get("by_reviewer_type"),
        )
        for a in (result.data or [])
    ]

    return SentimentAnalyticsResponse(aspects=aspects, total=len(aspects))


@router.get("/metrics-history")
async def get_metrics_history(
    metric_family: Optional[str] = Query(None),
    limit: int = Query(1, ge=1, le=50),
) -> list[dict[str, Any]]:
    sb = get_supabase()

    query = sb.table("metrics_history").select("*")
    if metric_family:
        query = query.eq("metric_family", metric_family)

    result = query.order("snapshot_date", desc=True).limit(limit).execute()

    return [
        {
            "id": m["id"],
            "snapshot_date": m["snapshot_date"],
            "metric_family": m["metric_family"],
            "metric_key": m["metric_key"],
            "metric_value": m.get("metric_value"),
            "schema_version": m.get("schema_version"),
        }
        for m in (result.data or [])
    ]


@router.get("/charts/sentiment-overview", response_model=StackedBarChartData)
async def get_sentiment_overview_chart(
    limit: int = Query(20, ge=1, le=200),
    min_mentions: int = Query(1, ge=0, description="Minimum mention count to include"),
) -> StackedBarChartData:
    sb = get_supabase()

    result = (
        sb.table("aspect_metrics")
        .select("display_aspect, mention_count, positive_pct, negative_pct, neutral_pct, avg_sentiment_score, computed_at")
        .order("mention_count", desc=True)
        .execute()
    )

    rows = [r for r in (result.data or []) if r.get("mention_count", 0) >= min_mentions][:limit]

    return StackedBarChartData(
        chart_type="stacked_bar",
        title="Aspect Sentiment Overview",
        description="Positive, neutral, and negative sentiment distribution across all aspects",
        labels=[r["display_aspect"] for r in rows],
        series=StackedBarChartSeries(
            positive=[r["positive_pct"] for r in rows],
            neutral=[r["neutral_pct"] for r in rows],
            negative=[r["negative_pct"] for r in rows],
        ),
        mention_counts=[r["mention_count"] for r in rows],
        avg_scores=[r.get("avg_sentiment_score") for r in rows],
        computed_at=rows[0]["computed_at"] if rows else None,
    )


@router.get("/charts/aspect-trend/{aspect}", response_model=AspectTrendChartData)
async def get_aspect_trend_chart(aspect: str) -> AspectTrendChartData:
    sb = get_supabase()

    result = (
        sb.table("aspect_metrics")
        .select("*")
        .eq("aspect", aspect)
        .execute()
    )

    if not result.data:
        raise HTTPException(status_code=404, detail=f"Aspect '{aspect}' not found")

    row = result.data[0]

    trend_by_year = []
    for t in (row.get("trend_by_year") or []):
        mc = t.get("mention_count", 0)
        pos = t.get("positive_count", 0)
        neg = t.get("negative_count", 0)
        pos_pct = round(pos * 100.0 / mc, 1) if mc else 0.0
        neg_pct = round(neg * 100.0 / mc, 1) if mc else 0.0
        trend_by_year.append(AspectTrendYearPoint(
            year=t["year"],
            avg_score=t.get("avg_score"),
            mention_count=mc,
            positive_count=pos,
            negative_count=neg,
            positive_pct=pos_pct,
            negative_pct=neg_pct,
        ))

    trend_by_period = [
        AspectTrendPeriodPoint(
            period=t.get("period"),
            avg_score=t.get("avg_score"),
            mention_count=t.get("mention_count"),
        )
        for t in (row.get("trend_by_period") or [])
    ]

    by_trip_type = None
    raw_trip = row.get("by_trip_type")
    if raw_trip and isinstance(raw_trip, dict):
        by_trip_type = {
            k: AspectSegmentStats(
                positive_pct=v.get("positive_pct", 0),
                negative_pct=v.get("negative_pct", 0),
                avg_score=v.get("avg_score"),
                mention_count=v.get("mention_count"),
            )
            for k, v in raw_trip.items()
        }

    by_reviewer_type = None
    raw_reviewer = row.get("by_reviewer_type")
    if raw_reviewer and isinstance(raw_reviewer, dict):
        by_reviewer_type = {
            k: AspectSegmentStats(
                positive_pct=v.get("positive_pct", 0),
                negative_pct=v.get("negative_pct", 0),
                avg_score=v.get("avg_score"),
                mention_count=v.get("mention_count"),
            )
            for k, v in raw_reviewer.items()
        }

    return AspectTrendChartData(
        chart_type="line",
        title=f"Trend Analysis: {row['display_aspect']}",
        description=f"Sentiment trend breakdown for aspect '{row['display_aspect']}'",
        aspect=row["aspect"],
        display_aspect=row["display_aspect"],
        mention_count=row["mention_count"],
        avg_sentiment_score=row.get("avg_sentiment_score"),
        trend_by_year=trend_by_year,
        trend_by_period=trend_by_period,
        by_trip_type=by_trip_type,
        by_reviewer_type=by_reviewer_type,
        computed_at=row.get("computed_at"),
    )


@router.get("/charts/entity-rankings", response_model=EntityRankingChartData)
async def get_entity_rankings_chart(
    ranking_type: str = Query("by_mention"),
    entity_type: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=200),
) -> EntityRankingChartData:
    sb = get_supabase()

    query = (
        sb.table("entity_rankings")
        .select("rank_position, display_name, score, is_sacred, entity_type, metadata, computed_at")
        .eq("ranking_type", ranking_type)
        .order("rank_position", desc=False)
        .limit(limit)
    )

    if entity_type:
        query = query.eq("entity_type", entity_type)

    result = query.execute()
    rows = result.data or []

    items = [
        EntityRankingItem(
            rank=r["rank_position"],
            name=r["display_name"],
            score=r["score"],
            is_sacred=r["is_sacred"],
            entity_type=r["entity_type"],
            metadata_=r.get("metadata"),
        )
        for r in rows
    ]

    return EntityRankingChartData(
        chart_type="horizontal_bar",
        title=f"Entity Rankings ({ranking_type})",
        description=f"Top entities ranked by {ranking_type.replace('_', ' ')}" + (f" ({entity_type})" if entity_type else ""),
        ranking_type=ranking_type,
        items=items,
        total=len(items),
        computed_at=rows[0]["computed_at"] if rows else None,
    )


@router.get("/charts/volume-trend", response_model=VolumeTrendChartData)
async def get_volume_trend_chart(
    granularity: str = Query("quarterly", description="monthly, quarterly, yearly"),
) -> VolumeTrendChartData:
    sb = get_supabase()

    result = sb.table("cleaned_reviews").select("year, quarter, month, rating, sentiment_class").execute()
    rows = result.data or []

    groups: dict[tuple, dict] = {}

    for r in rows:
        y = r.get("year")
        if y is None:
            continue

        if granularity == "yearly":
            key = (y,)
            label = str(y)
        elif granularity == "monthly":
            m = r.get("month")
            if m is None:
                continue
            key = (y, m)
            label = f"{y}-{m:02d}"
        else:
            q = r.get("quarter")
            if q is None:
                continue
            key = (y, q)
            label = f"{y}-Q{q}"

        if key not in groups:
            groups[key] = {"label": label, "ratings": [], "positive": 0, "count": 0}
        groups[key]["count"] += 1
        if r.get("rating"):
            groups[key]["ratings"].append(r["rating"])
        if r.get("sentiment_class") == "positive":
            groups[key]["positive"] += 1

    data = [
        VolumeTrendPoint(
            label=d["label"],
            volume=d["count"],
            avg_rating=round(sum(d["ratings"]) / max(len(d["ratings"]), 1), 2),
            positive_pct=round(d["positive"] * 100.0 / max(d["count"], 1), 1),
        )
        for _, d in sorted(groups.items())
    ]

    return VolumeTrendChartData(
        chart_type="dual_axis_line",
        title="Review Volume Trend",
        description=f"Review volume and sentiment over time ({granularity} granularity)",
        granularity=granularity,
        data=data,
    )


@router.get("/charts/aspect-radar", response_model=AspectRadarChartData)
async def get_aspect_radar_chart(
    min_mentions: int = Query(10, ge=0, description="Minimum mention count to include"),
    limit: int = Query(20, ge=1, le=50),
) -> AspectRadarChartData:
    sb = get_supabase()

    result = (
        sb.table("aspect_metrics")
        .select("aspect, display_aspect, mention_count, positive_pct, negative_pct, neutral_pct, avg_sentiment_score, computed_at")
        .execute()
    )

    rows = [r for r in (result.data or []) if r.get("mention_count", 0) >= min_mentions]
    rows.sort(key=lambda r: r.get("mention_count", 0), reverse=True)
    rows = rows[:limit]

    aspects = [
        AspectRadarItem(
            aspect=r["aspect"],
            display_aspect=r["display_aspect"],
            mention_count=r["mention_count"],
            positive_pct=r["positive_pct"],
            negative_pct=r["negative_pct"],
            neutral_pct=r["neutral_pct"],
            avg_sentiment_score=r.get("avg_sentiment_score"),
            score_normalized=round(r.get("avg_sentiment_score", 0) * 100) if r.get("avg_sentiment_score") is not None else None,
        )
        for r in rows
    ]

    return AspectRadarChartData(
        chart_type="radar",
        title="Aspect Sentiment Radar",
        description=f"Positive sentiment and avg score per aspect (min {min_mentions} mentions)",
        aspects=aspects,
        total=len(aspects),
        computed_at=rows[0].get("computed_at") if rows else None,
    )


@router.get("/charts/top-entities", response_model=TopEntitiesChartData)
async def get_top_entities_chart(
    limit: int = Query(12, ge=1, le=50),
) -> TopEntitiesChartData:
    sb = get_supabase()

    result = (
        sb.table("entities")
        .select("display_name, entity_type, mention_count")
        .order("mention_count", desc=True)
        .limit(limit)
        .execute()
    )

    items = [
        TopEntityItem(
            rank=i + 1,
            display_name=r["display_name"],
            entity_type=r["entity_type"],
            mention_count=r["mention_count"],
        )
        for i, r in enumerate(result.data or [])
    ]

    return TopEntitiesChartData(
        chart_type="table",
        title="Top Discussed Entities",
        description=f"Top {limit} most mentioned entities across all reviews",
        items=items,
        total=len(items),
    )


@router.get("/charts/centrality", response_model=CentralityChartData)
async def get_centrality_chart(
    limit: int = Query(10, ge=1, le=50),
) -> CentralityChartData:
    sb = get_supabase()

    result = (
        sb.table("metrics_current")
        .select("metric_value")
        .eq("metric_family", "intelligence")
        .eq("metric_key", "entity_type_centrality")
        .execute()
    )

    if not result.data:
        return CentralityChartData(
            chart_type="bar",
            title="Entity Type Centrality",
            description="Average degree centrality by entity type",
            items=[],
            total=0,
        )

    data = result.data[0]["metric_value"]
    data.sort(key=lambda x: x.get("avg_degree_centrality", 0), reverse=True)
    data = data[:limit]

    items = [
        CentralityItem(
            rank=i + 1,
            entity_type=r["entity_type"],
            entity_count=r.get("entity_count", 0),
            avg_degree_centrality=r.get("avg_degree_centrality", 0),
            avg_mention_count=r.get("avg_mention_count", 0),
        )
        for i, r in enumerate(data)
    ]

    return CentralityChartData(
        chart_type="bar",
        title="Entity Type Centrality",
        description=f"Top {limit} entity types by average degree centrality in the knowledge graph",
        items=items,
        total=len(items),
    )


@router.get("/charts/communities", response_model=CommunityChartData)
async def get_communities_chart(
    limit: int = Query(10, ge=1, le=50),
) -> CommunityChartData:
    sb = get_supabase()

    result = (
        sb.table("metrics_current")
        .select("metric_value")
        .eq("metric_family", "social_computing")
        .eq("metric_key", "community_structure")
        .execute()
    )

    if not result.data:
        return CommunityChartData(
            chart_type="bar",
            title="Community Size Distribution",
            description="Top communities in the knowledge graph",
            algorithm="",
            modularity=0,
            community_count=0,
            items=[],
            total=0,
        )

    val = result.data[0]["metric_value"]
    communities = val.get("communities", [])
    communities.sort(key=lambda c: c.get("size", 0), reverse=True)
    communities = communities[:limit]

    items = [
        CommunityItem(
            rank=i + 1,
            community_id=c.get("community_id", 0),
            size=c.get("size", 0),
            dominant_type=c.get("dominant_type", "unknown"),
            type_distribution=c.get("type_distribution"),
        )
        for i, c in enumerate(communities)
    ]

    return CommunityChartData(
        chart_type="bar",
        title="Community Size Distribution",
        description=f"Top {limit} largest communities in the knowledge graph",
        algorithm=val.get("algorithm", "louvain"),
        modularity=val.get("modularity", 0),
        community_count=val.get("community_count", 0),
        items=items,
        total=len(items),
    )
