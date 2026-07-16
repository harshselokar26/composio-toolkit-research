import json

from openai import OpenAI

from config import GROQ_API_KEY
from models import AppResearch
from prompts import DESCRIPTION_SYSTEM_PROMPT, SYSTEM_PROMPT, USER_PROMPT
from utils import estimate_api_scope

client = OpenAI(
    api_key=GROQ_API_KEY,
    base_url="https://api.groq.com/openai/v1"
)

GROQ_MODEL = "llama-3.1-8b-instant"


def describe_app(name, category, website, markdown):
    prompt = f"""
{name}

Category: {category}
Website: {website}

Documentation:
{markdown[:5000]}

Write one sentence explaining what this software product does.
Do not describe the API.
Maximum 20 words.
"""

    response = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {
                "role": "system",
                "content": DESCRIPTION_SYSTEM_PROMPT
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0,
    )

    description = response.choices[0].message.content.strip()
    return " ".join(description.split())[:200]


def extract_research(name, website, category, markdown):
    return _extract_research(name, website, category, markdown, retry=False)


def extract_research_retry(name, website, category, markdown):
    return _extract_research(name, website, category, markdown, retry=True)


def _extract_research(name, website, category, markdown, retry=False):
    retry_instruction = """

Be stricter on unsupported fields.
Use only explicit evidence from the documentation.
If a field is not clearly supported, return "Unknown".
Do not change the Known Category.
""" if retry else ""

    prompt = USER_PROMPT.format(
        name=name,
        category=category,
        website=website,
        documentation=markdown[:6000]
    )

    prompt = f"{prompt}{retry_instruction}"

    response = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {
                "role": "system",
                "content": SYSTEM_PROMPT
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0,
        response_format={"type": "json_object"}
    )

    output = response.choices[0].message.content
    data = json.loads(output)

    if not data.get("description") or data.get("description") in {"", "Unknown", f"{name} API", f"{name} API documentation"}:
        data["description"] = describe_app(name, category, website, markdown)

    if not data.get("api_scope") or data.get("api_scope") in {"", "Unknown"}:
        fallback_scope = estimate_api_scope(markdown)
        if fallback_scope != "Unknown":
            data["api_scope"] = fallback_scope

    data["name"] = name

    required_fields = [
        "description",
        "auth_method",
        "self_serve",
        "credential_requirement",
        "api_type",
        "api_scope",
        "mcp_support",
        "buildability",
        "blocker",
        "evidence_url",
    ]

    filled = sum(
        1
        for field_name in required_fields
        if data.get(field_name) not in {"", "Unknown", None}
    )

    confidence = int((filled / len(required_fields)) * 100)
    unknown_count = len(required_fields) - filled
    confidence -= unknown_count * 3
    if retry:
        confidence -= 5

    data["confidence"] = max(0, min(confidence, 95))
    research = AppResearch(**data)

    print("\n================ GROQ OUTPUT ================\n")
    print(research.model_dump_json(indent=2))

    return research