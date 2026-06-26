from __future__ import annotations

from datetime import date, datetime
from typing import Any, Optional

from pydantic import BaseModel


class SummaryStats(BaseModel):
    total_reviews: int
    avg_rating: float
    positive_count: int
    positive_pct: float
    total_entities: int


class TopSiteItem(BaseModel):
    rank_position: int
    display_name: str
    entity_type: str
    score: float
    is_sacred: bool
    mention_count: Optional[int] = None
    metadata_: Optional[Any] = None


class TopSitesResponse(BaseModel):
    ranking_type: str
    sites: list[TopSiteItem]


class SiteOverview(BaseModel):
    entity_id: int
    display_name: str
    entity_type: str
    mention_count: Optional[int] = None
    positive_count: Optional[int] = None
    negative_count: Optional[int] = None
    neutral_count: Optional[int] = None
    avg_sentiment_score: Optional[float] = None


class SiteAspectItem(BaseModel):
    aspect_raw: Optional[str] = None
    sentiment_label: Optional[str] = None
    sentiment_score: Optional[float] = None
    evidence: Optional[str] = None


class SiteRelatedEntity(BaseModel):
    display_name: str
    entity_type: str
    relation_type: str
    weight: Optional[int] = None


class SiteDetailResponse(BaseModel):
    site: SiteOverview
    top_aspects: list[SiteAspectItem]
    related_entities: list[SiteRelatedEntity]


class ReviewListItem(BaseModel):
    review_id: str
    title_clean: Optional[str] = None
    text_clean: str
    rating: Optional[float] = None
    sentiment_class: Optional[str] = None
    date: Optional[str] = None
    trip_type: Optional[str] = None
    reviewer_name: Optional[str] = None
    reviewer_type: Optional[str] = None
    word_count: Optional[int] = None
    like_count: Optional[int] = None
    has_sacred_content: Optional[bool] = None
    has_ritual: Optional[bool] = None
    has_festival: Optional[bool] = None


class ReviewFilters(BaseModel):
    sentiment: Optional[str] = None
    rating: Optional[int] = None
    min_rating: Optional[int] = None
    max_rating: Optional[int] = None
    year: Optional[int] = None
    month: Optional[int] = None
    quarter: Optional[int] = None
    trip_type: Optional[str] = None
    reviewer_type: Optional[str] = None
    has_sacred_content: Optional[bool] = None
    has_ritual: Optional[bool] = None
    has_festival: Optional[bool] = None
    language: Optional[str] = None
    entity_id: Optional[int] = None
    search: Optional[str] = None


class ReviewListResponse(BaseModel):
    reviews: list[ReviewListItem]
    total: int
    page: int
    page_size: int
    total_pages: int
    filters: ReviewFilters


class ReviewDetailResponse(BaseModel):
    review_id: str
    title_clean: Optional[str] = None
    text_clean: str
    rating: Optional[float] = None
    sentiment_class: Optional[str] = None
    date: Optional[str] = None
    trip_type: Optional[str] = None
    reviewer_type: Optional[str] = None
    reviewer_name: Optional[str] = None
    word_count: Optional[int] = None
    like_count: Optional[int] = None
    has_images: Optional[bool] = None
    image_count: Optional[int] = None
    image_urls: Optional[str] = None
    has_sacred_content: Optional[bool] = None
    has_ritual: Optional[bool] = None
    has_actor: Optional[bool] = None
    has_space: Optional[bool] = None
    has_spiritual: Optional[bool] = None
    has_festival: Optional[bool] = None
    has_rule: Optional[bool] = None
    language: Optional[str] = None
    review_link: Optional[str] = None
    entities: list[Any] = []
    sentiments: list[Any] = []


class AspectGroupedReviews(BaseModel):
    aspect: str
    count: int
    reviews: list[ReviewListItem]


class ReviewsByAspectResponse(BaseModel):
    groups: list[AspectGroupedReviews]
    total_aspects: int


class NarrativeInsightItem(BaseModel):
    id: int
    category: str
    priority: str
    title: str
    narrative: str
    evidence: Optional[Any] = None
    recommended_actions: Optional[Any] = None
    audience: str
    is_active: bool
    computed_at: datetime


class AIInsightsResponse(BaseModel):
    insights: list[NarrativeInsightItem]
    total: int


class RecurringProblemItem(BaseModel):
    display_aspect: str
    mention_count: int
    negative_pct: float
    avg_sentiment_score: Optional[float] = None
    trend_by_year: Optional[Any] = None


class RecurringProblemsResponse(BaseModel):
    problems: list[RecurringProblemItem]


class IssueDetailResponse(BaseModel):
    insight: NarrativeInsightItem
    supporting_reviews: list[Any]


class PipelineActivityItem(BaseModel):
    id: int
    activity_type: str
    run_id: Optional[str] = None
    status: str
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    total_reviews: Optional[int] = None
    new_reviews: Optional[int] = None
    duration_seconds: Optional[float] = None
    details: Optional[dict] = None


class PipelineActivityResponse(BaseModel):
    activities: list[PipelineActivityItem]
    total: int


class MonthlyReportData(BaseModel):
    year: int
    month: int
    review_count: int
    avg_rating: float
    positive_count: int
    negative_count: int


class SiteMonthlyReportResponse(BaseModel):
    site_name: str
    year: int
    monthly_data: list[MonthlyReportData]
    top_aspects: list[Any]


class RankingTableItem(BaseModel):
    rank_position: int
    display_name: str
    entity_type: str
    score: float
    is_sacred: bool
    metadata_: Optional[Any] = None
    computed_at: datetime


class RankingTableResponse(BaseModel):
    ranking_type: str
    rankings: list[RankingTableItem]
    total: int


class TrendDataPoint(BaseModel):
    year: int
    quarter: Optional[int] = None
    month: Optional[int] = None
    review_count: int
    avg_rating: float
    positive_pct: float


class TrendAnalysisResponse(BaseModel):
    granularity: str
    data: list[TrendDataPoint]


class AspectAnalyticsItem(BaseModel):
    display_aspect: str
    mention_count: int
    positive_pct: float
    negative_pct: float
    neutral_pct: float
    avg_sentiment_score: Optional[float] = None
    trend_by_year: Optional[Any] = None
    trend_by_period: Optional[Any] = None
    by_trip_type: Optional[Any] = None
    by_reviewer_type: Optional[Any] = None


class SentimentAnalyticsResponse(BaseModel):
    aspects: list[AspectAnalyticsItem]
    total: int


class NetworkNode(BaseModel):
    id: int
    display_name: str
    entity_type: str
    mention_count: int


class NetworkEdge(BaseModel):
    source: int
    target: int
    relation_type: str
    weight: int


class SemanticNetworkResponse(BaseModel):
    nodes: list[NetworkNode]
    edges: list[NetworkEdge]
    total_nodes: int
    total_edges: int


class ExportReviewItem(BaseModel):
    review_id: str
    title_clean: Optional[str] = None
    text_clean: str
    rating: Optional[float] = None
    sentiment_class: Optional[str] = None
    date: Optional[str] = None
    trip_type: Optional[str] = None
    reviewer_type: Optional[str] = None


class ExportResponse(BaseModel):
    reviews: list[ExportReviewItem]
    total: int


class ChartMeta(BaseModel):
    chart_type: str
    title: str
    description: Optional[str] = None


class StackedBarChartSeries(BaseModel):
    positive: list[float]
    neutral: list[float]
    negative: list[float]


class StackedBarChartData(ChartMeta):
    labels: list[str]
    series: StackedBarChartSeries
    mention_counts: list[int]
    avg_scores: list[Optional[float]]
    computed_at: Optional[datetime] = None


class AspectTrendYearPoint(BaseModel):
    year: int
    avg_score: Optional[float] = None
    mention_count: Optional[int] = None
    positive_count: Optional[int] = None
    negative_count: Optional[int] = None
    positive_pct: Optional[float] = None
    negative_pct: Optional[float] = None


class AspectTrendPeriodPoint(BaseModel):
    period: Optional[str] = None
    avg_score: Optional[float] = None
    mention_count: Optional[int] = None


class AspectSegmentStats(BaseModel):
    positive_pct: float
    negative_pct: float
    avg_score: Optional[float] = None
    mention_count: Optional[int] = None


class AspectTrendChartData(ChartMeta):
    aspect: str
    display_aspect: str
    mention_count: int
    avg_sentiment_score: Optional[float] = None
    trend_by_year: list[AspectTrendYearPoint]
    trend_by_period: list[AspectTrendPeriodPoint]
    by_trip_type: Optional[dict[str, AspectSegmentStats]] = None
    by_reviewer_type: Optional[dict[str, AspectSegmentStats]] = None
    computed_at: Optional[datetime] = None


class EntityRankingItem(BaseModel):
    rank: int
    name: str
    score: float
    is_sacred: bool
    entity_type: str
    metadata_: Optional[Any] = None


class EntityRankingChartData(ChartMeta):
    ranking_type: str
    items: list[EntityRankingItem]
    total: int
    computed_at: Optional[datetime] = None


class VolumeTrendPoint(BaseModel):
    label: str
    volume: int
    avg_rating: Optional[float] = None
    positive_pct: Optional[float] = None


class VolumeTrendChartData(ChartMeta):
    granularity: str
    data: list[VolumeTrendPoint]
    computed_at: Optional[datetime] = None


class AspectRadarItem(BaseModel):
    aspect: str
    display_aspect: str
    mention_count: int
    positive_pct: float
    negative_pct: float
    neutral_pct: float
    avg_sentiment_score: Optional[float] = None
    score_normalized: Optional[int] = None


class AspectRadarChartData(ChartMeta):
    aspects: list[AspectRadarItem]
    total: int
    computed_at: Optional[datetime] = None


class TopEntityItem(BaseModel):
    rank: int
    display_name: str
    entity_type: str
    mention_count: int


class TopEntitiesChartData(ChartMeta):
    items: list[TopEntityItem]
    total: int


class CentralityItem(BaseModel):
    rank: int
    entity_type: str
    entity_count: int
    avg_degree_centrality: float
    avg_mention_count: float


class CentralityChartData(ChartMeta):
    items: list[CentralityItem]
    total: int


class CommunityItem(BaseModel):
    rank: int
    community_id: int
    size: int
    dominant_type: str
    type_distribution: Optional[dict] = None


class CommunityChartData(ChartMeta):
    algorithm: str
    modularity: float
    community_count: int
    items: list[CommunityItem]
    total: int


class ReviewFilterOptions(BaseModel):
    sentiments: list[str]
    trip_types: list[str]
    reviewer_types: list[str]
    years: list[int]
    languages: list[str]
    rating_range: dict[str, int]
    total_reviews: int


class TopInsight(BaseModel):
    title: str
    priority: str
    aspect: str
    negative_pct: float
    narrative: str


class ExecutiveSummaryResponse(BaseModel):
    summary: str
    key_metrics: dict[str, Any]
    top_insights: list[TopInsight]
    generated_for: str
    critical_count: int
    high_priority_count: int


class HeritageHealthItem(BaseModel):
    title: str
    audience: str
    category: str
    priority: str
    narrative: str
    evidence: Optional[Any] = None
    recommended_actions: list[Any]


class HeritageHealthResponse(BaseModel):
    items: list[HeritageHealthItem]
    total: int


class EmotionalAnchorItem(BaseModel):
    emotion: str
    anchored_type: str
    anchored_entity: str
    co_mention_count: int


class EmotionalAnchorsResponse(BaseModel):
    anchors: list[EmotionalAnchorItem]
    total: int


class SemanticTrajectoryItem(BaseModel):
    trend: str
    entity_type: str
    display_name: str
    total_mentions: int
    yearly_mentions: list[dict[str, Any]]


class SemanticTrajectoriesResponse(BaseModel):
    trajectories: list[SemanticTrajectoryItem]
    total: int


class MetaPathItem(BaseModel):
    source_type: str
    target_type: str
    path_count: int


class MetaPathResponse(BaseModel):
    top_patterns: list[MetaPathItem]
    total_paths: int


class MotifItem(BaseModel):
    label: str
    count: int
    entity_types: list[str]


class MotifResponse(BaseModel):
    motifs: list[MotifItem]
    triad_count: int
    unique_motif_types: int


class SacredSecularNetworkResponse(BaseModel):
    edge_matrix: list[dict[str, Any]]
    bridge_ratio: float
    cross_domain_edges: int
    sacred_sacred_edges: int
    secular_secular_edges: int


class TemporalEvolutionResponse(BaseModel):
    timeline: list[dict[str, Any]]
    total_years: int


class DualEmotionResponse(BaseModel):
    total_reviews: int
    pct_of_reviews: float
    dual_valence_entities: int
    dual_emotion_review_count: int


class CriticalFinding(BaseModel):
    finding: str
    explanation: str
    evidence: str
    impact: str
    urgency: str


class LLRecommendation(BaseModel):
    title: str
    rationale: str
    expected_outcome: str
    stakeholders: list[str]
    effort: str
    timeline: str


class LLMRecommendationResponse(BaseModel):
    narrative_summary: str
    critical_findings: list[CriticalFinding]
    recommendations: list[LLRecommendation]
    heritage_considerations: str
    error: Optional[str] = None


# --- Action / Response Drafting Schemas ---


class DraftResponseRequest(BaseModel):
    review_id: str
    tone: Optional[str] = "professional"


class DraftResponseResponse(BaseModel):
    review_id: str
    draft: str
    tone: str
    reviewer_name: Optional[str] = None
    original_rating: Optional[float] = None
    original_sentiment: Optional[str] = None
    error: Optional[str] = None


class ActionPlanItem(BaseModel):
    title: str
    description: str
    priority: str
    assignee: str
    due_hint: str
    category: str


class GenerateActionPlanRequest(BaseModel):
    source_type: str
    source_id: Optional[int] = None
    title: str
    context: str
    num_tasks: Optional[int] = 5


class GenerateActionPlanResponse(BaseModel):
    source_type: str
    source_title: str
    action_items: list[ActionPlanItem]
    summary: str
    error: Optional[str] = None
