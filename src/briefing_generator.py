import re

def _clean_text(value, headline=""):
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    if not text:
        return ""
    # Some feeds repeat the headline as the description; avoid presenting that as a summary.
    if headline and text.casefold().strip(" .!?") == headline.casefold().strip(" .!?"):
        return ""
    if headline and text.casefold().startswith(headline.casefold()):
        text = text[len(headline):].lstrip(" :—–-.")
    return text.strip()

def _summary_from_source(arts, headline):
    """Build a fuller, source-grounded summary without repeating the headline."""
    candidates = []
    seen = set()
    for article in arts:
        # Retrieved article text is preferred because feed descriptions are often just headlines.
        for raw in (
            getattr(article, "extracted_text", ""),
            getattr(article, "description", ""),
        ):
            cleaned = _clean_text(raw, headline)
            if not cleaned:
                continue
            key = cleaned.casefold()
            if key not in seen:
                candidates.append(cleaned)
                seen.add(key)
        if len(candidates) >= 5:
            break

    if not candidates:
        return (
            "A detailed, source-grounded summary cannot be prepared from the headline alone. "
            "The publisher's feed does not contain enough article text to establish what happened, "
            "who was involved, or what evidence supports the report. Open the original report and "
            "use “Read more / retrieve text” in Discover to retrieve available article text. "
            "NewsPilot will then use the retrieved reporting to build a fuller explanation rather "
            "than repeating the headline or inventing details."
        )

    # Use multiple factual sentences when the source provides them; retain enough detail for a
    # useful editorial graphic while avoiding an unsupported expansion of short feed snippets.
    sentences_out = []
    seen_sentences = set()
    for text in candidates:
        parts = re.split(r"(?<=[.!?])\s+(?=[A-Z0-9“\"'])", text)
        if len(parts) == 1:
            parts = re.split(r"(?<=[.!?])\s+", text)
        for sentence in parts:
            sentence = sentence.strip()
            if len(sentence) < 24 or sentence.casefold().strip(" .!?") == headline.casefold().strip(" .!?"):
                continue
            key = sentence.casefold()
            if key not in seen_sentences:
                sentences_out.append(sentence)
                seen_sentences.add(key)
            if len(" ".join(sentences_out)) >= 1150:
                break
        if len(sentences_out) >= 7 or len(" ".join(sentences_out)) >= 1150:
            break

    summary = " ".join(sentences_out).strip()
    if not summary:
        return (
            "The headline is available, but the source has not supplied enough distinct reporting "
            "to produce a reliable multi-sentence explanation. Retrieve the article text from "
            "Discover and return to Create studio for a more detailed, source-based summary."
        )
    if len(summary) > 1200:
        summary = summary[:1197].rsplit(" ", 1)[0] + "…"
    return summary

def make_briefing(story, verification):
    arts = story.related_articles
    lead = arts[0] if arts else None
    summary = _summary_from_source(arts, story.canonical_headline)
    return {
        "headline": story.canonical_headline,
        "summary": summary,
        "what_happened": summary,
        "who_involved": "Only identify people or organisations when they are explicitly named in the retrieved source text.",
        "where_when": lead.published_at.isoformat() if lead and lead.published_at else "Publication date unavailable",
        "why_it_matters": "Assess the significance using the linked reporting and any relevant background sources. The available metadata alone may not establish wider implications.",
        "verification_status": verification.get("status", "INSUFFICIENT_EVIDENCE"),
        "claims": verification.get("claims", []),
        "sources": verification.get("sources", []),
        "source_independence": verification.get("source_independence", []),
        "uncertainties": verification.get("limitations", []),
        "verified_at": verification.get("verified_at"),
        "model_used": None,
        "note": "This summary uses text retrieved from the linked reporting. If article text was unavailable, retrieve it from Latest coverage to get a more detailed explanation. Review the original report before publication."
    }
