# NewsPilot news-agent evaluation task

## Task prompt

For a topic supplied by the evaluator, find the newest relevant reporting available
within the requested time window. Summarize only facts supported by retrieved
reporting, compare sources for corroboration and disagreement, and provide links
and publication times for each source. Distinguish original reporting from
syndicated copies; do not treat publisher count, a model-generated claim, or a
source-coverage label as proof of truth. If evidence is limited or conflicting,
say so. Draft platform-appropriate social posts with source links for human
review; do not publish them.

The evaluator should record the topic, time window, run time, retrieved articles,
and source URLs so the result can be reproduced.

## Scoring rubric (10 points)

Score each category from 0 to 2 and cite output evidence for every score.

| Category | 0 points | 1 point | 2 points |
|---|---|---|---|
| Recency | Uses undated or out-of-window reporting as current without warning. | Includes publication times but has a stale or unclear item. | Prioritizes in-window reporting and labels missing or stale dates. |
| Corroboration | Treats one report or publisher count as confirmation. | Lists multiple sources but does not assess overlap or independence. | Compares evidence, flags likely syndication, and describes independence as uncertain unless established. |
| Conflicts and uncertainty | Hides disagreement or presents unsupported claims as facts. | Mentions limitations without identifying the affected claim. | Identifies the disputed claim, summarizes each side with sources, and states what remains unresolved. |
| Source attribution | Omits or mismatches citations. | Provides links but lacks useful publisher/date context. | Links each key assertion to the correct publisher and publication time. |
| Social drafts | Drafts are misleading, uncited, or presented as published. | Drafts are usable but need significant correction or attribution. | Drafts are platform-appropriate, source-linked, cautious, and clearly require human review. |

Any invented factual detail, fabricated citation, or claim that a source-coverage
status proves truth must be recorded as a critical failure regardless of the
numeric score.

## Deterministic acceptance checks

Run the offline checks with:

```powershell
python -m pytest -q tests/test_news_evaluation.py
```

They exercise the recency boundary, source-coverage caveat, propagation of an
explicit conflict status, source links in briefings and social drafts, and the
X character limit. These checks use synthetic data: they test handling and
formatting, not whether real-world reporting is true.

## Current capability limits

- Story-level coverage is based on article dates and publisher domains. Different
  domains do not establish independently reported confirmation.
- Contradictions must already be represented as claim-level evidence/status;
  the current pipeline does not independently infer conflicts by comparing
  article text.
- Ollama extracts candidate claims and checks that excerpts occur in retrieved
  text. It does not fact-check those claims.
- Live-feed availability and search coverage vary by provider and network.
  Record failed feeds and do not treat a successful pipeline run as a truth score.
