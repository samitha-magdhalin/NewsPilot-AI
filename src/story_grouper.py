from hashlib import sha1
from rapidfuzz.fuzz import token_set_ratio
from .deduplicator import normalize_title
from .data_models import Story

def group_stories(articles, threshold=78):
    groups=[]
    for a in articles:
        title=normalize_title(a.title); words=set(title.split())
        best=None; best_score=0
        for g in groups:
            anchor=normalize_title(g['articles'][0].title); score=token_set_ratio(title,anchor)
            common=len(words & set(anchor.split()))
            if score>=threshold and common>=2 and score>best_score: best,best_score=g,score
        if best: best['articles'].append(a)
        else: groups.append({'articles':[a]})
    out=[]
    for g in groups:
        arts=g['articles']; sid=sha1('|'.join(sorted(a.article_id for a in arts)).encode()).hexdigest()[:12]
        dates=[a.published_at for a in arts if a.published_at]
        out.append(Story(story_id=sid,canonical_headline=arts[0].title,topic=arts[0].category,related_articles=arts,
          first_observed_at=min((a.fetched_at for a in arts),default=arts[0].fetched_at),
          latest_observed_at=max((a.fetched_at for a in arts),default=arts[0].fetched_at),
          event_date_if_known=max(dates) if dates else None,
          limitations=['Headline grouping is heuristic; review related articles manually.']))
    return out
