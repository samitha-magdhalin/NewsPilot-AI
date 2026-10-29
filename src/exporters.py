import json, csv, io, html
from pathlib import Path
import pandas as pd

def articles_csv(articles):
 rows=[{'title':a.title,'publisher':a.publisher_name,'url':a.canonical_url,'published_at':a.published_at.isoformat() if a.published_at else '', 'fetched_at':a.fetched_at.isoformat(),'story_id':'','verification_status':''} for a in articles]
 return pd.DataFrame(rows,columns=['title','publisher','url','published_at','fetched_at','story_id','verification_status']).to_csv(index=False).encode()
def stories_json(stories): return json.dumps([s.model_dump(mode='json') for s in stories],ensure_ascii=False,indent=2,default=str).encode()
def briefing_markdown(story, verification, briefing):
 lines=[f"# {story.canonical_headline}",f"\n**Status:** {verification['status']}",f"\n{briefing.get('summary','')}","\n## Sources"]
 for a in story.related_articles: lines.append(f"- [{a.publisher_name}: {a.title}]({a.canonical_url}) — {a.published_at.isoformat() if a.published_at else 'date unavailable'}")
 lines += ['\n## Limitations']+['- '+x for x in verification.get('limitations',[])]
 return '\n'.join(lines).encode()
def social_txt(posts): return '\n\n'.join(f'## {k}\n{v}' for k,v in posts.items() if not k.startswith('_')).encode()
def report_html(story, verification, briefing):
 links=''.join(f'<li><a href="{html.escape(a.canonical_url,quote=True)}">{html.escape(a.publisher_name)}: {html.escape(a.title)}</a></li>' for a in story.related_articles)
 return (f'<!doctype html><html><meta charset="utf-8"><title>NewsPilot report</title><body style="font-family:Arial;max-width:900px;margin:3rem auto;line-height:1.5"><h1>{html.escape(story.canonical_headline)}</h1><p><b>Status:</b> {verification["status"]}</p><p>{html.escape(briefing.get("summary",""))}</p><h2>Sources</h2><ul>{links}</ul><h2>Limitations</h2><ul>'+''.join(f'<li>{html.escape(x)}</li>' for x in verification.get('limitations',[]))+'</ul></body></html>').encode()
