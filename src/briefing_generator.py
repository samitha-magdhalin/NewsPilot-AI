
"""Build concise, source-grounded summaries without concatenating headlines."""

import re


def _clean_text(value, headline=""):
    text = re.sub(r"\s+", " ", str(value or "")).strip(
        " \t\r\n-|–—•"
    )
    if not text:
        return ""

    def norm(s):
        return re.sub(
            r"[^a-z0-9 ]+", " ", str(s or "").casefold()
        ).strip()

    if headline and norm(text) == norm(headline):
        return ""

    # Remove the headline when it is an exact prefix.
    if headline and text.casefold().startswith(headline.casefold()):
        text = text[len(headline):].lstrip(" :—–-.|•")

    return re.sub(r"\s+", " ", text).strip()


def _looks_like_headline_list(text, articles=()):
    lower = text.casefold()

    publisher_names = {
        str(getattr(article, "publisher_name", "") or "")
        .casefold()
        .strip()
        for article in articles
    }
    publisher_names.discard("")

    publisher_hits = sum(
        1 for name in publisher_names if name in lower
    )
    sentence_count = len(re.findall(r"[.!?](?:\s|$)", text))
    words = text.split()

    return (
        (publisher_hits >= 2 and sentence_count < 3)
        or (
            len(words) > 35
            and sentence_count < 2
            and text.count(":") >= 2
        )
    )


def _summary_from_source(arts, headline):
    """Prefer retrieved article text; reject headline-only descriptions."""
    arts = list(arts or [])
    candidates = []
    seen = set()

    # Retrieved article text is the strongest available source.
    for article in arts:
        raw = getattr(article, "extracted_text", "")
        cleaned = _clean_text(raw, headline)

        if (
            cleaned
            and len(cleaned) >= 160
            and cleaned.casefold() not in seen
        ):
            candidates.append((cleaned, True))
            seen.add(cleaned.casefold())

    # Use feed descriptions only if they look like actual prose.
    if not candidates:
        for article in arts:
            raw = getattr(article, "description", "")
            article_title = getattr(article, "title", "") or headline

            cleaned = _clean_text(raw, article_title)

            if not cleaned or len(cleaned) < 100:
                continue

            if _looks_like_headline_list(cleaned, arts):
                continue

            sentence_count = len(
                re.findall(r"[.!?](?:\s|$)", cleaned)
            )

            if sentence_count < 1 and len(cleaned.split()) < 45:
                continue

            key = cleaned.casefold()

            if key not in seen:
                candidates.append((cleaned, False))
                seen.add(key)

    # IMPORTANT: Never pretend headlines are a detailed summary.
    if not candidates:
        return (
            "A detailed summary cannot be prepared because the available "
            "feeds provide headlines but not enough article text. "
            "Retrieve the original article text or select a report with "
            "a substantive description. NewsPilot will not combine "
            "unrelated headlines or invent facts to fill the space."
        )

    # Prefer a coherent article over concatenating unrelated descriptions.
    text, from_body = max(
        candidates,
        key=lambda item: (item[1], min(len(item[0]), 1800)),
    )

    sentences = [
        re.sub(r"\s+", " ", sentence).strip()
        for sentence in re.split(r"(?<=[.!?])\s+", text)
    ]

    sentences = [
        sentence
        for sentence in sentences
        if len(sentence) >= 25
        and sentence.casefold().strip(" .!?")
        != headline.casefold().strip(" .!?")
    ]

    summary = " ".join(sentences[:7]).strip() or text

    if len(summary) > 1000:
        summary = summary[:997].rsplit(" ", 1)[0] + "…"

    return summary


def make_briefing(story, verification):
    """Create a briefing from available source text and verification data."""
    arts = story.related_articles
    lead = arts[0] if arts else None

    summary = _summary_from_source(
        arts,
        story.canonical_headline,
    )

    return {
        "headline": story.canonical_headline,
        "summary": summary,
        "what_happened": summary,
        "who_involved": (
            "Only identify people or organisations when they are "
            "explicitly named in the retrieved source text."
        ),
        "where_when": (
            lead.published_at.isoformat()
            if lead and lead.published_at
            else "Publication date unavailable"
        ),
        "why_it_matters": (
            "Assess the significance using the linked reporting and "
            "relevant background sources. The available metadata alone "
            "may not establish wider implications."
        ),
        "verification_status": verification.get(
            "status", "INSUFFICIENT_EVIDENCE"
        ),
        "claims": verification.get("claims", []),
        "sources": verification.get("sources", []),
        "source_independence": verification.get(
            "source_independence", []
        ),
        "uncertainties": verification.get("limitations", []),
        "verified_at": verification.get("verified_at"),
        "model_used": None,
        "note": (
            "This summary uses available article text where possible. "
            "If only headlines are available, retrieve the original "
            "report or select another source. Review the original "
            "report before publication."
        ),
    }
