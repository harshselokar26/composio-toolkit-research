import json
import os
import re
from pathlib import Path

import pandas as pd

CSV_FILE = Path(__file__).resolve().parents[1] / "data" / "research_results.csv"
JSON_FILE = Path(__file__).resolve().parents[1] / "data" / "research_results.json"
LOG_FILE = Path(__file__).resolve().parents[1] / "logs.txt"

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

    df = pd.DataFrame([result])
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