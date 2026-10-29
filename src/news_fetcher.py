from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime
from urllib.parse import urlparse, urlunparse, parse_qsl, urlencode
import time, requests
try: import feedparser
except ImportError: feedparser=None
import xml.etree.ElementTree as ET
from .data_models import Article
from .url_validator import validate_public_http_url

TRACKING={'utm_source','utm_medium','utm_campaign','utm_term','utm_content','fbclid','gclid'}
def canonicalize_url(url):
    p=urlparse(url.strip()); q=[(k,v) for k,v in parse_qsl(p.query) if k.lower() not in TRACKING]
    return urlunparse((p.scheme.lower(),p.netloc.lower(),p.path.rstrip('/') or '/', '', urlencode(q), ''))
def parse_date(entry):
    for key in ('published','updated','created'):
        raw=entry.get(key)
        if not raw: continue
        try:
            if key+'_parsed' in entry and entry[key+'_parsed']:
                import time as _time
                return datetime.fromtimestamp(_time.mktime(entry[key+'_parsed']), timezone.utc)
            dt=parsedate_to_datetime(raw)
            return dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt.astimezone(timezone.utc)
        except Exception: pass
    return None

def parse_feed(content, source: dict, now=None):
    now=now or datetime.now(timezone.utc)
    if feedparser is not None:
        parsed=feedparser.parse(content)
        if getattr(parsed,'bozo',False) and not parsed.entries: raise ValueError('Invalid RSS/Atom feed')
        entries=[]
        for e in parsed.entries:
            entries.append({'title':e.get('title',''),'link':e.get('link',''),'summary':e.get('summary','') or e.get('description',''),'published':e.get('published'),'updated':e.get('updated'),'published_parsed':e.get('published_parsed'),'updated_parsed':e.get('updated_parsed')})
    else:
        try:
            root=ET.fromstring(content); entries=[]
            for item in root.findall('.//item'):
                entries.append({'title':item.findtext('title',''),'link':item.findtext('link',''),'summary':item.findtext('description',''),'published':item.findtext('pubDate')})
            ns={'atom':'http://www.w3.org/2005/Atom'}
            if not entries:
                for item in root.findall('.//atom:entry',ns):
                    link=item.find('atom:link',ns); entries.append({'title':item.findtext('atom:title','',ns),'link':link.attrib.get('href','') if link is not None else '', 'summary':item.findtext('atom:summary','',ns),'published':item.findtext('atom:published','',ns)})
            if root.tag.lower() not in ('rss','feed','rdf:rdf') and not entries: raise ValueError('Invalid RSS/Atom feed')
        except ET.ParseError as e: raise ValueError('Invalid RSS/Atom feed') from e
    results=[]
    for e in entries:
        url=e.get('link','').strip(); title=' '.join(e.get('title','').split())
        ok,_=validate_public_http_url(url)
        if not title or not ok: continue
        from bs4 import BeautifulSoup
        description=BeautifulSoup(e.get('summary','') or e.get('description',''), 'html.parser').get_text(' ',strip=True)
        article=Article(title=title, canonical_url=canonicalize_url(url), original_url=url,
          publisher_name=source.get('name','Unknown publisher'), publisher_domain=urlparse(url).hostname or '',
          category=source.get('category','General'), description=description,
          published_at=parse_date(e), fetched_at=now, retrieval_status='metadata_only',
          extraction_limitations=['RSS metadata only; full article text not yet retrieved']).ensure_id()
        results.append(article)
    return results

def fetch_source(source, timeout=12, max_bytes=2500000):
    url=source.get('url',''); ok,why=validate_public_http_url(url, resolve_dns=True)
    if not ok: return [], {'source':source.get('name','unknown'),'ok':False,'error':why,'count':0}
    try:
        r=requests.get(url,timeout=timeout,headers={'User-Agent':'NewsPilotAI/1.0 (local news research tool)'},stream=True,allow_redirects=False)
        if r.status_code in (301,302,303,307,308): return [], {'source':source.get('name'),'ok':False,'error':'Redirect not followed; edit feed URL to the final public endpoint','count':0}
        r.raise_for_status(); chunks=[]; size=0
        for chunk in r.iter_content(65536):
            size+=len(chunk)
            if size>max_bytes: raise ValueError('Feed response exceeds configured size limit')
            chunks.append(chunk)
        articles=parse_feed(b''.join(chunks),source)
        return articles, {'source':source.get('name'),'ok':True,'error':'','count':len(articles)}
    except Exception as e: return [], {'source':source.get('name'),'ok':False,'error':str(e),'count':0}

def fetch_sources(sources, timeout=12, max_bytes=2500000, delay=0.4, max_articles=60):
    all_articles=[]; health=[]
    for i,s in enumerate(sources):
        if not s.get('enabled',True): continue
        arts,status=fetch_source(s,timeout,max_bytes); all_articles.extend(arts); health.append(status)
        if i < len(sources)-1: time.sleep(max(0,delay))
    seen=set(); unique=[]
    for a in all_articles:
        if a.canonical_url not in seen: seen.add(a.canonical_url); unique.append(a)
    unique.sort(key=lambda a:a.published_at or datetime.min.replace(tzinfo=timezone.utc),reverse=True)
    return unique[:max_articles],health
