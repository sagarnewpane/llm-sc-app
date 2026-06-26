from __future__ import annotations

from typing import Any, Optional

from fastapi import APIRouter, HTTPException, Query

from app.db.supabase_client import get_supabase
from app.schemas.dashboard import (
    AIInsightsResponse,
    DraftResponseRequest,
    DraftResponseResponse,
    GenerateActionPlanRequest,
    GenerateActionPlanResponse,
    IssueDetailResponse,
    NarrativeInsightItem,
    RecurringProblemItem,
    RecurringProblemsResponse,
)

router = APIRouter(prefix="/ai", tags=["ai-insights"])


def _priority_order(p: str) -> int:
    return {"high": 1, "medium": 2, "low": 3}.get(p, 4)


@router.get("/insights", response_model=AIInsightsResponse)
async def get_ai_insights(
    category: Optional[str] = Query(None),
    audience: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=100),
) -> AIInsightsResponse:
    sb = get_supabase()

    query = sb.table("narrative_insights").select("*").eq("is_active", True)
    if category:
        query = query.eq("category", category)
    if audience:
        query = query.eq("audience", audience)

    result = query.execute()
    insights_raw = result.data or []
    sorted_insights = sorted(insights_raw, key=lambda x: (_priority_order(x.get("priority", "")), -x.get("id", 0)))
    limited = sorted_insights[:limit]

    items = [
        NarrativeInsightItem(
            id=i["id"],
            category=i["category"],
            priority=i["priority"],
            title=i["title"],
            narrative=i["narrative"],
            evidence=i.get("evidence"),
            recommended_actions=i.get("recommended_actions"),
            audience=i["audience"],
            is_active=i["is_active"],
            computed_at=i["computed_at"],
        )
        for i in limited
    ]

    return AIInsightsResponse(insights=items, total=len(items))


@router.get("/recurring-problems", response_model=RecurringProblemsResponse)
async def get_recurring_problems(
    negative_threshold: float = Query(0.3, ge=0.0, le=1.0),
    limit: int = Query(20, ge=1, le=50),
) -> RecurringProblemsResponse:
    sb = get_supabase()

    result = (
        sb.table("aspect_metrics")
        .select("*")
        .gt("negative_pct", negative_threshold)
        .order("negative_pct", desc=True)
        .order("mention_count", desc=True)
        .limit(limit)
        .execute()
    )

    items = [
        RecurringProblemItem(
            display_aspect=a["display_aspect"],
            mention_count=a["mention_count"],
            negative_pct=a["negative_pct"],
            avg_sentiment_score=a.get("avg_sentiment_score"),
            trend_by_year=a.get("trend_by_year"),
        )
        for a in (result.data or [])
    ]

    return RecurringProblemsResponse(problems=items)


@router.get("/insights/{insight_id}", response_model=IssueDetailResponse)
async def get_issue_detail(insight_id: int) -> IssueDetailResponse:
    sb = get_supabase()

    result = sb.table("narrative_insights").select("*").eq("id", insight_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Insight not found")

    insight = result.data[0]
    evidence_list: list[dict[str, Any]] = []

    if insight.get("evidence") and isinstance(insight["evidence"], dict):
        aspect = insight["evidence"].get("aspect")
        if aspect:
            sentiments_result = (
                sb.table("sentiment_mentions")
                .select("*, review:cleaned_reviews(review_id, text_clean, rating, date)")
                .eq("sentiment_label", "negative")
                .limit(20)
                .execute()
            )
            for sm in (sentiments_result.data or []):
                if sm.get("review"):
                    evidence_list.append({
                        "review_id": sm["review"]["review_id"],
                        "text_clean": sm["review"]["text_clean"],
                        "rating": sm["review"].get("rating"),
                        "date": sm["review"].get("date"),
                        "sentiment_score": sm.get("sentiment_score"),
                        "evidence": sm.get("evidence"),
                    })

    return IssueDetailResponse(
        insight=NarrativeInsightItem(
            id=insight["id"],
            category=insight["category"],
            priority=insight["priority"],
            title=insight["title"],
            narrative=insight["narrative"],
            evidence=insight.get("evidence"),
            recommended_actions=insight.get("recommended_actions"),
            audience=insight["audience"],
            is_active=insight["is_active"],
            computed_at=insight["computed_at"],
        ),
        supporting_reviews=evidence_list,
    )


@router.get("/recommendations")
async def get_resolution_recommendations(
    audience: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=100),
) -> list[dict[str, Any]]:
    sb = get_supabase()

    query = sb.table("narrative_insights").select("*").eq("is_active", True)
    if audience:
        query = query.eq("audience", audience)

    # 1. Remove the .order() from Supabase since text sorting is unreliable here
    result = query.limit(limit).execute()
    print(result)
    data = result.data or []

    # 2. Define a priority weight mapping (higher number = higher priority)
    priority_weights = {
        "critical": 4,
        "high": 3,
        "medium": 2,
        "low": 1
    }

    # 3. Sort the Python list using the mapping (default to 0 if an unknown priority appears)
    sorted_data = sorted(
        data, 
        key=lambda x: priority_weights.get(str(x.get("priority", "")).lower(), 0), 
        reverse=True
    )

    return [
        {
            "id": i["id"],
            "title": i["title"],
            "narrative": i["narrative"],
            "recommended_actions": i.get("recommended_actions"),
            "audience": i["audience"],
            "priority": i["priority"],
            "category": i["category"],
        }
        for i in sorted_data
    ]


@router.post("/draft-response", response_model=DraftResponseResponse)
async def draft_review_response(request: DraftResponseRequest) -> DraftResponseResponse:
    """Generate an LLM-drafted response to a negative visitor review."""
    from app.services.llm_recommendations import draft_review_response as _draft

    result = _draft(review_id=request.review_id, tone=request.tone or "professional")
    if result.get("error") and not result.get("draft"):
        raise HTTPException(status_code=500, detail=result["error"])

    return DraftResponseResponse(
        review_id=result.get("review_id", request.review_id),
        draft=result.get("draft", ""),
        tone=result.get("tone", request.tone or "professional"),
        reviewer_name=result.get("reviewer_name"),
        original_rating=result.get("original_rating"),
        original_sentiment=result.get("original_sentiment"),
        error=result.get("error"),
    )


@router.post("/generate-action-plan", response_model=GenerateActionPlanResponse)
async def generate_action_plan(request: GenerateActionPlanRequest) -> GenerateActionPlanResponse:
    """Generate structured action items from an insight, recommendation, or alert."""
    from app.services.llm_recommendations import generate_action_plan as _plan

    result = _plan(
        source_type=request.source_type,
        title=request.title,
        context=request.context,
        num_tasks=request.num_tasks or 5,
    )
    if result.get("error") and not result.get("action_items"):
        raise HTTPException(status_code=500, detail=result["error"])

    return GenerateActionPlanResponse(
        source_type=result.get("source_type", request.source_type),
        source_title=result.get("source_title", request.title),
        action_items=result.get("action_items", []),
        summary=result.get("summary", ""),
        error=result.get("error"),
    )