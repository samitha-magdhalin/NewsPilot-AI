import re
from rapidfuzz.fuzz import token_set_ratio
from .news_fetcher import canonicalize_url

def normalize_title(s): return re.sub(r'[^a-z0-9 ]',' ',s.lower()).strip()
def deduplicate(articles, threshold=92):
    seen_urls=set(); titles=[]; out=[]
    for a in articles:
        url=canonicalize_url(a.canonical_url)
        if url in seen_urls: continue
        title=normalize_title(a.title)
        if any(token_set_ratio(title,old)>=threshold for old in titles): continue
        seen_urls.add(url); titles.append(title); out.append(a)
    return out
