PLATFORMS=('LinkedIn','Instagram','X','Facebook')
def generate_posts(story, briefing, x_limit=280):
    title=story.canonical_headline.strip(); sources=story.related_articles
    source=f"Source: {sources[0].canonical_url}" if sources else 'Source link unavailable'
    summary=(briefing.get('summary') or 'The retrieved source metadata provides limited detail.').strip()
    posts={
      'LinkedIn':f"News update: {title}\n\n{summary}\n\nThis draft reflects the currently collected evidence; review the source and verification notes before sharing.\n{source}\n\n#News #Research #MediaLiteracy",
      'Instagram':f"{title}\n\n{summary}\n\nRead the source and check the evidence before sharing.\n{source}\n\n#News #MediaLiteracy #CurrentAffairs",
      'X':f"{title} — {source}",
      'Facebook':f"{title}\n\n{summary}\n\nWhy it matters: review the linked report and the verification notes for context.\n{source}"
    }
    if len(posts['X'])>x_limit: posts['X']=title[:max(0,x_limit-len('… '+source)-1)]+'… '+source
    posts['Instagram_carousel']=[{'headline':title,'body':'What the source reports.'},{'headline':'What is supported','body':'Review the source and claim-level evidence.'},{'headline':'What remains unclear','body':'Check limitations and any conflicting reports.'}]
    posts['_review_required']='Drafts only. Human review and approval are required; nothing is published automatically.'
    return posts

def validate_post_lengths(posts, x_limit=280): return {'X':len(posts.get('X',''))<=x_limit,'x_length':len(posts.get('X','')),'x_limit':x_limit}
