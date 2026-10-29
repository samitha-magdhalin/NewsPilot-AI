from src.briefing_generator import make_briefing
from src.data_models import Story


def test_briefing_uses_retrieved_article_text(article_factory):
    article = article_factory(
        title="Can AI resurrect the dead?",
        description="Can AI resurrect the dead?",
        url="https://example.org/ai-story",
    )
    article.extracted_text = (
        "Researchers are studying whether artificial intelligence can recreate aspects of a deceased "
        "person from digital records. The approach may use messages, photographs, audio recordings, "
        "and other personal data to build a conversational simulation. Experts warn that the result "
        "would be an imitation rather than a return of the person, and raise questions about consent, "
        "privacy, grief, and how families might use such systems. The technology remains limited by "
        "the quality of available data and the risk that generated responses could be inaccurate."
    )
    story = Story(story_id="test-story", canonical_headline=article.title, related_articles=[article])
    briefing = make_briefing(story, {})
    assert len(briefing["summary"]) > 150
    assert "artificial intelligence" in briefing["summary"].lower()
    assert briefing["summary"] != article.title


def test_headline_only_feed_does_not_misrepresent_headline_as_summary(article_factory):
    article = article_factory(
        title="Can AI resurrect the dead?",
        description="Can AI resurrect the dead?",
        url="https://example.org/ai-story",
    )
    story = Story(story_id="test-story", canonical_headline=article.title, related_articles=[article])
    briefing = make_briefing(story, {})
    assert len(briefing["summary"]) > 100
    assert briefing["summary"] != article.title
    assert "cannot be prepared" in briefing["summary"].lower()
