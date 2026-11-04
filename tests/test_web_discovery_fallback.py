from src import web_discovery


def test_configured_rss_fallback_when_search_providers_fail(monkeypatch, article_factory):
    article = article_factory()
    article.title = "Cybersecurity incident affects Indian banks"
    article.description = "A report about cybersecurity controls in India."
    monkeypatch.setattr(web_discovery.requests, "get", lambda *a, **k: (_ for _ in ()).throw(TimeoutError("provider timeout")))
    monkeypatch.setattr(web_discovery, "fetch_sources", lambda *a, **k: (
        [article], [{"source": "Fixture RSS", "ok": True, "count": 1, "error": ""}]
    ))
    monkeypatch.setattr("src.config_loader.load_sources", lambda: [{"name": "Fixture RSS", "url": "https://example.com/feed.xml", "enabled": True}])
    monkeypatch.setattr("src.config_loader.load_settings", lambda: {"news": {"request_timeout_seconds": 5, "max_response_bytes": 10000}})

    results, health = web_discovery.discover_web("cybersecurity India", max_results=10)

    assert results
    assert results[0].source_type == "configured_rss_fallback"
    assert any(item["provider"] == "Configured RSS fallback" and item["ok"] for item in health)
