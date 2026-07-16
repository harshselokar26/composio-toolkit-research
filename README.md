# Composio Toolkit Research — 100 Apps Case Study

An automated research pipeline and self-contained interactive case study that inspects developer toolkits across 100 SaaS apps. The project extracts API/SDK metadata, authentication patterns, buildability signals, and verification flags — then produces a single-page HTML case study and optional Streamlit viewer.

Repository: https://github.com/harshselokar26/composio-toolkit-research.git

## Highlights

- Single-file deliverable: `html/assets/case_study.html` (interactive, Chart.js charts, embedded dataset and table)
- Pipeline drivers: `src/main.py` runs the research loop; `src/analysis.py` summarizes outputs and writes the case study HTML.
- Streamlit wrapper: `app.py` embeds the generated HTML for quick local viewing or Streamlit Cloud deployment.

## Project structure (top-level)

- `app.py` — Streamlit viewer that embeds the case study
- `html/assets/case_study.html` — generated interactive case study
- `data/apps.csv` — source list of apps to research
- `outputs/` — results written by the pipeline (`research_results.csv`, `research_results.json`, `analysis.json`, `verification_sample.csv`)
- `src/` — pipeline code: `main.py`, `analysis.py`, `research_agent.py`, `llm.py`, `utils.py`, `verifier.py`, etc.
- `requirements.txt` — Python dependencies (ensure UTF-8 encoding; see notes)

## Quickstart — run locally

1. From the repository root, create and activate a virtualenv (recommended):

```powershell
python -m venv .venv
# PowerShell
.\.venv\Scripts\Activate.ps1
# or cmd.exe
.venv\Scripts\activate.bat
```

2. Install dependencies. If `requirements.txt` looks corrupted (UTF-16 / BOM), regenerate it in your activated venv:

```powershell
# install minimal viewer
pip install streamlit
# or install all deps
pip install -r requirements.txt
# to regenerate clean UTF-8 requirements after installing, run:
pip freeze > requirements.txt
```

3. Run the full research pipeline (this will read `data/apps.csv`, execute the research agent for each app, save outputs, and generate the HTML):

```powershell
python src/main.py  # runs all apps
# short sample run (fast):
python src/main.py --sample
# limit number of apps:
python src/main.py --limit 10
# reset outputs before running:
python src/main.py --reset
```

4. View the generated HTML directly (open `html/assets/case_study.html` in a browser), or run the bundled Streamlit viewer:

```powershell
streamlit run app.py
# then open http://localhost:8501
```

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

## Streamlit viewer (`app.py`)

`app.py` is a small wrapper that reads `html/assets/case_study.html` and renders it with `streamlit.components.v1.html()` so the page loads exactly as authored (Chart.js via CDN, embedded data). This is useful for quick demos and Streamlit Cloud deployments.

## CSS animation example (copy into your HTML head or site CSS)

Use this snippet to animate metric cards (pulse + fade-in):

```css
.metric { display:inline-block; padding:18px 22px; border-radius:12px; background:#0f172a; color:#fff; transform-origin:center; }
@keyframes pulseUp { 0% { transform: translateY(0) scale(1); opacity: 0; } 50% { transform: translateY(-6px) scale(1.02); opacity: 1; } 100% { transform: translateY(0) scale(1); opacity: 1; } }
.metric.animated { animation: pulseUp 900ms cubic-bezier(.2,.9,.2,1) both; }
```

Quick JS to add the class on load:

```html
<script>
  window.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('.metric').forEach((el, i) => setTimeout(()=>el.classList.add('animated'), i*120));
  });
</script>
```

## Example: embedding the HTML in Streamlit (the project already includes `app.py`)

```python
import streamlit as st
from streamlit.components.v1 import html as st_html
html = open('html/assets/case_study.html','r',encoding='utf-8').read()
st.set_page_config(layout='wide')
st_html(html, height=1400, scrolling=True)
```

## Notes & troubleshooting

- `requirements.txt` in this repo may be in UTF-16 / contain null bytes if it was written with a different encoding. If `pip install -r requirements.txt` fails, regenerate it from an activated venv using `pip freeze > requirements.txt`.
- The LLM client in `src/llm.py` uses a GROQ/OpenAI-compatible client; ensure you have the correct API key(s) set in `src/config.py` before running the full pipeline.
- `src/extractor.py` exists but is empty in the checked-in state — the pipeline uses `firecrawl` scraping inside `src/research_agent.py` and LLM extraction in `src/llm.py`.

## Contributing

- Report issues or feature requests on GitHub.
- To add apps to the dataset, edit `data/apps.csv` and re-run the pipeline.

## License

See `LICENSE` in this repository.

---
If you want, I can now:

1. Add `streamlit` to `requirements.txt` and reformat the file as UTF-8.
2. Create a short animated GIF of the `case_study.html` for README display (I can generate a static GIF from a headless browser if you want).
3. Prepare a GitHub-ready branch and instructions for a Streamlit Cloud one-click deploy.

Reply with which of the above you'd like me to do next.
# composio-toolkit-research
AI-powered research pipeline for analyzing API toolkits, authentication methods, buildability, and MCP support across 100 SaaS applications.
