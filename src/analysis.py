import json
from collections import Counter
from pathlib import Path

import pandas as pd

OUTPUT_DIR = Path(__file__).resolve().parents[1] / "outputs"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

CSV_FILE = OUTPUT_DIR / "research_results.csv"
ANALYSIS_FILE = OUTPUT_DIR / "analysis.json"
HTML_FILE = Path(__file__).resolve().parents[1] / "html" / "assets" / "case_study.html"

FIELD_CANDIDATES = {
    "app": ["App", "app", "name"],
    "category": ["Category", "category"],
    "auth_method": ["Auth Method", "auth_method", "auth", "authentication"],
    "self_serve": ["Self Serve", "self_serve", "selfserve"],
    "api_type": ["API Type", "api_type", "api"],
    "buildability": ["Buildability", "buildability"],
    "mcp_support": ["MCP", "mcp", "mcp_support"],
    "blocker": ["Blocker", "blocker"],
    "confidence": ["Confidence", "confidence"],
    "needs_review": ["Needs Review", "manual_review", "needs_review"],
    "issues": ["Issues", "issues"],
}


def find_column(df: pd.DataFrame, names):
    lower_map = {col.lower(): col for col in df.columns}
    for name in names:
        if name in df.columns:
            return name
        if name.lower() in lower_map:
            return lower_map[name.lower()]
    return None


def lookup_series(df: pd.DataFrame, names, default="") -> pd.Series:
    column = find_column(df, names)
    if column is None:
        return pd.Series([default] * len(df), dtype=str)
    return df[column].fillna(default).astype(str).str.strip()


def _counter(series):
    values = [value for value in series.dropna().astype(str).tolist() if value.strip()]
    return dict(Counter(values).most_common())


def _to_bool_series(series):
    normalized = series.fillna(False).astype(str).str.lower()
    return normalized.isin({"true", "1", "yes"})


def _top_items(counter, total):
    if not counter or total == 0:
        return []
    return [
        {"value": key, "count": count, "share": round(count / total * 100, 1)}
        for key, count in counter.items()
    ]


def _build_findings(report):
    findings = []
    if report["total_rows"]:
        auth_items = report.get("top_auth_methods", [])
        if auth_items:
            findings.append(f"Top auth method is {auth_items[0]['value']} ({auth_items[0]['share']}%).")
        self_serve_items = report.get("top_self_serve", [])
        if self_serve_items:
            findings.append(f"Most products are {self_serve_items[0]['value']} ({self_serve_items[0]['share']}%).")
        blocker_items = report.get("top_blockers", [])
        if blocker_items:
            findings.append(f"Most common blocker is {blocker_items[0]['value']}.")
        if report["manual_review_rate"] >= 10:
            findings.append(f"{report['manual_review_rate']}% of rows need manual review.")
    return findings


def _serialize_review_rows(df):
    app_values = lookup_series(df, FIELD_CANDIDATES["app"], default="Unknown")
    confidence_values = lookup_series(df, FIELD_CANDIDATES["confidence"], default="0")
    issues_values = lookup_series(df, FIELD_CANDIDATES["issues"], default="")
    review_flags = _to_bool_series(lookup_series(df, FIELD_CANDIDATES["needs_review"], default="False"))

    rows = []
    for idx, needs_review in enumerate(review_flags):
        if not needs_review:
            continue
        rows.append({
            "name": app_values.iloc[idx],
            "confidence": int(pd.to_numeric(confidence_values.iloc[idx], errors="coerce") or 0),
            "issues": issues_values.iloc[idx],
        })
    return rows


def generate_analysis():
    if not CSV_FILE.exists():
        report = {
            "total_rows": 0,
            "message": "No research results found.",
        }
        ANALYSIS_FILE.write_text(json.dumps(report, indent=2), encoding="utf-8")
        return report

    df = pd.read_csv(CSV_FILE)

    confidence_series = pd.to_numeric(df["confidence"], errors="coerce").fillna(0) if "confidence" in df else pd.Series(dtype=float)
    manual_review_series = _to_bool_series(df["manual_review"]) if "manual_review" in df else pd.Series(dtype=bool)

    if confidence_series.empty:
        confidence_stats = {"mean": 0, "min": 0, "max": 0}
    else:
        confidence_stats = {
            "mean": round(float(confidence_series.mean()), 2),
            "min": int(confidence_series.min()),
            "max": int(confidence_series.max()),
        }

    manual_review_rate = round(float(manual_review_series.mean()) * 100, 2) if len(manual_review_series) else 0

    total_rows = int(len(df))

    auth_method_counts = _counter(lookup_series(df, FIELD_CANDIDATES["auth_method"]))
    self_serve_counts = _counter(lookup_series(df, FIELD_CANDIDATES["self_serve"]))
    api_type_counts = _counter(lookup_series(df, FIELD_CANDIDATES["api_type"]))
    buildability_counts = _counter(lookup_series(df, FIELD_CANDIDATES["buildability"]))
    mcp_support_counts = _counter(lookup_series(df, FIELD_CANDIDATES["mcp_support"]))
    blocker_counts = _counter(lookup_series(df, FIELD_CANDIDATES["blocker"]))
    category_counts = _counter(lookup_series(df, FIELD_CANDIDATES["category"]))
    credential_counts = _counter(lookup_series(df, ["Credential Requirement", "credential_requirement"]))

    review_rows = _serialize_review_rows(df)

    report = {
        "total_rows": total_rows,
        "manual_review_rate": manual_review_rate,
        "confidence": confidence_stats,
        "top_auth_methods": _top_items(auth_method_counts, total_rows),
        "top_self_serve": _top_items(self_serve_counts, total_rows),
        "top_api_types": _top_items(api_type_counts, total_rows),
        "top_buildability": _top_items(buildability_counts, total_rows),
        "top_mcp_support": _top_items(mcp_support_counts, total_rows),
        "top_blockers": _top_items(blocker_counts, total_rows),
        "top_categories": _top_items(category_counts, total_rows),
        "top_credential_requirements": _top_items(credential_counts, total_rows),
        "categories": category_counts,
        "findings": [],
        "apps_needing_review": review_rows,
        "verification_stats": {
            "manual_review_count": len(review_rows),
            "manual_review_rate": manual_review_rate,
            "average_confidence": confidence_stats["mean"],
            "min_confidence": confidence_stats["min"],
            "max_confidence": confidence_stats["max"],
        },
    }

    report["findings"] = _build_findings(report)

    ANALYSIS_FILE.write_text(json.dumps(report, indent=2), encoding="utf-8")
    generate_case_study_html(report, df)
    print(f"Analysis written to {ANALYSIS_FILE}")
    return report


def generate_case_study_html(report, df):
    top_rows = []
    for section, key in [
        ("Auth", "top_auth_methods"),
        ("Self Serve", "top_self_serve"),
        ("API Type", "top_api_types"),
        ("MCP", "top_mcp_support"),
        ("Blockers", "top_blockers"),
    ]:
        items = report.get(key, [])[:5]
        if items:
            top_rows.append((section, items))

    review_rows = _serialize_review_rows(df)
    findings = report.get("findings", [])

    finding_items = "".join(f"<li>{finding}</li>" for finding in findings)
    distribution_sections = []
    for section, items in top_rows:
        rows = "".join(
            f"<tr><td>{item['value']}</td><td>{item['count']}</td><td>{item['share']}%</td></tr>"
            for item in items
        )
        distribution_sections.append(
            f"<h3>{section}</h3>"
            f"<table><thead><tr><th>Value</th><th>Count</th><th>Share</th></tr></thead><tbody>{rows}</tbody></table>"
        )
    distribution_html = "".join(distribution_sections)

    review_rows_html = "".join(
        f"<tr><td>{item['name']}</td><td>{item['confidence']}%</td><td>{item['issues']}</td></tr>"
        for item in review_rows
    )

    top_categories_html = "".join(
        f"<li>{item['value']}: {item['count']} apps</li>" for item in report.get("top_categories", [])[:6]
    )
    chart_cards = "".join([
        "<div class='chart-card'><h3>Authentication distribution</h3><img src='charts/authentication_distribution.svg' alt='Authentication distribution'></div>",
        "<div class='chart-card'><h3>API type distribution</h3><img src='charts/api_type_distribution.svg' alt='API type distribution'></div>",
        "<div class='chart-card'><h3>Self serve distribution</h3><img src='charts/self_serve_distribution.svg' alt='Self serve distribution'></div>",
        "<div class='chart-card'><h3>Buildability distribution</h3><img src='charts/buildability_distribution.svg' alt='Buildability distribution'></div>",
    ])
    example_rows = []
    row_columns = [
        find_column(df, FIELD_CANDIDATES["app"]),
        find_column(df, FIELD_CANDIDATES["category"]),
        find_column(df, FIELD_CANDIDATES["auth_method"]),
        find_column(df, FIELD_CANDIDATES["api_type"]),
        find_column(df, FIELD_CANDIDATES["buildability"]),
        find_column(df, FIELD_CANDIDATES["confidence"]),
    ]
    for _, row in df.head(6).iterrows():
        cells = [str(row[col]) if col in row and pd.notna(row[col]) else "" for col in row_columns]
        example_rows.append(f"<tr>{''.join(f'<td>{cell}</td>' for cell in cells)}</tr>")
    example_rows_html = "".join(example_rows)

    full_table_rows = []
    full_columns = [
        find_column(df, FIELD_CANDIDATES["app"]),
        find_column(df, FIELD_CANDIDATES["category"]),
        find_column(df, FIELD_CANDIDATES["auth_method"]),
        find_column(df, FIELD_CANDIDATES["api_type"]),
        find_column(df, FIELD_CANDIDATES["buildability"]),
        find_column(df, FIELD_CANDIDATES["mcp_support"]),
        find_column(df, FIELD_CANDIDATES["confidence"]),
    ]
    for _, row in df.iterrows():
        cells = [str(row[col]) if col in row and pd.notna(row[col]) else "" for col in full_columns]
        full_table_rows.append(f"<tr>{''.join(f'<td>{cell}</td>' for cell in cells)}</tr>")
    full_table_html = "".join(full_table_rows)

    html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Composio Research Case Study</title>
  <style>
    body {{ font-family: Inter, system-ui, sans-serif; margin: 0; padding: 0; background: #f5f7fb; color: #111; }}
    .container {{ max-width: 1120px; margin: 0 auto; padding: 32px 24px; }}
    header {{ margin-bottom: 32px; }}
    .eyebrow {{ display: inline-flex; padding: 8px 14px; border-radius: 999px; background: #e9f5ff; color: #1d4ed8; font-size: 0.95rem; font-weight: 700; letter-spacing: 0.02em; }}
    h1 {{ margin: 16px 0 8px; font-size: clamp(2.25rem, 3vw, 3.1rem); line-height: 1.05; }}
    p.lead {{ max-width: 760px; font-size: 1.05rem; color: #4b5563; }}
    .summary-grid {{ display: grid; gap: 14px; margin-top: 28px; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); }}
    .card {{ background: #ffffff; border-radius: 20px; padding: 24px; box-shadow: 0 16px 45px rgba(15, 23, 42, 0.08); border: 1px solid rgba(148, 163, 184, 0.16); }}
    .card h2 {{ margin: 0 0 10px; font-size: 0.92rem; color: #334155; text-transform: uppercase; letter-spacing: 0.08em; }}
    .card p, .card span.value {{ margin: 0; font-size: 1.75rem; font-weight: 700; color: #0f172a; }}
    .metrics-grid {{ display: grid; gap: 14px; grid-template-columns: repeat(auto-fit, minmax(210px, 1fr)); }}
    section {{ margin-bottom: 42px; }}
    section h2 {{ margin-bottom: 18px; font-size: 1.55rem; color: #0f172a; }}
    section p {{ color: #475569; line-height: 1.75; }}
    .architecture {{ display: grid; gap: 10px; justify-items: center; text-align: center; margin: 0 auto; max-width: 420px; }}
    .architecture .step {{ width: 100%; background: #ffffff; border: 1px solid #dbeafe; border-radius: 18px; padding: 18px 16px; font-weight: 700; color: #0f172a; box-shadow: 0 12px 30px rgba(15, 23, 42, 0.05); }}
    .architecture .arrow {{ font-size: 1.4rem; color: #64748b; }}
    .workflow-list {{ display: grid; gap: 10px; }}
    .workflow-list li {{ background: #ffffff; border-radius: 14px; padding: 16px 18px; border: 1px solid #e2e8f0; box-shadow: 0 8px 25px rgba(15, 23, 42, 0.04); }}
    .chart-grid {{ display: grid; gap: 18px; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); }}
    .chart-card {{ background: #ffffff; border-radius: 20px; padding: 18px; border: 1px solid #e2e8f0; }}
    .chart-card h3 {{ margin: 0 0 10px; font-size: 1rem; color: #0f172a; }}
    .chart-card img {{ width: 100%; height: auto; display: block; }}
    .table-wrapper {{ overflow-x: auto; background: #ffffff; border-radius: 20px; border: 1px solid #e2e8f0; box-shadow: 0 12px 30px rgba(15, 23, 42, 0.05); }}
    table {{ width: 100%; border-collapse: collapse; min-width: 720px; }}
    th, td {{ padding: 14px 16px; border-bottom: 1px solid #e2e8f0; text-align: left; }}
    th {{ background: #f8fafc; color: #334155; font-weight: 700; }}
    tbody tr:hover {{ background: #f8fafc; }}
    .outline-list {{ list-style: none; padding: 0; margin: 0; display: grid; gap: 10px; }}
    .outline-list li {{ padding-left: 24px; position: relative; color: #334155; }}
    .outline-list li::before {{ content: "•"; position: absolute; left: 0; top: 0; color: #2563eb; }}
    .badge-pill {{ display: inline-flex; align-items: center; gap: 8px; padding: 7px 12px; border-radius: 999px; background: #eff6ff; color: #1d4ed8; font-size: 0.92rem; }}
    .search-bar {{ margin: 18px 0 14px; display: flex; gap: 12px; flex-wrap: wrap; }}
    .search-bar input {{ flex: 1; min-width: 220px; padding: 14px 16px; border-radius: 14px; border: 1px solid #cbd5e1; background: #fff; color: #0f172a; }}
    .footer-grid {{ display: grid; gap: 14px; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); }}
    .footer-card {{ display: block; background: #e2e8f0; border-radius: 18px; padding: 22px; text-decoration: none; color: #0f172a; }}
    .footer-card h3 {{ margin: 0 0 10px; font-size: 1rem; }}
  </style>
</head>
<body>
  <div class="container">
    <header>
      <span class="eyebrow">Composio Research</span>
      <h1>API toolkit discovery and validation case study</h1>
      <p class="lead">A concise review of the research pipeline that scanned a 100-app toolkit dataset, extracted API metadata, evaluated buildability, and surfaced confidence-backed verified results.</p>
    </header>

    <section id="project-summary">
      <h2>Project summary</h2>
      <p>This investigation used a 100-app source dataset and automated search, extraction, and validation steps to identify which products expose documented APIs, what authentication patterns they use, and how ready they are for developer integration.</p>
    </section>

    <section id="architecture">
      <h2>Architecture</h2>
      <div class="architecture">
        <div class="step">100 Apps CSV</div>
        <div class="arrow">▼</div>
        <div class="step">Firecrawl Search</div>
        <div class="arrow">▼</div>
        <div class="step">Top Documentation Pages</div>
        <div class="arrow">▼</div>
        <div class="step">Content Extraction</div>
        <div class="arrow">▼</div>
        <div class="step">Groq Structured Extraction</div>
        <div class="arrow">▼</div>
        <div class="step">Validation Rules</div>
        <div class="arrow">▼</div>
        <div class="step">Verification Agent</div>
        <div class="arrow">▼</div>
        <div class="step">Confidence Score</div>
        <div class="arrow">▼</div>
        <div class="step">CSV + JSON</div>
        <div class="arrow">▼</div>
        <div class="step">Analytics Generator</div>
        <div class="arrow">▼</div>
        <div class="step">Case Study</div>
      </div>
    </section>

    <section id="workflow">
      <h2>Workflow</h2>
      <ul class="workflow-list">
        <li>Load app titles and categories from the CSV source.</li>
        <li>Search for official documentation using Firecrawl.</li>
        <li>Extract API references and auth patterns from docs.</li>
        <li>Convert narrative text to structured fields using Groq.</li>
        <li>Apply validation rules and verify results with a review agent.</li>
        <li>Compute confidence scores and export cleaned CSV/JSON outputs.</li>
        <li>Generate charts, summaries, and a standalone case study page.</li>
      </ul>
    </section>

    <section id="overview">
      <h2>100 Apps overview</h2>
      <p>The dataset spans 100 applications across many SaaS categories. The top categories are:</p>
      <ul class="outline-list">
        {top_categories_html}
      </ul>
    </section>

    <section id="key-metrics">
      <h2>Key metrics</h2>
      <div class="metrics-grid">
        <div class="card"><h2>Most common auth</h2><p>{report['top_auth_methods'][0]['value'] if report['top_auth_methods'] else 'N/A'}</p></div>
        <div class="card"><h2>API type leader</h2><p>{report['top_api_types'][0]['value'] if report['top_api_types'] else 'N/A'}</p></div>
        <div class="card"><h2>Primary self-serve model</h2><p>{report['top_self_serve'][0]['value'] if report['top_self_serve'] else 'N/A'}</p></div>
        <div class="card"><h2>Buildability</h2><p>{report['top_buildability'][0]['value'] if report['top_buildability'] else 'N/A'}</p></div>
      </div>
    </section>

    <section id="charts">
      <h2>Charts</h2>
      <div class="chart-grid">
        {chart_cards}
      </div>
    </section>

    <section id="patterns">
      <h2>Patterns</h2>
      <p>These findings come directly from the verified dataset and highlight the most common implementation themes.</p>
      <ul class="outline-list">
        {finding_items or '<li>No findings were detected from the current data.</li>'}
      </ul>
    </section>

    <section id="verification">
      <h2>Verification</h2>
      <p>Results were verified with confidence scores and manual review flags to reduce ambiguity in the final dataset.</p>
      <div class="metrics-grid">
        <div class="card"><h2>Manual review count</h2><span class="value">{report['verification_stats']['manual_review_count']}</span></div>
        <div class="card"><h2>Review coverage</h2><span class="value">{report['manual_review_rate']}%</span></div>
        <div class="card"><h2>Confidence range</h2><span class="value">{report['confidence']['min']}–{report['confidence']['max']}%</span></div>
      </div>
    </section>

    <section id="example-rows">
      <h2>Example rows</h2>
      <div class="table-wrapper">
        <table>
          <thead>
            <tr><th>App</th><th>Category</th><th>Auth</th><th>API Type</th><th>Buildability</th><th>Confidence</th></tr>
          </thead>
          <tbody>
            {example_rows_html}
          </tbody>
        </table>
      </div>
    </section>

    <section id="searchable-table">
      <h2>Searchable table</h2>
      <div class="search-bar">
        <input id="tableSearch" type="search" placeholder="Search apps, categories, auth type, or buildability" aria-label="Search table">
      </div>
      <div class="table-wrapper">
        <table id="dataTable">
          <thead>
            <tr><th>App</th><th>Category</th><th>Auth</th><th>API Type</th><th>Buildability</th><th>MCP</th><th>Confidence</th></tr>
          </thead>
          <tbody>
            {full_table_html}
          </tbody>
        </table>
      </div>
    </section>

    <section id="limitations">
      <h2>Limitations</h2>
      <ul class="outline-list">
        <li>Data is derived from documentation search and may miss private or partner-only APIs.</li>
        <li>Confidence scores are based on extraction quality and require manual review for edge cases.</li>
        <li>Blocker classification is only as good as the source text available from docs.</li>
        <li>This report is a static case study, not a live hosted demo.</li>
      </ul>
    </section>

    <section id="github-live">
      <h2>GitHub and live demo</h2>
      <div class="footer-grid">
        <a class="footer-card" href="#">
          <h3>GitHub repository</h3>
          <p>Open the project source, pipeline code, and export data in the repository root.</p>
        </a>
        <a class="footer-card" href="#">
          <h3>Live demo</h3>
          <p>Inspect the generated CSV, charts, and case study locally for a complete review.</p>
        </a>
      </div>
    </section>
  </div>
  <script>
    const tableSearch = document.getElementById('tableSearch');
    const dataTable = document.getElementById('dataTable');
    tableSearch?.addEventListener('input', () => {{
      const query = tableSearch.value.trim().toLowerCase();
      Array.from(dataTable.tBodies[0].rows).forEach(row => {{
        const text = row.textContent.toLowerCase();
        row.style.display = text.includes(query) ? '' : 'none';
      }});
    }});
  </script>
</body>
</html>
"""

    HTML_FILE.write_text(html, encoding="utf-8")
    print(f"Case study written to {HTML_FILE}")


if __name__ == "__main__":
    generate_analysis()