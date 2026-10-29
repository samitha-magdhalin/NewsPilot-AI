from datetime import datetime, timezone
import pytest
from src.data_models import Article
@pytest.fixture
def article_factory():
 def make(title='City council approves new transit plan',url='https://example.org/story',publisher='Example',domain='example.org',published=None,description='Officials announced a new transit plan.'):
  return Article(title=title,canonical_url=url,original_url=url,publisher_name=publisher,publisher_domain=domain,description=description,published_at=published,fetched_at=datetime.now(timezone.utc)).ensure_id()
 return make
