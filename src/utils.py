import csv
import json
import os
import re
from pathlib import Path

import pandas as pd

OUTPUT_DIR = Path(__file__).resolve().parents[1] / "outputs"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

CSV_FILE = OUTPUT_DIR / "research_results.csv"
JSON_FILE = OUTPUT_DIR / "research_results.json"
ERROR_FILE = OUTPUT_DIR / "errors.csv"
VERIFICATION_FILE = OUTPUT_DIR / "verification_sample.csv"
LOG_FILE = OUTPUT_DIR / "logs.txt"

ENDPOINT_PATTERN = re.compile(r"\b(?:GET|POST|PUT|PATCH|DELETE|HEAD|OPTIONS)\s+/[^\s]*", re.IGNORECASE)


def _normalize_result(result):
    if result is None:
        return None

    if hasattr(result, "model_dump"):
        return result.model_dump()

    return result


def estimate_api_scope(markdown: str) -> str:
    if not isinstance(markdown, str) or not markdown.strip():
        return "Unknown"

    endpoints = ENDPOINT_PATTERN.findall(markdown)
    count = len(endpoints)

    explicit_match = re.search(r"(\d{1,4})\s+(?:endpoints|operations|routes|API methods)", markdown, re.IGNORECASE)
    if explicit_match:
        try:
            count = max(count, int(explicit_match.group(1)))
        except ValueError:
            pass

    if count >= 500:
        return "Very Large"
    if count >= 200:
        return "Large"
    if count >= 50:
        return "Medium"
    if count >= 1:
        return "Small"

    return "Unknown"


def save_result(result):
    result = _normalize_result(result)

    if result is None:
        return

    if "name" in result:
        result["App"] = result.pop("name")
    if "manual_review" in result:
        result["Needs Review"] = result.pop("manual_review")

    rename_map = {
        "category": "Category",
        "description": "Description",
        "auth_method": "Auth Method",
        "credential_requirement": "Credential Requirement",
        "self_serve": "Self Serve",
        "api_type": "API Type",
        "api_scope": "API Surface",
        "mcp_support": "MCP",
        "buildability": "Buildability",
        "blocker": "Blocker",
        "evidence_url": "Evidence URL",
        "confidence": "Confidence",
        "issues": "Issues",
    }

    df = pd.DataFrame([result])
    df = df.rename(columns=rename_map)
    columns_order = [
        "App",
        "Category",
        "Description",
        "Auth Method",
        "Credential Requirement",
        "Self Serve",
        "API Type",
        "API Surface",
        "MCP",
        "Buildability",
        "Blocker",
        "Evidence URL",
        "Confidence",
        "Needs Review",
        "Issues",
    ]
    columns_order = [col for col in columns_order if col in df.columns]
    df = df[columns_order]

    file_exists = CSV_FILE.exists()

    try:
        with open(CSV_FILE, "a" if file_exists else "w", encoding="utf-8", newline="") as file:
            df.to_csv(
                file,
                index=False,
                header=not file_exists
            )
    except PermissionError:
        existing = pd.read_csv(CSV_FILE) if file_exists else pd.DataFrame()
        combined = pd.concat([existing, df], ignore_index=True)
        temp_file = CSV_FILE.with_suffix(".tmp.csv")
        combined.to_csv(temp_file, index=False)
        os.replace(temp_file, CSV_FILE)


def save_json(result):
    result = _normalize_result(result)

    if result is None:
        return

    if JSON_FILE.exists():
        with open(JSON_FILE, encoding="utf-8") as file:
            data = json.load(file)
    else:
        data = []

    data.append(result)

    with open(JSON_FILE, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4)


def append_log(name, success, reason=""):
    status = "✔" if success else "❌"
    lines = [f"{name} {status}"]

    if reason:
        lines.append(reason)

    lines.append("")

    with open(LOG_FILE, "a", encoding="utf-8") as file:
        file.write("\n".join(lines))


def append_error(name, error, notes=""):
    fieldnames = ["app", "error", "notes"]
    write_header = not ERROR_FILE.exists()

    with open(ERROR_FILE, "a", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        if write_header:
            writer.writeheader()
        writer.writerow({
            "app": name,
            "error": error,
            "notes": notes,
        })