# Composio Toolkit Research — 100 Apps Case Study

Professional, self-contained case study and analytics generated from automated agent research across 100 apps.

Repository: https://github.com/harshselokar26/composio-toolkit-research.git

---

Quick overview

- Purpose: Generate a single-page interactive HTML case study that summarizes agent-driven findings across 100 apps (auth types, gate vs self-serve, API support, buildability, verification metrics, patterns, and charts).
- Output: `html/assets/case_study.html` — a self-contained interactive page (Chart.js, embedded data, searchable table).
- Streamlit wrapper: `app.py` — embeds the case study for local runs and Streamlit Cloud deployments.

Features

- Interactive charts (Chart.js) and verification visualizations
- Searchable, sortable table of the 100 apps (embedded as JS data)
- Inline SVG architecture diagrams and responsive layout
- Single-file case study that can be embedded or hosted

Quick start (local)

1. Clone the repo:

   git clone https://github.com/harshselokar26/composio-toolkit-research.git
   cd composio-toolkit-research

2. Create and activate a virtual environment (recommended):

   python -m venv .venv
   # Windows PowerShell
   .\.venv\Scripts\Activate.ps1

3. Install dependencies (this project uses `requirements.txt`):

   pip install -r requirements.txt

   If you prefer to only install Streamlit for the viewer:

   pip install streamlit

4. Run the Streamlit wrapper:

   streamlit run app.py

5. Open the app: http://localhost:8501

Notes

- The case study HTML is produced by the analysis scripts under `src/` (see `src/analysis.py`). If you regenerate the HTML, it will be written to `html/assets/case_study.html`.
- The project includes `html/assets/case_study.html` as a self-contained deliverable with embedded data and Chart.js via CDN.

Project layout (high level)

- `app.py` — Streamlit wrapper that embeds the HTML
- `html/assets/case_study.html` — generated case study (interactive)
- `src/` — generator scripts and pipeline (`analysis.py`, `extractor.py`, `research_agent.py`, etc.)
- `outputs/` — CSV/JSON outputs from runs (research_results.csv, research_results.json)
- `requirements.txt` — Python dependencies for the project

Deploying to Streamlit Cloud

1. Ensure `requirements.txt` contains `streamlit`.
2. Push the repo to GitHub (this repo URL is listed at the top).
3. Create a new app on Streamlit Cloud and point it to this repository; set the main file to `app.py` if asked.

Contributing

Contributions, fixes, or improvements are welcome. Please open issues or PRs against the repository.

License

See the repository `LICENSE` file for licensing information.

Contact

Open an issue on the GitHub repo for questions or demo requests.
# composio-toolkit-research
AI-powered research pipeline for analyzing API toolkits, authentication methods, buildability, and MCP support across 100 SaaS applications.
# Composio Toolkit Research Agent

## Overview

## Problem Statement

## Architecture

## Features

## Tech Stack

## Project Structure

## Installation

## Usage

## Research Workflow

## Verification Process

## Results

## Future Improvements

## License