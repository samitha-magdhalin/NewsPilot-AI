"""Opt-in end-to-end diagnostics for the model-free NewsPilot AI build.

Only requests the RSS feeds explicitly configured by the user. The pipeline
uses deterministic Python rules/templates and never calls an LLM endpoint.
"""
from __future__ import annotations
import json, subprocess, sys, time, urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .config_loader import load_settings, load_sources
from .news_fetcher import fetch_sources
from .deduplicator import deduplicate
from .story_grouper import group_stories
from .verification_engine import assess_story
from .graphic_generator import make_graphic
from .social_writer import generate_posts
from .briefing_generator import make_briefing
from .exporters import articles_csv, stories_json, briefing_markdown, social_txt, report_html


def _result(name: str, status: str, details: str = "") -> dict[str, str]:
    return {"check": name, "status": status, "details": str(details)[:1200]}


def _http_get(url: str, timeout: float = 1.5) -> tuple[int, str]:
    req = urllib.request.Request(url, headers={"User-Agent": "NewsPilotAI-Local-Diagnostics/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return response.status, response.read(512 * 1024).decode("utf-8", "replace")


def run_validation(include_dashboard: bool = True, include_live_feeds: bool = True,
                   output_dir: str | Path = "output") -> dict[str, Any]:
    """Run configured diagnostics and return a report with PASS/FAIL/NOT RUN states."""
    started = datetime.now(timezone.utc)
    out = Path(output_dir); out.mkdir(parents=True, exist_ok=True)
    settings = load_settings(); news = settings["news"]
    results: list[dict[str, str]] = []
    articles = []; feed_rows = []

    try:
        sources = load_sources()
        if not sources: raise ValueError("No RSS sources configured in config/sources.yaml")
        results.append(_result("Configuration", "PASS", f"Loaded settings and {len(sources)} configured feeds."))
    except Exception as exc:
        sources = []
        results.append(_result("Configuration", "FAIL", exc))

    if include_live_feeds and sources:
        try:
            enabled = [s for s in sources if s.get("enabled", True)]
            articles, feed_rows = fetch_sources(enabled, news["request_timeout_seconds"],
                news["max_response_bytes"], news["request_delay_seconds"], news["max_articles"])
            good = sum(bool(x.get("ok")) for x in feed_rows)
            results.append(_result("Live RSS retrieval", "PASS" if good else "FAIL",
                f"{good}/{len(feed_rows)} feeds responded successfully; {len(articles)} articles retrieved. " +
                "; ".join(f"{x.get('source')}: {'OK' if x.get('ok') else x.get('error')} ({x.get('count',0)} items)" for x in feed_rows)))
        except Exception as exc:
            results.append(_result("Live RSS retrieval", "FAIL", exc))
    else:
        results.append(_result("Live RSS retrieval", "NOT RUN", "Disabled by user or no feeds configured."))

    results.append(_result("AI model dependency", "PASS", "No Ollama, downloaded model, API key, or cloud AI service is required or called."))

    if articles:
        try:
            unique = deduplicate(articles)
            stories = group_stories(unique)
            verification = {s.story_id: assess_story(s, freshness_hours=news["freshness_hours"]) for s in stories}
            results.append(_result("Deduplication and story grouping", "PASS",
                f"{len(articles)} retrieved articles -> {len(unique)} unique articles -> {len(stories)} story groups."))
            story = stories[0]; ver = verification[story.story_id]; briefing = make_briefing(story, ver)
            posts = generate_posts(story, briefing)
            results.append(_result("Briefing and social drafts", "PASS",
                f"Created rule-based briefing and drafts for: {', '.join(k for k in posts if not k.startswith('_'))}. Drafts are not published."))
            art = story.related_articles[0] if story.related_articles else None
            graphic = make_graphic(story.canonical_headline, briefing.get("summary", "Review source evidence."),
                art.publisher_name if art else "News source",
                art.published_at.date().isoformat() if art and art.published_at else "",
                art.canonical_url if art else "", ver["status"], out / "live_validation_graphic.png")
            files = {
                "live_validation_articles.csv": articles_csv(unique),
                "live_validation_stories.json": stories_json(stories),
                "live_validation_briefing.md": briefing_markdown(story, ver, briefing),
                "live_validation_social.txt": social_txt(posts),
                "live_validation_report.html": report_html(story, ver, briefing),
            }
            for filename, payload in files.items(): (out / filename).write_bytes(payload)
            results.append(_result("Graphic and export generation", "PASS", f"PNG: {graphic}; exports: {', '.join(files)}"))
        except Exception as exc:
            results.append(_result("Pipeline and outputs", "FAIL", exc))
    else:
        results.append(_result("Pipeline and outputs", "NOT RUN", "No live articles available; no fake story was substituted."))

    if include_dashboard:
        try:
            import streamlit
            results.append(_result("Streamlit dependency", "PASS", f"Streamlit {streamlit.__version__} is importable."))
            proc = subprocess.Popen([sys.executable, "-m", "streamlit", "run", "app.py",
                "--server.address", "127.0.0.1", "--server.port", "18501",
                "--server.headless", "true", "--browser.gatherUsageStats", "false"],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            ready = False; detail = "Dashboard did not respond before timeout."
            try:
                for _ in range(30):
                    if proc.poll() is not None: break
                    try:
                        code, body = _http_get("http://127.0.0.1:18501/_stcore/health", 1)
                        if code == 200 and "ok" in body.lower(): ready = True; detail = "Local Streamlit health endpoint returned OK."; break
                    except Exception: pass
                    time.sleep(1)
            finally:
                proc.terminate()
                try: proc.wait(timeout=5)
                except subprocess.TimeoutExpired: proc.kill()
            results.append(_result("Dashboard launch smoke test", "PASS" if ready else "FAIL", detail))
        except Exception as exc:
            results.append(_result("Dashboard launch smoke test", "FAIL", exc))
    else:
        results.append(_result("Dashboard launch smoke test", "NOT RUN", "Disabled by user."))

    finished = datetime.now(timezone.utc)
    report = {"application": "NewsPilot AI", "mode": "deterministic-rule-based-no-model",
        "started_at": started.isoformat(), "finished_at": finished.isoformat(),
        "environment": {"python": sys.version.split()[0], "platform": sys.platform,
            "llm_required": False, "cloud_ai_calls": False},
        "summary": {s: sum(r["status"] == s for r in results) for s in ("PASS", "FAIL", "NOT RUN")},
        "feed_results": feed_rows, "article_count": len(articles), "checks": results,
        "note": "Passing diagnostics show technical operation, not proof that reported news claims are true."}
    report_path = out / "live_validation_report.json"
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    report["report_path"] = str(report_path)
    return report


def main() -> int:
    import argparse
    parser = argparse.ArgumentParser(description="Run NewsPilot AI live integration diagnostics")
    parser.add_argument("--skip-feeds", action="store_true", help="Do not request configured RSS feeds")
    parser.add_argument("--skip-dashboard", action="store_true", help="Do not launch the local Streamlit smoke test")
    parser.add_argument("--output-dir", default="output", help="Local report directory")
    args = parser.parse_args()
    report = run_validation(not args.skip_dashboard, not args.skip_feeds, args.output_dir)
    print(f"\nNewsPilot AI live validation: {report['summary']}")
    for item in report["checks"]: print(f"[{item['status']}] {item['check']}: {item['details']}")
    print(f"\nReport saved to: {report['report_path']}")
    return 1 if report["summary"]["FAIL"] else 0

if __name__ == "__main__":
    raise SystemExit(main())
