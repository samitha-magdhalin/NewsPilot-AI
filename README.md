# NewsPilot — The Living Newsroom

A dark, editorial-style news research and content-creation app built with Python and Streamlit. Discover reporting, compare related coverage, draft social copy, create locally rendered editorial graphics, and export assets for review.

## Main workflow

1. **Discover** — search a topic or use a suggested topic; sort reports by trending coverage or recency.
2. On any article, choose **Create story** to open its briefing or **Create image** to open Graphic Studio for that same story.
3. **Coverage review** — compare grouped reports, publishers, and evidence limitations.
4. **Create studio** — review the source-grounded briefing, edit social drafts, generate a PNG graphic, and download individual assets or a ZIP bundle.

## Important limits

NewsPilot searches selected public news indexes and configured feeds; it does not search the entire internet. Search results depend on provider availability and network conditions. Publishers may restrict article extraction or require a subscription. Briefings and graphic supporting text use retrieved article text where available, refresh stale headline-only graphic text, and avoid repeating a headline as if it were a summary. Graphic Studio also offers a direct article-text retrieval action when the feed contains only a headline. If a publisher blocks retrieval and its feed has no meaningful description, the app explains that limitation rather than inventing details. Briefings are not an independent fact-check. Coverage labels indicate reporting availability, not truth.

Graphic templates are original, locally rendered illustrations with distinct compositions and palettes. They do not require an AI image API and are not photorealistic generative images. Nothing is automatically published to social media. Review original sources before sharing.

## Run on Windows

1. Install Python 3.11 or newer.
2. Open PowerShell in the folder containing `app.py` and `requirements.txt` (the `NewsPilot-AI` folder).
3. Create and install dependencies:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pytest -q tests
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Or use `setup_windows.bat` followed by `run_windows.bat`. The app normally opens at `http://localhost:8501`.

## Tests

```powershell
python -m pytest -q tests
```

## Deploy a shareable demo with Streamlit Community Cloud

1. Create a GitHub repository and upload the **contents of this `newspilot-ai` folder**. Do not upload `.venv`, Python caches, the local SQLite database, or generated PNG outputs.
2. Confirm that `app.py`, `requirements.txt`, `src/`, and `config/` are at the repository root.
3. Open [Streamlit Community Cloud](https://share.streamlit.io/) and choose **Create app**. Select your repository, branch, and `app.py` as the main file.
4. Keep `packages.txt` at the repository root. It installs the TrueType font used by the graphic renderer so generated text stays correctly sized in the Linux deployment.
5. Deploy and wait for the build to finish; then share the generated app URL with your reviewer. If the app is already deployed, reboot it after adding `packages.txt` so the system font is installed.

The cloud runtime has its own filesystem. Local SQLite cache and generated files should be treated as temporary and may not persist across restarts. Never commit API keys or secrets; put any required secrets in the deployment platform's secrets manager.

## Configuration

- `config/settings.yaml` — timeouts, freshness, storage, and output directory.
- `config/sources.yaml` — optional RSS source configuration.

Keep source links and attribution intact and follow publishers' terms when using article text.
