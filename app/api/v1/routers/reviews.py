from __future__ import annotations

import math
from typing import Any, Optional

from fastapi import APIRouter, HTTPException, Query

from app.db.supabase_client import get_supabase
from app.schemas.dashboard import (
    AspectGroupedReviews,
    ExportResponse,
    ExportReviewItem,
    ReviewDetailResponse,
    ReviewFilterOptions,
    ReviewFilters,
    ReviewListItem,
    ReviewListResponse,
    ReviewsByAspectResponse,
)

router = APIRouter(prefix="/reviews", tags=["reviews"])


def _build_review_query(
    sb: Any,
    sentiment: Optional[str] = None,
    rating: Optional[int] = None,
    min_rating: Optional[int] = None,
    max_rating: Optional[int] = None,
    year: Optional[int] = None,
    month: Optional[int] = None,
    quarter: Optional[int] = None,
    trip_type: Optional[str] = None,
    reviewer_type: Optional[str] = None,
    has_sacred_content: Optional[bool] = None,
    has_ritual: Optional[bool] = None,
    has_festival: Optional[bool] = None,
    language: Optional[str] = None,
    search: Optional[str] = None,
) -> Any:
    query = sb.table("cleaned_reviews").select("*")
    if sentiment:
        query = query.eq("sentiment_class", sentiment)
    if rating is not None:
        query = query.eq("rating", rating)
    if min_rating is not None:
        query = query.gte("rating", min_rating)
    if max_rating is not None:
        query = query.lte("rating", max_rating)
    if year is not None:
        query = query.eq("year", year)
    if month is not None:
        query = query.eq("month", month)
    if quarter is not None:
        query = query.eq("quarter", quarter)
    if trip_type:
        query = query.eq("trip_type", trip_type)
    if reviewer_type:
        query = query.eq("reviewer_type", reviewer_type)
    if has_sacred_content is not None:
        query = query.eq("has_sacred_content", has_sacred_content)
    if has_ritual is not None:
        query = query.eq("has_ritual", has_ritual)
    if has_festival is not None:
        query = query.eq("has_festival", has_festival)
    if language:
        query = query.eq("language", language)
    if search:
        query = query.or_(f"text_clean.ilike.%{search}%,title_clean.ilike.%{search}%")
    return query


def _row_to_review_item(r: dict) -> ReviewListItem:
    return ReviewListItem(
        review_id=r["review_id"],
        title_clean=r.get("title_clean"),
        text_clean=r["text_clean"],
        rating=r.get("rating"),
        sentiment_class=r.get("sentiment_class"),
        date=r.get("date"),
        trip_type=r.get("trip_type"),
        reviewer_name=r.get("reviewer_name"),
        reviewer_type=r.get("reviewer_type"),
        word_count=r.get("word_count"),
        like_count=r.get("like_count"),
        has_sacred_content=r.get("has_sacred_content"),
        has_ritual=r.get("has_ritual"),
        has_festival=r.get("has_festival"),
    )


@router.get("/filters", response_model=ReviewFilterOptions)
async def get_review_filters() -> ReviewFilterOptions:
    sb = get_supabase()

    total_result = sb.table("cleaned_reviews").select("review_id", count="exact").execute()
    total = total_result.count or 0

    result = sb.table("cleaned_reviews").select(
        "sentiment_class, trip_type, reviewer_type, year, language, rating"
    ).limit(min(total, 10000)).execute()
    rows = result.data or []

    sentiments = sorted(set(r["sentiment_class"] for r in rows if r.get("sentiment_class")))
    trip_types = sorted(set(r["trip_type"] for r in rows if r.get("trip_type")))
    reviewer_types = sorted(set(r["reviewer_type"] for r in rows if r.get("reviewer_type")))
    years = sorted(set(r["year"] for r in rows if r.get("year")))
    languages = sorted(set(r["language"] for r in rows if r.get("language")))
    ratings = [r["rating"] for r in rows if r.get("rating")]

    return ReviewFilterOptions(
        sentiments=sentiments,
        trip_types=trip_types,
        reviewer_types=reviewer_types,
        years=years,
        languages=languages,
        rating_range={"min": min(ratings) if ratings else 1, "max": max(ratings) if ratings else 5},
        total_reviews=total,
    )


@router.get("", response_model=ReviewListResponse)
async def list_reviews(
    sentiment: Optional[str] = Query(None),
    rating: Optional[int] = Query(None, ge=1, le=5),
    min_rating: Optional[int] = Query(None, ge=1, le=5),
    max_rating: Optional[int] = Query(None, ge=1, le=5),
    year: Optional[int] = Query(None),
    month: Optional[int] = Query(None, ge=1, le=12),
    quarter: Optional[int] = Query(None, ge=1, le=4),
    trip_type: Optional[str] = Query(None),
    reviewer_type: Optional[str] = Query(None),
    has_sacred_content: Optional[bool] = Query(None),
    has_ritual: Optional[bool] = Query(None),
    has_festival: Optional[bool] = Query(None),
    language: Optional[str] = Query(None),
    entity_id: Optional[int] = Query(None),
    search: Optional[str] = Query(None),
    sort_by: Optional[str] = Query("date"),
    sort_dir: Optional[str] = Query("desc"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> ReviewListResponse:
    sb = get_supabase()

    if entity_id:
        mentions = (
            sb.table("entity_mentions")
            .select("review_id")
            .eq("entity_id", entity_id)
            .execute()
        )
        review_ids = [m["review_id"] for m in (mentions.data or [])]
        if not review_ids:
            return ReviewListResponse(
                reviews=[], total=0, page=page, page_size=page_size,
                total_pages=1, filters=ReviewFilters(
                    sentiment=sentiment, rating=rating, year=year, month=month,
                    quarter=quarter, trip_type=trip_type, reviewer_type=reviewer_type,
                    has_sacred_content=has_sacred_content, has_ritual=has_ritual,
                    has_festival=has_festival, language=language, entity_id=entity_id,
                    search=search,
                ),
            )

    query = _build_review_query(
        sb, sentiment=sentiment, rating=rating, min_rating=min_rating,
        max_rating=max_rating, year=year, month=month, quarter=quarter,
        trip_type=trip_type, reviewer_type=reviewer_type,
        has_sacred_content=has_sacred_content, has_ritual=has_ritual,
        has_festival=has_festival, language=language, search=search,
    )

    if entity_id:
        query = query.in_("review_id", review_ids)

    total_result = query.execute()
    total = len(total_result.data or [])

    allowed_sorts = {"date", "rating", "review_id"}
    col = sort_by if sort_by in allowed_sorts else "date"
    desc = sort_dir != "asc"

    offset = (page - 1) * page_size
    result = query.order(col, desc=desc).range(offset, offset + page_size - 1).execute()
    reviews = result.data or []
    total_pages = math.ceil(total / page_size) if total > 0 else 1

    return ReviewListResponse(
        reviews=[_row_to_review_item(r) for r in reviews],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        filters=ReviewFilters(
            sentiment=sentiment, rating=rating, min_rating=min_rating,
            max_rating=max_rating, year=year, month=month, quarter=quarter,
            trip_type=trip_type, reviewer_type=reviewer_type,
            has_sacred_content=has_sacred_content, has_ritual=has_ritual,
            has_festival=has_festival, language=language, entity_id=entity_id,
            search=search,
        ),
    )


@router.get("/{review_id}", response_model=ReviewDetailResponse)
async def get_review_detail(review_id: str) -> ReviewDetailResponse:
    sb = get_supabase()

    result = sb.table("cleaned_reviews").select("*").eq("review_id", review_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Review not found")

    review = result.data[0]

    entities_result = (
        sb.table("entities_raw")
        .select("entity_name, entity_type, quote, rating")
        .eq("review_id", review_id)
        .execute()
    )

    sentiments_result = (
        sb.table("sentiments_raw")
        .select("aspect, sentiment, score, evidence")
        .eq("review_id", review_id)
        .execute()
    )

    return ReviewDetailResponse(
        review_id=review["review_id"],
        title_clean=review.get("title_clean"),
        text_clean=review["text_clean"],
        rating=review.get("rating"),
        sentiment_class=review.get("sentiment_class"),
        date=review.get("date"),
        trip_type=review.get("trip_type"),
        reviewer_type=review.get("reviewer_type"),
        reviewer_name=review.get("reviewer_name"),
        word_count=review.get("word_count"),
        like_count=review.get("like_count"),
        has_images=review.get("has_images"),
        image_count=review.get("image_count"),
        image_urls=review.get("image_urls"),
        has_sacred_content=review.get("has_sacred_content"),
        has_ritual=review.get("has_ritual"),
        has_actor=review.get("has_actor"),
        has_space=review.get("has_space"),
        has_spiritual=review.get("has_spiritual"),
        has_festival=review.get("has_festival"),
        has_rule=review.get("has_rule"),
        language=review.get("language"),
        review_link=review.get("review_link"),
        entities=entities_result.data or [],
        sentiments=sentiments_result.data or [],
    )


@router.get("/by-aspect/groups", response_model=ReviewsByAspectResponse)
async def get_reviews_by_aspect(
    limit_per_group: int = Query(10, ge=1, le=50),
) -> ReviewsByAspectResponse:
    sb = get_supabase()

    raw_result = (
        sb.table("sentiments_raw")
        .select("review_id, aspect, sentiment, score")
        .order("score", desc=True)
        .execute()
    )
    rows = raw_result.data or []

    aspect_map: dict[str, list[dict]] = {}
    seen_per_review: dict[str, set[str]] = {}
    for r in rows:
        rid = r["review_id"]
        aspect = r["aspect"]
        if rid not in seen_per_review:
            seen_per_review[rid] = set()
        if aspect not in seen_per_review[rid]:
            seen_per_review[rid].add(aspect)
            aspect_map.setdefault(aspect, []).append(r)

    groups = []
    for aspect, aspect_rows in sorted(aspect_map.items(), key=lambda x: -len(x[1])):
        review_ids = list({r["review_id"] for r in aspect_rows})[:limit_per_group]
        if not review_ids:
            continue

        reviews_result = (
            sb.table("cleaned_reviews")
            .select("*")
            .in_("review_id", review_ids)
            .execute()
        )
        review_map = {r["review_id"]: r for r in (reviews_result.data or [])}

        items = []
        for r in aspect_rows[:limit_per_group]:
            cr = review_map.get(r["review_id"])
            if cr:
                items.append(_row_to_review_item(cr))

        groups.append(AspectGroupedReviews(aspect=aspect, count=len(aspect_rows), reviews=items))

    return ReviewsByAspectResponse(groups=groups, total_aspects=len(groups))


@router.post("/export", response_model=ExportResponse)
async def export_reviews(review_ids: list[str]) -> ExportResponse:
    if not review_ids:
        raise HTTPException(status_code=400, detail="No review IDs provided")

    sb = get_supabase()
    result = (
        sb.table("cleaned_reviews")
        .select("review_id, title_clean, text_clean, rating, sentiment_class, date, trip_type, reviewer_type")
        .in_("review_id", review_ids)
        .execute()
    )

    items = [ExportReviewItem(**r) for r in (result.data or [])]
    return ExportResponse(reviews=items, total=len(items))
