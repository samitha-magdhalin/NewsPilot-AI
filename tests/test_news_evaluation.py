from datetime import datetime, timedelta, timezone

from src.briefing_generator import make_briefing
from src.data_models import Claim, Story, VerificationStatus
from src.social_writer import generate_posts
from src.verification_engine import assess_story


def _story(articles, claims=None):
    return Story(
        story_id="evaluation-story",
        canonical_headline="Northbridge approves the fictional Green Loop plan",
        topic="Local transport",
        related_articles=articles,
        claims=claims or [],
    )


def test_recency_uses_newest_report_within_configured_window(article_factory):
    recent = datetime.now(timezone.utc) - timedelta(hours=2)
    old = datetime.now(timezone.utc) - timedelta(days=30)
    story = _story([
        article_factory(
            url="https://northbridge.example/news/green-loop",
            domain="northbridge.example",
            published=recent,
        ),
        article_factory(
            url="https://regional.example/green-loop",
            domain="regional.example",
            published=old,
        ),
    ])

    assert assess_story(story, freshness_hours=168)["status"] == "MULTI_SOURCE_SUPPORTED"

    stale_story = _story([
        article_factory(
            url="https://archive.example/green-loop",
            domain="archive.example",
            published=old,
        )
    ])
    assert assess_story(stale_story, freshness_hours=168)["status"] == "OUTDATED"


def test_multiple_publishers_are_not_presented_as_proof_of_truth(article_factory):
    story = _story([
        article_factory(
            url="https://northbridge.example/news/green-loop",
            domain="northbridge.example",
        ),
        article_factory(
            url="https://regional.example/green-loop",
            domain="regional.example",
            publisher="Regional News",
        ),
    ])

    result = assess_story(story)

    assert result["status"] == "MULTI_SOURCE_SUPPORTED"
    assert result["source_independence"]["independence"] == "uncertain"
    assert "do not prove independent reporting" in result["source_independence"]["note"]
    assert "not probability" in result["coverage_note"]


def test_explicit_conflicting_claim_is_reflected_in_story_status(article_factory):
    claim = Claim(
        claim_id="conflict-1",
        text="The plan was approved",
        status=VerificationStatus.CONFLICTING_REPORTS,
        limitations=["Sources disagree about the vote outcome."],
    )
    story = _story([article_factory()], claims=[claim])

    result = assess_story(story)

    assert result["status"] == "CONFLICTING_REPORTS"
    assert result["claims"][0]["status"] == "CONFLICTING_REPORTS"


def test_briefing_and_social_drafts_keep_source_attribution(article_factory):
    article = article_factory(
        url="https://northbridge.example/news/green-loop",
        domain="northbridge.example",
        publisher="Northbridge News",
        published=datetime.now(timezone.utc),
        description=(
            "Northbridge officials announced the fictional Green Loop plan today. "
            "The proposal includes new bus routes and protected bike lanes. "
            "A public consultation will begin next month."
        ),
    )
    story = _story([article])
    verification = assess_story(story)
    briefing = make_briefing(story, verification)
    posts = generate_posts(story, briefing)

    assert briefing["sources"][0]["url"] == article.canonical_url
    for platform in ("LinkedIn", "Instagram", "X", "Facebook"):
        assert article.canonical_url in posts[platform]
    assert "Human review" in posts["_review_required"]
    assert len(posts["X"]) <= 280
