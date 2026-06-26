from datetime import datetime
from typing import Optional

from sqlmodel import SQLModel, Field


class CleanedReview(SQLModel, table=True):
    __tablename__ = "cleaned_reviews"

    review_id: str = Field(primary_key=True)
    title_clean: Optional[str] = None
    text_clean: str
    rating: Optional[float] = None
    sentiment_class: Optional[str] = None
    date: Optional[str] = None
    year: Optional[int] = None
    month: Optional[int] = None
    quarter: Optional[int] = None
    period: Optional[str] = None
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
    is_translated: Optional[bool] = None
    original_language: Optional[str] = None
    review_link: Optional[str] = None
    run_id: str
    ingested_at: Optional[datetime] = None
