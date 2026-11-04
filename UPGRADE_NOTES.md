# NewsPilot — bug-fix and next-phase notes

## Changes in this update

- Replaced the Create Studio output dropdown with visible horizontal choices: Briefing, Social posts, and Graphic studio.
- Replaced the graphic style and canvas-size dropdowns with visible radio choices so the available options are discoverable without opening menus.
- Made PNG preview state resilient across Streamlit reruns: the app now keeps verified image bytes in session state, reloads the generated image, and renders the preview from a decoded Pillow image.
- The app now reruns after a successful render so the preview panel is refreshed immediately.
- Added a briefing safeguard that rejects feed descriptions dominated by publisher navigation, newsletter, or sitemap text.
- Preserved the existing dark theme, story workflows, source-grounding safeguards, and local Pillow graphic renderer.

## Validation

- Python compilation: passed.
- Automated test suite: **49 passed**.

## Recommended next features (Phase 2)

1. **Saved stories and cloud persistence** — move saved story records from local-only SQLite to a hosted PostgreSQL database (for example, Supabase) so saved work survives Streamlit Cloud restarts and is available across sessions.
2. **Story library** — bookmark stories, add tags and notes, filter by topic/date/publisher, and reopen a saved story directly in Create Studio.
3. **Operations monitor** — a compact health view for feed freshness, source failures, extraction success rate, duplicate rate, and last successful refresh. Show actionable errors, not raw technical logs.
4. **Publisher comparison** — compare the selected story's coverage by publisher, what each source adds, publication times, and access limitations. Clearly distinguish article text from feed snippets.
5. **Manual daily digest** — let the user select saved stories, generate an editable digest, preview it, and download Markdown/PDF. No automatic sending or publishing.
6. **Optional AI image provider** — the current renderer creates designed editorial PNGs locally with Pillow; it is not a photorealistic image-generation model. A future optional provider integration can generate original artwork when an API key is configured, while keeping the local renderer as a reliable fallback.

## Deployment reminder

Deploy this version only after reviewing the changes locally. The `packages.txt` font dependency is retained for Streamlit Cloud. No API key is required for the current local graphic renderer.
