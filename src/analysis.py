import json
from collections import Counter
from pathlib import Path

import pandas as pd

DATA_DIR = Path(__file__).resolve().parents[1] / "data"
CSV_FILE = DATA_DIR / "research_results.csv"
ANALYSIS_FILE = DATA_DIR / "analysis.json"
HTML_FILE = DATA_DIR / "case_study.html"


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
    if "manual_review" not in df or "name" not in df:
        return []

    rows = []
    for _, record in df[df["manual_review"].astype(str).str.lower().isin({"true", "1", "yes"})].iterrows():
        rows.append({
            "name": str(record.get("name", "Unknown")),
            "confidence": int(pd.to_numeric(record.get("confidence", 0), errors="coerce")) if pd.notna(record.get("confidence", None)) else 0,
            "issues": str(record.get("issues", "")).strip(),
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

    auth_method_counts = _counter(df["auth_method"]) if "auth_method" in df else {}
    self_serve_counts = _counter(df["self_serve"]) if "self_serve" in df else {}
    api_type_counts = _counter(df["api_type"]) if "api_type" in df else {}
    mcp_support_counts = _counter(df["mcp_support"]) if "mcp_support" in df else {}
    blocker_counts = _counter(df["blocker"]) if "blocker" in df else {}
    category_counts = _counter(df["category"]) if "category" in df else {}
    credential_counts = _counter(df["credential_requirement"]) if "credential_requirement" in df else {}

    review_rows = _serialize_review_rows(df)

    report = {
        "total_rows": total_rows,
        "manual_review_rate": manual_review_rate,
        "confidence": confidence_stats,
        "top_auth_methods": _top_items(auth_method_counts, total_rows),
        "top_self_serve": _top_items(self_serve_counts, total_rows),
        "top_api_types": _top_items(api_type_counts, total_rows),
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

    html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Composio Research Case Study</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 0; padding: 0; background: #f7f8fb; color: #111; }}
    .container {{ max-width: 1100px; margin: 0 auto; padding: 32px; }}
    header {{ margin-bottom: 32px; }}
    h1 {{ margin: 0; font-size: 2.4rem; }}
    .metrics {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 16px; margin: 24px 0; }}
    .metric-card {{ background: #fff; border-radius: 16px; padding: 18px 22px; box-shadow: 0 10px 30px rgba(0,0,0,0.06); }}
    .metric-card h2 {{ margin: 0 0 8px; font-size: 1rem; color: #555; }}
    .metric-card p {{ margin: 0; font-size: 1.5rem; font-weight: 700; }}
    section {{ margin-bottom: 32px; }}
    table {{ width: 100%; border-collapse: collapse; background: #fff; border-radius: 12px; overflow: hidden; box-shadow: 0 8px 24px rgba(0,0,0,0.05); }}
    th, td {{ text-align: left; padding: 14px 16px; border-bottom: 1px solid #eef2f7; }}
    th {{ background: #f5f7fb; font-weight: 700; }}
    tr:last-child td {{ border-bottom: none; }}
    .badge {{ display: inline-flex; padding: 4px 10px; border-radius: 999px; background: #e9f5ff; color: #1d72e8; font-size: 0.9rem; }}
  </style>
</head>
<body>
  <div class="container">
    <header>
      <p class="badge">Composio Research</p>
      <h1>Developer platform research summary</h1>
      <p>Analysis of {report['total_rows']} products with structured extraction, confidence scoring, and review guidance.</p>
    </header>

    <div class="metrics">
      <div class="metric-card"><h2>Total products</h2><p>{report['total_rows']}</p></div>
      <div class="metric-card"><h2>Average confidence</h2><p>{report['confidence']['mean']}%</p></div>
      <div class="metric-card"><h2>Review rate</h2><p>{report['manual_review_rate']}%</p></div>
      <div class="metric-card"><h2>Unique categories</h2><p>{len(report['categories'])}</p></div>
    </div>

    <section>
      <h2>Key findings</h2>
      <ul>
        {finding_items}
      </ul>
    </section>

    <section>
      <h2>Top distributions</h2>
      {distribution_html}
    </section>

    <section>
      <h2>Apps requiring manual review</h2>
      <table>
        <thead><tr><th>Application</th><th>Confidence</th><th>Issues</th></tr></thead>
        <tbody>
          {review_rows_html}
        </tbody>
      </table>
    </section>
  </div>
</body>
</html>
"""

    HTML_FILE.write_text(html, encoding="utf-8")
    print(f"Case study written to {HTML_FILE}")


if __name__ == "__main__":
    generate_analysis()