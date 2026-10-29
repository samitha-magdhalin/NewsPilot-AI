import sqlite3, json
from pathlib import Path
class Store:
 def __init__(self,path='data/newspilot.sqlite3'):
  self.path=Path(path); self.path.parent.mkdir(parents=True,exist_ok=True)
  with self.connect() as c:
   c.execute('CREATE TABLE IF NOT EXISTS articles (article_id TEXT PRIMARY KEY, payload TEXT NOT NULL)')
   c.execute('CREATE TABLE IF NOT EXISTS stories (story_id TEXT PRIMARY KEY, payload TEXT NOT NULL)')
 def connect(self): return sqlite3.connect(self.path)
 def save_articles(self,articles):
  with self.connect() as c:
   for a in articles: c.execute('INSERT OR REPLACE INTO articles VALUES (?,?)',(a.article_id,a.model_dump_json()))
 def load_articles(self):
  from .data_models import Article
  with self.connect() as c: rows=c.execute('SELECT payload FROM articles').fetchall()
  return [Article.model_validate_json(r[0]) for r in rows]
 def save_stories(self,stories):
  with self.connect() as c:
   for s in stories: c.execute('INSERT OR REPLACE INTO stories VALUES (?,?)',(s.story_id,s.model_dump_json()))
 def clear_cache(self):
  with self.connect() as c: c.execute('DELETE FROM articles'); c.execute('DELETE FROM stories')
