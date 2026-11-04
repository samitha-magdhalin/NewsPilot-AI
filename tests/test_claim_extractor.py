import json

import pytest

from src.claim_extractor import extract_claims_with_ollama
from src.data_models import VerificationStatus


def test_ollama_claims_require_exact_retrieved_evidence(article_factory, monkeypatch):
    article = article_factory()
    article.article_id = "article-1"
    article.retrieval_status = "article_text_retrieved"
    article.extracted_text = (
        "The city council approved a new transit plan on Tuesday. "
        "Officials said the plan adds three bus routes."
    )
    response_payload = {
        "message": {
            "content": json.dumps({
                "claims": [
                    {
                        "claim": "The council approved a transit plan.",
                        "evidence": [{
                            "article_id": "article-1",
                            "excerpt": "The city council approved a new transit plan on Tuesday.",
                        }],
                    },
                    {
                        "claim": "The plan will reduce fares.",
                        "evidence": [{
                            "article_id": "article-1",
                            "excerpt": "The plan will reduce fares across the city.",
                        }],
                    },
                    {
                        "claim": "The mayor signed the plan.",
                        "evidence": [{
                            "article_id": "invented-id",
                            "excerpt": "Officials said the plan adds three bus routes.",
                        }],
                    },
                ]
            })
        }
    }

    class Response:
        def raise_for_status(self):
            pass

        def json(self):
            return response_payload

    class Session:
        trust_env = True

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def post(self, url, **kwargs):
            assert self.trust_env is False
            assert url == "http://127.0.0.1:11434/api/chat"
            assert kwargs["json"]["model"] == "qwen2.5:3b"
            return Response()

    def fake_session():
        return Session()

    monkeypatch.setattr("src.claim_extractor.requests.Session", fake_session)
    claims = extract_claims_with_ollama([article])

    assert len(claims) == 1
    assert claims[0].status == VerificationStatus.INSUFFICIENT_EVIDENCE
    assert claims[0].supporting_source_ids == ["article-1"]
    assert claims[0].evidence[0].excerpt in article.extracted_text


def test_ollama_rejects_case_changed_excerpt(article_factory, monkeypatch):
    article = article_factory()
    article.article_id = "article-1"
    article.retrieval_status = "article_text_retrieved"
    article.extracted_text = "The city council approved a new transit plan on Tuesday."
    payload = {
        "message": {
            "content": json.dumps({
                "claims": [{
                    "claim": "The council approved a transit plan.",
                    "evidence": [{
                        "article_id": "article-1",
                        "excerpt": "THE CITY COUNCIL APPROVED A NEW TRANSIT PLAN ON TUESDAY.",
                    }],
                }]
            })
        }
    }

    class Response:
        def raise_for_status(self):
            pass

        def json(self):
            return payload

    class Session:
        trust_env = True

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def post(self, *_args, **_kwargs):
            return Response()

    monkeypatch.setattr("src.claim_extractor.requests.Session", Session)
    assert extract_claims_with_ollama([article]) == []


def test_local_claims_export_with_evidence(article_factory):
    from src.exporters import briefing_markdown

    article = article_factory()
    article.article_id = "article-1"
    from src.data_models import Claim, ClaimEvidence, Story
    story = Story(
        story_id="story-1",
        canonical_headline=article.title,
        related_articles=[article],
        claims=[
            Claim(
                claim_id="claim-1",
                text="The council approved a transit plan.",
                supporting_source_ids=["article-1"],
                evidence=[
                    ClaimEvidence(
                        article_id="article-1",
                        excerpt="The city council approved the plan.",
                    )
                ],
            )
        ],
    )
    payload = briefing_markdown(
        story,
        {
            "status": "SINGLE_SOURCE",
            "claims": [claim.model_dump(mode="json") for claim in story.claims],
            "limitations": [],
        },
        {"summary": "A source-limited briefing."},
    ).decode()

    assert "Candidate claims — not fact-checked" in payload
    assert "The city council approved the plan." in payload
    assert article.canonical_url in payload


def test_ollama_rejects_non_local_endpoint(article_factory):
    article = article_factory()
    article.retrieval_status = "article_text_retrieved"
    article.extracted_text = "A sufficiently long retrieved article body for extraction."

    with pytest.raises(ValueError, match="local HTTP loopback"):
        extract_claims_with_ollama(
            [article], base_url="https://example.com"
        )


def test_ollama_requires_full_retrieved_text(article_factory):
    article = article_factory()
    article.extracted_text = "A feed snippet that is not a full article body."

    with pytest.raises(ValueError, match="No retrieved article text"):
        extract_claims_with_ollama([article])
