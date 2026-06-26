from datetime import datetime
from typing import Optional

from sqlmodel import SQLModel, Field


class ScrapeRun(SQLModel, table=True):
    __tablename__ = "scrape_runs"

    id: Optional[int] = Field(default=None, primary_key=True)
    run_id: str = Field(unique=True)
    run_date: Optional[str] = None
    scraped_at: Optional[datetime] = None
    total_reviews: Optional[int] = None
    new_reviews: Optional[int] = None
    total_pages: Optional[int] = None
    storage_path: Optional[str] = None
    created_at: Optional[datetime] = None
