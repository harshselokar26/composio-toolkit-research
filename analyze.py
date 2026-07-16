import json
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

plt.switch_backend("Agg")

ROOT = Path(__file__).resolve().parent
OUTPUTS = ROOT / "outputs"
CHART_DIR = ROOT / "charts"
CHART_DIR.mkdir(exist_ok=True)

INPUT_CANDIDATES = [
    OUTPUTS / "research_results.csv",
    ROOT / "research_results.csv",
    ROOT / "data" / "research_results.csv",
]

FALLBACK_COLUMNS = {
    "App": ["App", "app", "name"],
    "Category": ["Category", "category"],
    "Auth Method": ["Auth Method", "auth_method", "auth", "authentication"],
    "API Type": ["API Type", "api_type", "api"],
    "Self Serve": ["Self Serve", "self_serve", "selfserve"],
    "Buildability": ["Buildability", "buildability"],
    "Blocker": ["Blocker", "blocker"],
    "MCP": ["MCP", "mcp", "mcp_support"],
    "Confidence": ["Confidence", "confidence"],
    "Needs Review": ["Needs Review", "manual_review", "needs_review"],
}


def find_column(df: pd.DataFrame, names):
    lower_map = {col.lower(): col for col in df.columns}
    for name in names:
        if name in df.columns:
            return name
        if name.lower() in lower_map:
            return lower_map[name.lower()]
    return None


def lookup_series(df: pd.DataFrame, names, default="Unknown") -> pd.Series:
    column = find_column(df, names)
    if column is None:
        return pd.Series([default] * len(df), dtype=str)
    return df[column].fillna(default).astype(str).str.strip().replace({"": default})


def normalize_auth(series: pd.Series) -> pd.Series:
    normalized = []
    for value in series.fillna("Unknown").astype(str):
        text = value.lower()
        if "oauth" in text:
            normalized.append("OAuth2")
        elif "api key" in text or "api-key" in text:
            normalized.append("API Key")
        elif "personal access" in text or "pat" in text:
            normalized.append("PAT")
        elif "basic" in text:
            normalized.append("Basic")
        elif value.strip().lower() in {"unknown", "none", "nan"}:
            normalized.append("Unknown")
        elif text.strip() == "":
            normalized.append("Unknown")
        else:
            normalized.append("Other")
    return pd.Series(normalized)


def normalize_api_type(series: pd.Series) -> pd.Series:
    normalized = []
    for value in series.fillna("Unknown").astype(str):
        text = value.lower()
        if "graphql" in text and "rest" in text:
            normalized.append("Mixed")
        elif "graphql" in text:
            normalized.append("GraphQL")
        elif "soap" in text:
            normalized.append("SOAP")
        elif "rest" in text or "api" in text:
            normalized.append("REST")
        elif value.strip().lower() in {"unknown", "none", "nan"}:
            normalized.append("Unknown")
        else:
            normalized.append("Other")
    return pd.Series(normalized)


def normalize_self_serve(series: pd.Series) -> pd.Series:
    normalized = []
    for value in series.fillna("Unknown").astype(str):
        text = value.lower()
        if "self" in text:
            normalized.append("Self Serve")
        elif "enterprise" in text:
            normalized.append("Enterprise")
        elif "admin" in text or "approval" in text:
            normalized.append("Admin Approval")
        elif "paid" in text or "sales" in text or "trial" in text:
            normalized.append("Paid Plan")
        elif value.strip().lower() in {"unknown", "none", "nan"}:
            normalized.append("Unknown")
        else:
            normalized.append("Other")
    return pd.Series(normalized)


def normalize_buildability(series: pd.Series) -> pd.Series:
    normalized = []
    for value in series.fillna("Unknown").astype(str):
        text = value.lower()
        if "yes" in text:
            normalized.append("Yes")
        elif "partial" in text or "limited" in text:
            normalized.append("Partial")
        elif "no" in text or "contact" in text:
            normalized.append("No")
        elif value.strip().lower() in {"unknown", "none", "nan"}:
            normalized.append("Unknown")
        else:
            normalized.append("Other")
    return pd.Series(normalized)


def normalize_mcp(series: pd.Series) -> pd.Series:
    normalized = []
    for value in series.fillna("Unknown").astype(str):
        text = value.lower()
        if "yes" in text or "supported" in text:
            normalized.append("Yes")
        elif "no" in text or "unsupported" in text:
            normalized.append("No")
        elif value.strip().lower() in {"unknown", "none", "nan"}:
            normalized.append("Unknown")
        else:
            normalized.append("Unknown")
    return pd.Series(normalized)


def normalize_blocker(series: pd.Series) -> pd.Series:
    normalized = []
    for value in series.fillna("Unknown").astype(str):
        text = value.lower()
        if value.strip() == "" or value.strip().lower() in {"none", "unknown", "nan"}:
            normalized.append("Unknown")
        elif "paid" in text or "plan" in text:
            normalized.append("Paid plan required")
        elif "partner" in text or "approval" in text:
            normalized.append("Partner approval")
        elif "no public api" in text or "no api" in text or "unsupported" in text:
            normalized.append("No public API")
        elif "limited" in text or "poor" in text or "documentation" in text:
            normalized.append("Limited documentation")
        else:
            normalized.append(value.strip())
    return pd.Series(normalized)


def count_distribution(series: pd.Series) -> list[dict[str, int]]:
    counts = series.fillna("Unknown").replace({"": "Unknown"}).value_counts(dropna=False)
    return [{"value": str(value), "count": int(count)} for value, count in counts.items()]


def safe_numeric(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce").fillna(0).astype(int)


def plot_bar_chart(title: str, items: list[dict[str, int]], filepath: Path):
    labels = [item["value"] for item in items]
    values = [item["count"] for item in items]
    palette = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd", "#8c564b", "#e377c2"]

    fig, ax = plt.subplots(figsize=(10, max(4, len(labels) * 0.7)))
    fig.patch.set_facecolor("#ffffff")
    ax.set_facecolor("#fbfbfb")

    bars = ax.barh(labels, values, color=[palette[i % len(palette)] for i in range(len(labels))], edgecolor="#333333", height=0.6)
    ax.invert_yaxis()
    ax.set_title(title, fontsize=20, pad=18, color="#222222")
    ax.set_xlabel("Count", fontsize=14, color="#333333")
    ax.tick_params(axis="x", labelsize=12, colors="#333333")
    ax.tick_params(axis="y", labelsize=12, colors="#333333")
    ax.grid(axis="x", linestyle="--", alpha=0.25, color="#bbbbbb")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_visible(False)
    ax.spines["bottom"].set_color("#cccccc")

    for bar in bars:
        width = bar.get_width()
        ax.text(width + max(values) * 0.01, bar.get_y() + bar.get_height() / 2,
                f"{int(width)}", va="center", fontsize=12, color="#222222")

    plt.tight_layout(pad=1.2)
    fig.savefig(filepath, format="svg", bbox_inches="tight")
    plt.close(fig)


def plot_histogram(title: str, series: pd.Series, filepath: Path):
    fig, ax = plt.subplots(figsize=(9, 5))
    fig.patch.set_facecolor("#ffffff")
    ax.set_facecolor("#fbfbfb")

    n, bins, patches = ax.hist(series, bins=10, color="#1f77b4", edgecolor="#333333", alpha=0.92)
    ax.set_title(title, fontsize=20, pad=18, color="#222222")
    ax.set_xlabel("Confidence")
    ax.set_ylabel("Applications")
    ax.grid(axis="y", linestyle="--", alpha=0.25, color="#bbbbbb")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_visible(False)
    ax.spines["bottom"].set_color("#cccccc")

    for i, count in enumerate(n):
        if count > 0:
            ax.text((bins[i] + bins[i + 1]) / 2, count + max(n) * 0.02,
                    f"{int(count)}", ha="center", va="bottom", fontsize=11, color="#222222")

    plt.tight_layout(pad=1.2)
    fig.savefig(filepath, format="svg", bbox_inches="tight")
    plt.close(fig)


def cross_tab(df: pd.DataFrame, row: str, col: str) -> dict[str, dict[str, int]]:
    table = pd.crosstab(df[row], df[col], dropna=False)
    return {str(index): {str(col_name): int(value) for col_name, value in row_data.items()} for index, row_data in table.iterrows()}


def load_data() -> pd.DataFrame:
    for path in INPUT_CANDIDATES:
        if path.exists():
            return pd.read_csv(path)
    raise FileNotFoundError("research_results.csv not found in outputs/, root, or data/.")


def main():
    df = load_data()

    df["Auth Normalized"] = normalize_auth(lookup_series(df, FALLBACK_COLUMNS["Auth Method"]))
    df["API Type Normalized"] = normalize_api_type(lookup_series(df, FALLBACK_COLUMNS["API Type"]))
    df["Self Serve Normalized"] = normalize_self_serve(lookup_series(df, FALLBACK_COLUMNS["Self Serve"]))
    df["Buildability Normalized"] = normalize_buildability(lookup_series(df, FALLBACK_COLUMNS["Buildability"]))
    df["MCP Normalized"] = normalize_mcp(lookup_series(df, FALLBACK_COLUMNS["MCP"]))
    df["Blocker Normalized"] = normalize_blocker(lookup_series(df, FALLBACK_COLUMNS["Blocker"]))
    df["Confidence Numeric"] = safe_numeric(lookup_series(df, FALLBACK_COLUMNS["Confidence"], default="0"))
    df["Needs Review Flag"] = lookup_series(df, FALLBACK_COLUMNS["Needs Review"], default="False").str.lower().isin({"true", "1", "yes"})
    df["Category Normalized"] = lookup_series(df, FALLBACK_COLUMNS["Category"], default="Unknown")

    report = {
        "authentication_distribution": count_distribution(df["Auth Normalized"]),
        "api_type_distribution": count_distribution(df["API Type Normalized"]),
        "self_serve_distribution": count_distribution(df["Self Serve Normalized"]),
        "buildability_distribution": count_distribution(df["Buildability Normalized"]),
        "mcp_distribution": count_distribution(df["MCP Normalized"]),
        "blocker_distribution": count_distribution(df["Blocker Normalized"]),
        "confidence_summary": {
            "average": round(float(df["Confidence Numeric"].mean()), 2) if len(df) else 0,
            "median": round(float(df["Confidence Numeric"].median()), 2) if len(df) else 0,
            "lowest": int(df["Confidence Numeric"].min()) if len(df) else 0,
            "highest": int(df["Confidence Numeric"].max()) if len(df) else 0,
            "manual_review_count": int(df["Needs Review Flag"].sum()),
        },
        "counts_by_category": df["Category Normalized"].value_counts(dropna=False).to_dict(),
        "auth_by_category": cross_tab(df, "Category Normalized", "Auth Normalized"),
        "self_serve_by_category": cross_tab(df, "Category Normalized", "Self Serve Normalized"),
        "buildability_by_category": cross_tab(df, "Category Normalized", "Buildability Normalized"),
    }

    summary_path = ROOT / "summary.json"
    summary_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    plot_bar_chart("Authentication Distribution", report["authentication_distribution"], CHART_DIR / "authentication_distribution.svg")
    plot_bar_chart("API Type Distribution", report["api_type_distribution"], CHART_DIR / "api_type_distribution.svg")
    plot_bar_chart("Self Serve Distribution", report["self_serve_distribution"], CHART_DIR / "self_serve_distribution.svg")
    plot_bar_chart("Buildability Distribution", report["buildability_distribution"], CHART_DIR / "buildability_distribution.svg")
    plot_bar_chart("MCP Support", report["mcp_distribution"], CHART_DIR / "mcp_distribution.svg")
    plot_bar_chart("Blocker Distribution", report["blocker_distribution"], CHART_DIR / "blocker_distribution.svg")
    plot_histogram("Confidence Distribution", df["Confidence Numeric"], CHART_DIR / "confidence_distribution.svg")

    print(f"Wrote {summary_path}")
    print(f"Wrote charts to {CHART_DIR}")


if __name__ == "__main__":
    main()
