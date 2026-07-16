import json
from collections import Counter
from pathlib import Path

import pandas as pd

DATA_DIR = Path(__file__).resolve().parents[1] / "data"
CSV_FILE = DATA_DIR / "research_results.csv"
ANALYSIS_FILE = DATA_DIR / "analysis.json"


def _counter(series):
    values = [value for value in series.dropna().astype(str).tolist() if value.strip()]
    return dict(Counter(values).most_common())


def _to_bool_series(series):
    normalized = series.fillna(False).astype(str).str.lower()
    return normalized.isin({"true", "1", "yes"})


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

    report = {
        "total_rows": int(len(df)),
        "manual_review_rate": manual_review_rate,
        "confidence": confidence_stats,
        "distributions": {
            "auth_method": _counter(df["auth_method"]) if "auth_method" in df else {},
            "self_serve": _counter(df["self_serve"]) if "self_serve" in df else {},
            "buildability": _counter(df["buildability"]) if "buildability" in df else {},
            "mcp_support": _counter(df["mcp_support"]) if "mcp_support" in df else {},
            "blocker": _counter(df["blocker"]) if "blocker" in df else {},
        },
        "categories": _counter(df["category"]) if "category" in df else {},
        "top_blockers": _counter(df["blocker"]) if "blocker" in df else {},
    }

    ANALYSIS_FILE.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"Analysis written to {ANALYSIS_FILE}")
    return report


if __name__ == "__main__":
    generate_analysis()