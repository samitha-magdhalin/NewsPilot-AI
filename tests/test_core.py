from datetime import datetime, timezone, timedelta
from src.news_fetcher import canonicalize_url, parse_feed
from src.deduplicator import deduplicate
from src.story_grouper import group_stories
from src.verification_engine import assess_story
from src.data_models import Story, VerificationStatus
from src.url_validator import validate_public_http_url
from src.source_independence import assess_independence

def test_canonical_url_removes_tracking():
 assert canonicalize_url('https://example.com/a?utm_source=x&id=4')=='https://example.com/a?id=4'
def test_parse_feed_missing_date_and_metadata():
 feed=b'<rss version="2.0"><channel><title>Test</title><item><title>City council approves transit plan</title><link>https://example.org/a</link><description>Officials announced a plan.</description></item></channel></rss>'
 a=parse_feed(feed,{'name':'Test','category':'Local'})[0]
 assert a.published_at is None and a.title.startswith('City council')
def test_invalid_feed():
 try: parse_feed(b'not rss',{'name':'Broken'})
 except Exception: pass
 else: assert False, 'invalid feed should not parse as a usable feed'
def test_dedupe_url_and_headline(article_factory):
 a=article_factory(url='https://example.org/a'); b=article_factory(url='https://example.org/a?utm_source=x'); c=article_factory(title='City council approves a new transit plan',url='https://other.org/b',domain='other.org')
 assert len(deduplicate([a,b]))==1
 assert len(deduplicate([a,c]))==1
def test_story_grouping_related_and_unrelated(article_factory):
 a=article_factory(title='City council approves new transit plan',url='https://a.org/1',domain='a.org')
 b=article_factory(title='City council approved a new transit plan',url='https://b.org/2',domain='b.org')
 c=article_factory(title='City council announces library opening hours',url='https://c.org/3',domain='c.org')
 groups=group_stories([a,b,c])
 assert len(groups)>=2
def test_single_source_status(article_factory):
 s=group_stories([article_factory()])[0]
 assert assess_story(s)['status']=='SINGLE_SOURCE'
def test_multidomain_coverage_not_truth_probability(article_factory):
 a=article_factory(url='https://a.org/1',domain='a.org'); b=article_factory(url='https://b.org/2',domain='b.org',publisher='B')
 s=group_stories([a,b])[0]; v=assess_story(s)
 assert v['status']=='MULTI_SOURCE_SUPPORTED' and 'not probability' in v['coverage_note']
def test_outdated(article_factory):
 old=datetime.now(timezone.utc)-timedelta(days=30)
 s=group_stories([article_factory(published=old)])[0]
 assert assess_story(s,freshness_hours=168)['status']=='OUTDATED'
def test_independence_caveat(article_factory):
 x=assess_independence([article_factory(url='https://a.org/a',domain='a.org'),article_factory(url='https://b.org/b',domain='b.org')])
 assert x['independence']=='uncertain'
def test_url_safety():
 assert not validate_public_http_url('file:///etc/passwd')[0]
 assert not validate_public_http_url('http://127.0.0.1')[0]
 assert validate_public_http_url('https://example.com')[0]
def test_claims_not_fabricated(article_factory):
 s=group_stories([article_factory()])[0]; assert assess_story(s)['claims']==[]
