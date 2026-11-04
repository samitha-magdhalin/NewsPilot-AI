"""Create editable social drafts without turning system limitations into story copy."""
import re

PLATFORMS = ('LinkedIn', 'Instagram', 'X', 'Facebook')


def _usable_summary(value):
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    lowered = text.casefold()
    fallback_markers = (
        "a detailed summary cannot be prepared",
        "not enough article text",
        "limited source detail is available",
        "retrieve the original article text",
    )
    if not text or any(marker in lowered for marker in fallback_markers):
        return ""
    return text


def generate_posts(story, briefing, x_limit=280):
    title = story.canonical_headline.strip()
    sources = story.related_articles
    source = f"Source: {sources[0].canonical_url}" if sources else "Source link unavailable"
    summary = _usable_summary(briefing.get('summary'))
    if summary:
        context = summary
    else:
        context = (
            "The available source records do not yet contain enough article text "
            "to describe the event in detail. Read the linked report for the full account."
        )
    posts = {
        'LinkedIn': f"News update: {title}\n\n{context}\n\nThis is an editable research draft. Check the original reporting and evidence notes before sharing.\n{source}\n\n#News #Research #MediaLiteracy",
        'Instagram': f"{title}\n\n{context}\n\nRead the linked report and review the evidence before sharing.\n{source}\n\n#News #MediaLiteracy #CurrentAffairs",
        'X': f"{title} — {source}",
        'Facebook': f"{title}\n\n{context}\n\nReview the linked report and evidence notes for context.\n{source}",
    }
    if len(posts['X']) > x_limit:
        suffix = '… ' + source
        posts['X'] = title[:max(0, x_limit-len(suffix))] + suffix
    posts['Instagram_carousel'] = [
        {'headline': title, 'body': context},
        {'headline': 'What is supported', 'body': 'Review the source and claim-level evidence.'},
        {'headline': 'What remains unclear', 'body': 'Check limitations and any conflicting reports.'},
    ]
    posts['_review_required'] = 'Drafts only. Human review and approval are required; nothing is published automatically.'
    return posts


def validate_post_lengths(posts, x_limit=280):
    return {'X': len(posts.get('X', '')) <= x_limit, 'x_length': len(posts.get('X', '')), 'x_limit': x_limit}
