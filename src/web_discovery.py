"""Broad, keyless discovery using public search feeds/APIs (not whole-web scraping)."""
from datetime import datetime, timezone
from urllib.parse import quote_plus, urlparse
import requests
from .news_fetcher import parse_feed, canonicalize_url

UA = {'User-Agent': 'NewsPilotAI/2.0 (local research dashboard; contact: local-user)'}

def discover_web(query: str, max_results: int = 50, timeout: int = 15):
    """Search Google News RSS and GDELT DOC API; each provider can fail independently."""
    query = (query or '').strip()
    if not query:
        raise ValueError('Enter a topic or keyword to search the web.')
    articles, health = [], []
    # Google News RSS returns links to reporting and works without an API key.
    try:
        url = 'https://news.google.com/rss/search?q=' + quote_plus(query) + '&hl=en-US&gl=US&ceid=US:en'
        r = requests.get(url, headers=UA, timeout=timeout)
        r.raise_for_status()
        parsed = parse_feed(r.content, {'name': 'Google News search', 'category': 'Web search'})
        for a in parsed:
            a.source_type = 'web_search'
            a.retrieval_status = 'metadata_only'
            a.extraction_limitations = ['Discovered through Google News RSS; open publisher link for full reporting']
        articles.extend(parsed[:max_results])
        health.append({'provider':'Google News RSS','ok':True,'count':len(parsed),'error':''})
    except Exception as e:
        health.append({'provider':'Google News RSS','ok':False,'count':0,'error':str(e)[:240]})
    # Bing News RSS is an independent fallback when Google News is unavailable.
    try:
        url = 'https://www.bing.com/news/search?q=' + quote_plus(query) + '&format=rss'
        r = requests.get(url, headers=UA, timeout=timeout)
        r.raise_for_status()
        parsed = parse_feed(r.content, {'name': 'Bing News search', 'category': 'Web search'})
        for a in parsed:
            a.source_type = 'web_search'
            a.retrieval_status = 'metadata_only'
            a.extraction_limitations = ['Discovered through Bing News RSS; open publisher link for full reporting']
        articles.extend(parsed[:max_results])
        health.append({'provider':'Bing News RSS','ok':True,'count':len(parsed),'error':''})
    except Exception as e:
        health.append({'provider':'Bing News RSS','ok':False,'count':0,'error':str(e)[:180]})
    # GDELT is a public global news index. It is an index, not a completeness guarantee.
    try:
        params = {'query': query, 'mode':'ArtList', 'format':'json', 'sort':'DateDesc', 'maxrecords':min(max_results,250), 'format':'json'}
        r = requests.get('https://api.gdeltproject.org/api/v2/doc/doc', params=params, headers=UA, timeout=timeout)
        r.raise_for_status(); payload = r.json(); count = 0
        for item in payload.get('articles', []):
            url = item.get('url','').strip(); title = ' '.join((item.get('title') or '').split())
            if not url.startswith(('http://','https://')) or not title: continue
            domain = urlparse(url).hostname or ''
            from .data_models import Article
            dt = None
            raw = item.get('seendate')
            if raw:
                try: dt = datetime.strptime(raw, '%Y%m%dT%H%M%SZ').replace(tzinfo=timezone.utc)
                except Exception: pass
            a = Article(title=title, canonical_url=canonicalize_url(url), original_url=url,
                publisher_name=domain.removeprefix('www.'), publisher_domain=domain,
                category='Web search', description=item.get('socialimage') or '', published_at=dt,
                fetched_at=datetime.now(timezone.utc), source_type='web_search', retrieval_status='metadata_only',
                extraction_limitations=['Discovered through the GDELT news index; open publisher link to inspect the article']).ensure_id()
            articles.append(a); count += 1
        health.append({'provider':'GDELT news index','ok':True,'count':count,'error':''})
    except Exception as e:
        health.append({'provider':'GDELT news index','ok':False,'count':0,'error':str(e)[:240]})
    unique, seen = [], set()
    for a in articles:
        key = a.canonical_url
        if key not in seen: seen.add(key); unique.append(a)
    unique.sort(key=lambda a:a.published_at or datetime.min.replace(tzinfo=timezone.utc), reverse=True)
    return unique[:max_results], health
