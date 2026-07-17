# Composio Toolkit Research — 100 Apps Case Study

A self-contained research pipeline and interactive case study for 100 SaaS apps. It extracts API/SDK metadata, authentication patterns, buildability signals, and verification flags, then produces a static HTML report and an optional Streamlit viewer.

- Repository: https://github.com/harshselokar26/composio-toolkit-research.git
- Live demo: https://earnest-treacle-7291ba.netlify.app/
- Deploy branch: `main`
- Netlify team: `harshselokar26’s team`
- Publish directory: `html/assets`

## Highlights

- Single-file deliverable: `html/assets/case_study.html` (interactive, Chart.js charts, embedded dataset and table)
- Pipeline drivers: `src/main.py` runs the research loop; `src/analysis.py` summarizes outputs and writes the case study HTML.
- Streamlit wrapper: `app.py` embeds the generated HTML for quick local viewing or Streamlit Cloud deployment.

## Project structure (top-level)

- `app.py` — netlify viewer that embeds the case study
- `html/assets/case_study.html` — generated interactive case study
- `data/apps.csv` — source list of apps to research
- `outputs/` — results written by the pipeline (`research_results.csv`, `research_results.json`, `analysis.json`, `verification_sample.csv`)
- `src/` — pipeline code: `main.py`, `analysis.py`, `research_agent.py`, `llm.py`, `utils.py`, `verifier.py`, etc.
- `requirements.txt` — Python dependencies (ensure UTF-8 encoding; see notes)

## Quickstart — fresh setup from clone to run

### 1. Clone the repository

```powershell
git clone https://github.com/harshselokar26/composio-toolkit-research.git
cd composio-toolkit-research
```

### 2. Create and activate a virtual environment

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```powershell
pip install -r requirements.txt
```

If `requirements.txt` has encoding issues, use this instead:

```powershell
pip install streamlit
pip install -r requirements.txt
```

Then freeze the exact installed dependencies:

```powershell
pip freeze > requirements.txt
```

### 4. Run the research pipeline

```powershell
python src/main.py
```

This command runs the full research pipeline across the 100 apps in `data/apps.csv`. It writes results into `outputs/`, generates analysis data, creates the Netlify-ready report at `html/assets/case_study.html`, and updates any charts used by the case study.

Useful options:

```powershell
python src/main.py --sample
python src/main.py --limit 10
python src/main.py --reset
```

- `--sample`: run only the short test set instead of all apps.
- `--limit 10`: run the first 10 apps only.
- `--reset`: delete old output files before running.

### 5. View the generated report

Open `html/assets/case_study.html` directly in a browser, or run the bundled Streamlit viewer:

```powershell
streamlit run app.py
```

Then visit `http://localhost:8501`.

### 6. Deploy to Netlify

- `Branch to deploy`: `main`
- `Base directory`: leave blank
- `Build command`: leave blank
- `Publish directory`: `html/assets`

Deploy the contents of the `html/assets` folder. The Streamlit app is only a local preview wrapper and is not required for Netlify.

> Live demo: https://earnest-treacle-7291ba.netlify.app/

## How it works (high level)

1. `src/main.py` loads `data/apps.csv` and iterates apps (or a sample when `--sample` is used).
2. For each app it calls `research_agent.research_app()` which uses `firecrawl` to find docs, scrapes pages, and collects markdown.
3. `src/llm.py` calls a Groq/OpenAI-compatible LLM to extract structured fields (auth_method, api_type, buildability, mcp_support, etc.) into an `AppResearch` model.
4. `src/verifier.py` normalizes and validates fields, adjusting confidence and flagging rows needing manual review.
5. Results are appended to `outputs/research_results.csv` and `outputs/research_results.json` via `src/utils.py`.
6. After the loop `src/analysis.py` computes distributions and writes `outputs/analysis.json` and `html/assets/case_study.html`.

## Regenerating the case study HTML

The HTML is produced automatically by `src/analysis.py` when `src/main.py` finishes. You can also call `generate_analysis()` directly from a Python REPL inside the `src/` directory:

```python
# from repo root
python -c "import src.analysis as a; a.generate_analysis()"
# or run inside src/
cd src
python analysis.py  # if adapted, otherwise use main.py flow
```

## netlify viewer (`app.py`)

`app.py` is a small wrapper that reads `html/assets/case_study.html` and renders it with `streamlit.components.v1.html()` so the page loads exactly as authored (Chart.js via CDN, embedded data). This is useful for quick demos and Streamlit Cloud deployments.



## Notes & troubleshooting

- `requirements.txt` in this repo may be in UTF-16 / contain null bytes if it was written with a different encoding. If `pip install -r requirements.txt` fails, regenerate it from an activated venv using `pip freeze > requirements.txt`.
- The LLM client in `src/llm.py` uses a GROQ/OpenAI-compatible client; ensure you have the correct API key(s) set in `src/config.py` before running the full pipeline.
- `src/extractor.py` exists but is empty in the checked-in state — the pipeline uses `firecrawl` scraping inside `src/research_agent.py` and LLM extraction in `src/llm.py`.

## Contributing

- Report issues or feature requests on GitHub.
- To add apps to the dataset, edit `data/apps.csv` and re-run the pipeline.

