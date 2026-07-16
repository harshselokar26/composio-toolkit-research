import argparse
from pathlib import Path

import pandas as pd
from tqdm import tqdm

from analysis import generate_analysis
from research_agent import research_app
from utils import CSV_FILE, JSON_FILE, LOG_FILE, append_log, save_json, save_result


def _load_apps(sample_mode: bool):
    apps = pd.read_csv("data/apps.csv")

    if sample_mode:
        test_app_names = [
            "Salesforce",
            "HubSpot",
            "Slack",
            "Stripe",
            "GitHub",
            "Shopify",
            "Notion",
            "Zendesk",
            "Twilio",
            "MongoDB Atlas",
        ]
        selected_rows = []
        for app_name in test_app_names:
            match = apps[apps["name"].str.strip() == app_name]
            if not match.empty:
                selected_rows.append(match.iloc[0])
        return pd.DataFrame(selected_rows)

    return apps


def _reset_outputs():
    for path in [CSV_FILE, JSON_FILE, LOG_FILE]:
        try:
            Path(path).unlink()
        except FileNotFoundError:
            pass


def main():
    parser = argparse.ArgumentParser(description="Run Composio research pipeline")
    parser.add_argument("--sample", action="store_true", help="Run the short sample set instead of all apps")
    parser.add_argument("--limit", type=int, default=None, help="Limit the number of apps to research")
    parser.add_argument("--reset", action="store_true", help="Reset output files before running")
    args = parser.parse_args()

    if args.reset:
        _reset_outputs()

    apps = _load_apps(args.sample)
    if args.limit:
        apps = apps.head(args.limit)

    for _, app in tqdm(
        apps.iterrows(),
        total=len(apps),
        desc="Researching Apps"
    ):
        try:
            result = research_app(
                app["name"],
                app["website"],
                app["category"]
            )

            save_result(result)
            save_json(result)

            if result is None:
                append_log(app["name"], False, "No documentation or research failed")
            else:
                append_log(app["name"], True)

        except Exception as e:
            append_log(app["name"], False, str(e))
            print(f"Failed: {app['name']}")
            print(e)

    generate_analysis()


if __name__ == "__main__":
    main()
