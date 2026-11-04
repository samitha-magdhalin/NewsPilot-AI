# NewsPilot Phase 1 fixes

## Changes
- Added a configured publisher RSS fallback when Google News, Bing News, and GDELT return no results.
- Kept fallback status explicit so feed results are not misrepresented as full article text.
- Removed the manual "Retrieve available article text" action from Discover. Already-available article text can still be viewed.
- Social drafts now refresh when the underlying briefing summary changes.
- Searching related coverage from Graphic Studio now synchronizes the updated summary into the social-draft cache.
- Kept the graphic renderer local (Pillow); no paid image API or model key is required.

## Validation
- Automated test suite: 49 passed.
- Graphic smoke test: generated and verified a 1080 × 1350 PNG.

## Important limitations
- News availability still depends on public providers and the configured publisher feeds being reachable from the user's network/Streamlit Cloud.
- Publisher websites may block extraction or use paywalls/JavaScript. NewsPilot does not invent missing details; it must show a source-limited notice when no usable article prose is available.
- The graphic is an editorial composition rendered with Pillow, not a photorealistic AI image-generation service.

## Suggested next feature phases
1. Saved Stories with persistent hosted storage (Postgres/Supabase).
2. Source Comparison with publisher-by-publisher coverage and limitations.
3. Operations Monitor showing provider health, retrieval success, and failure diagnostics.
4. Manual Daily Digest with a downloadable briefing.
