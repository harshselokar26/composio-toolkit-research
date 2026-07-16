Deploying the Case Study with Streamlit

This repo contains a single-page HTML case study at `html/assets/case_study.html` and a small Streamlit wrapper `app.py` that embeds it.

Quick local run

1. Create a Python virtual environment and activate it.

   python -m venv .venv
   # Windows PowerShell
   .\.venv\Scripts\Activate.ps1

2. Install Streamlit (and any other dependencies you need):

   pip install streamlit

3. Run the app:

   streamlit run app.py

Notes for Streamlit Cloud deployment

- Add `requirements.txt` including `streamlit` (this repo already has a `requirements.txt`; ensure `streamlit` is present).
- Ensure `app.py` is at the repository root (it is by default).
- On Streamlit Cloud, set the main file to `app.py` if required.

If you want, I can add `streamlit` to the repo `requirements.txt` and create a short `README.md` entry with a live demo link placeholder. Tell me if you'd like me to update `requirements.txt` automatically.