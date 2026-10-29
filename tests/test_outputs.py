from pathlib import Path
from src.graphic_generator import make_graphic
from src.exporters import articles_csv,stories_json,briefing_markdown,social_txt,report_html
from src.social_writer import generate_posts,validate_post_lengths
from src.story_grouper import group_stories
from src.verification_engine import assess_story

def test_social_posts_are_review_drafts(article_factory):
 s=group_stories([article_factory()])[0]; v=assess_story(s); posts=generate_posts(s,{'summary':'Limited source description.'})
 assert all(k in posts for k in ('LinkedIn','Instagram','X','Facebook'))
 assert 'Human review' in posts['_review_required']
 assert validate_post_lengths(posts)['X']
def test_exports_have_data(article_factory):
 a=article_factory(); s=group_stories([a])[0]; v=assess_story(s); b={'summary':'Summary'}; posts=generate_posts(s,b)
 assert b'Source' in briefing_markdown(s,v,b) or b'source' in briefing_markdown(s,v,b).lower()
 assert b'example.org' in articles_csv([a]); assert b'City council' in stories_json([s]); assert b'LinkedIn' in social_txt(posts); assert b'<html' in report_html(s,v,b)
def test_graphic_generation(tmp_path,article_factory):
 p=make_graphic('A headline','A short summary',output_path=tmp_path/'graphic.png',size=(600,750))
 assert p.exists() and p.stat().st_size>1000


def test_live_validation_report_writer(tmp_path, monkeypatch):
    """Offline test: prove the diagnostic runner writes an honest report without network calls."""
    from src import live_validation as lv
    monkeypatch.setattr(lv, 'load_settings', lambda: {
        'news': {'freshness_hours':168,'max_articles':5,'request_timeout_seconds':1,'request_delay_seconds':0,'max_response_bytes':10000},
        'output_dir': str(tmp_path),
    })
    monkeypatch.setattr(lv, 'load_sources', lambda: [{'name':'Fixture','url':'https://example.com/feed.xml','enabled':True}])
    monkeypatch.setattr(lv, 'fetch_sources', lambda *a, **k: ([], [{'source':'Fixture','ok':False,'error':'offline','count':0}]))
    report=lv.run_validation(include_dashboard=False, include_live_feeds=True, output_dir=tmp_path)
    assert report['summary']['FAIL'] >= 1
    assert (tmp_path/'live_validation_report.json').exists()
    assert any(x['status']=='NOT RUN' for x in report['checks'])
    assert any(x['check']=='AI model dependency' and x['status']=='PASS' for x in report['checks'])
