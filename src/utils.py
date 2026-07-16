import json
import os
from pathlib import Path

import pandas as pd

CSV_FILE = Path(__file__).resolve().parents[1] / "data" / "research_results.csv"
JSON_FILE = Path(__file__).resolve().parents[1] / "data" / "research_results.json"
LOG_FILE = Path(__file__).resolve().parents[1] / "logs.txt"


def _normalize_result(result):
    if result is None:
        return None

    if hasattr(result, "model_dump"):
        return result.model_dump()

    return result


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