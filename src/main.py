import pandas as pd
from tqdm import tqdm

from analysis import generate_analysis
from research_agent import research_app
from utils import append_log, save_json, save_result

apps = pd.read_csv("data/apps.csv")

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

apps = pd.DataFrame(selected_rows)

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
            append_log(app["name"], False, "No Docs or research failed")
        else:
            append_log(app["name"], True)

    except Exception as e:
        append_log(app["name"], False, str(e))
        print(f"Failed: {app['name']}")
        print(e)

generate_analysis()
