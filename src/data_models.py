from datetime import datetime, timezone
from enum import Enum
from hashlib import sha256
from pydantic import BaseModel, Field, HttpUrl, field_validator
from typing import Optional

def utcnow(): return datetime.now(timezone.utc)
class VerificationStatus(str, Enum):
    MULTI_SOURCE_SUPPORTED='MULTI_SOURCE_SUPPORTED'
    PRIMARY_SOURCE_SUPPORTED='PRIMARY_SOURCE_SUPPORTED'
    SINGLE_SOURCE='SINGLE_SOURCE'
    CONFLICTING_REPORTS='CONFLICTING_REPORTS'
    INSUFFICIENT_EVIDENCE='INSUFFICIENT_EVIDENCE'
    OUTDATED='OUTDATED'

class Article(BaseModel):
    article_id: str = ''
    title: str
    canonical_url: str
    original_url: str
    publisher_name: str = 'Unknown publisher'
    publisher_domain: str = ''
    category: str = 'General'
    description: str = ''
    extracted_text: str = ''
    published_at: Optional[datetime] = None
    fetched_at: datetime = Field(default_factory=utcnow)
    source_type: str = 'rss'
    retrieval_status: str = 'metadata_only'
    extraction_limitations: list[str] = Field(default_factory=list)

    @field_validator('published_at', 'fetched_at', mode='before')
    @classmethod
    def normalize_dates(cls, value):
        if value in (None, ''): return None
        if isinstance(value, datetime): dt=value
        else:
            from dateutil.parser import parse
            try: dt=parse(str(value))
            except Exception: return None
        return dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt.astimezone(timezone.utc)

    @field_validator('canonical_url', 'original_url')
    @classmethod
    def http_url_only(cls, value):
        if not value.startswith(('https://','http://')): raise ValueError('Only HTTP(S) URLs are allowed')
        return value

    def ensure_id(self):
        if not self.article_id: self.article_id=sha256(self.canonical_url.encode()).hexdigest()[:16]
        if not self.publisher_domain:
            from urllib.parse import urlparse
            self.publisher_domain=urlparse(self.canonical_url).hostname or ''
        return self

class Claim(BaseModel):
    claim_id: str
    text: str
    status: VerificationStatus = VerificationStatus.INSUFFICIENT_EVIDENCE
    supporting_source_ids: list[str] = Field(default_factory=list)
    contradictory_source_ids: list[str] = Field(default_factory=list)
    excerpts: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)

class Story(BaseModel):
    story_id: str
    canonical_headline: str
    topic: str = 'General'
    related_articles: list[Article] = Field(default_factory=list)
    first_observed_at: datetime = Field(default_factory=utcnow)
    latest_observed_at: datetime = Field(default_factory=utcnow)
    event_date_if_known: Optional[datetime] = None
    claims: list[Claim] = Field(default_factory=list)
    verification_status: VerificationStatus = VerificationStatus.INSUFFICIENT_EVIDENCE
    evidence_coverage: float = 0.0
    limitations: list[str] = Field(default_factory=list)
    briefing: dict = Field(default_factory=dict)
    social_posts: dict = Field(default_factory=dict)
    generated_by_model: Optional[str] = None
