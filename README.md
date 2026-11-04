# NewsPilot — The Living Newsroom

A dark, editorial-style news research and content-creation app built with Python and Streamlit. Discover reporting, compare related coverage, draft social copy, create locally rendered editorial graphics, and export assets for review.

## Main workflow

1. **Discover** — search a topic or use a suggested topic; sort reports by trending coverage or recency.
2. On any article, choose **Create story** to open its briefing or **Create image** to open Graphic Studio for that same story.
3. **Coverage review** — compare grouped reports, publishers, and evidence limitations.
4. **Create studio** — review the source-grounded briefing, edit social drafts, generate a PNG graphic, and download individual assets or a ZIP bundle.

## Important limits

NewsPilot searches selected public news indexes and configured feeds; it does not search the entire internet. Search results depend on provider availability and network conditions. Publishers may restrict article extraction or require a subscription. Briefings and graphic supporting text use retrieved article text where available, refresh stale headline-only graphic text, and avoid repeating a headline as if it were a summary. If a publisher blocks retrieval and its feed has no meaningful description, the app explains that limitation rather than inventing details. Briefings are not an independent fact-check. Coverage labels indicate reporting availability, not truth.

Graphic templates are original, locally rendered illustrations with distinct compositions and palettes. They do not require an AI image API and are not photorealistic generative images. Nothing is automatically published to social media. Review original sources before sharing.

## Optional local LLM claim extraction

The app's default workflow remains model-free. To extract **candidate** claims from retrieved article text using a local Ollama model:

1. Install Ollama and pull a model, for example `ollama pull qwen2.5:3b`.
2. Create `config/settings.local.yaml` with the following local-only override. The default endpoint is `http://127.0.0.1:11434`; model inference stays on this computer. The local settings file is ignored by Git, while the checked-in defaults keep Ollama disabled for cloud deployments.

   ```yaml
   llm:
     enabled: true
   ```

3. In Create studio → Briefing, choose **Extract candidate claims with local model**. This requires full article text retrieved from a publisher; headlines and feed snippets are not sent as article evidence.

Each displayed candidate is linked to an excerpt that must match the retrieved text. This validates the citation text, **not whether the claim is true**. Claims stay marked as insufficient evidence and require human review. If Ollama is unavailable, the app reports the error and the existing model-free workflow is unchanged. Check the selected model's license and local hardware requirements. News discovery itself still uses internet-based providers.

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

## Live demo

🚀 **[Open NewsPilot AI](https://newspilotai.streamlit.app/)**

## Configuration

- `config/settings.yaml` — timeouts, freshness, storage, and output directory.
- `config/settings.local.yaml` — optional, Git-ignored machine-specific overrides.
- `config/sources.yaml` — optional RSS source configuration.

Keep source links and attribution intact and follow publishers' terms when using article text.
