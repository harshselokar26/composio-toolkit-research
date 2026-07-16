import json

from llm import GROQ_MODEL, client

ALLOWED_VALUES = {
    "self_serve": {"Self Serve", "Paid Plan", "Enterprise", "Partner Required", "Admin Approval", "Unknown"},
    "credential_requirement": {"Secret API Key", "Internal Integration Token", "Programmatic API Key", "Service Account Key", "Developer account + Connected App + OAuth", "API key", "API token", "OAuth credentials", "Access token", "Personal access token", "Unknown"},
    "api_type": {"REST", "GraphQL", "SOAP", "SDK", "Unknown"},
    "api_scope": {"Small", "Medium", "Large", "Very Large", "Unknown"},
    "mcp_support": {"Yes", "No", "Unknown"},
    "buildability": {"Yes", "Partially", "No", "Unknown"},
    "blocker": {"None", "Unknown"},
}


def _normalize_value(field_name, value):
    if value is None:
        return "Unknown"

    text = str(value).strip()
    lower_text = text.lower()

    if field_name == "self_serve":
        if lower_text in {"true", "yes", "self serve", "self-serve"}:
            return "Self Serve"
        if lower_text in {"false", "no"}:
            return "Unknown"

    if field_name == "buildability":
        if lower_text in {"yes", "high", "highly buildable", "buildable"}:
            return "Yes"
        if lower_text in {"partially", "partial", "maybe", "somewhat"}:
            return "Partially"
        if lower_text in {"no", "not buildable"}:
            return "No"

    if field_name == "mcp_support":
        if lower_text in {"true", "yes"}:
            return "Yes"
        if lower_text in {"false", "no"}:
            return "No"

    if field_name == "api_scope":
        if "very large" in lower_text:
            return "Very Large"
        if "large" in lower_text:
            return "Large"
        if "medium" in lower_text:
            return "Medium"
        if "small" in lower_text:
            return "Small"

    if field_name == "credential_requirement":
        if not text or lower_text in {"unknown", "n/a", "na"}:
            return "Unknown"
        if "developer account" in lower_text and "oauth" in lower_text:
            return "Developer account + Connected App + OAuth"
        if "personal access token" in lower_text:
            return "Personal access token"
        if "internal integration token" in lower_text:
            return "Internal Integration Token"
        if "programmatic api" in lower_text or "programmatic key" in lower_text:
            return "Programmatic API Key"
        if "secret api key" in lower_text or "secret key" in lower_text:
            return "Secret API Key"
        if "service account" in lower_text:
            return "Service Account Key"
        return text

    if field_name == "auth_method":
        if "oauth" in lower_text:
            return "OAuth 2.0"
        if "api key" in lower_text:
            return "API key"
        if "bearer" in lower_text:
            return "Bearer token"
        if "basic" in lower_text:
            return "Basic auth"
        if "personal access token" in lower_text:
            return "Personal access token"

    if field_name == "blocker":
        if lower_text in {"", "none", "unknown", "n/a", "na"}:
            return "None"

    if field_name in ALLOWED_VALUES and text not in ALLOWED_VALUES[field_name]:
        return "Unknown"

    return text


def _sanitize_research(extracted_json, category):
    corrected = dict(extracted_json)
    corrected["category"] = category

    for field_name in ALLOWED_VALUES:
        corrected[field_name] = _normalize_value(field_name, corrected.get(field_name))

    try:
        corrected["confidence"] = int(corrected.get("confidence", 0))
    except (TypeError, ValueError):
        corrected["confidence"] = 0

    return corrected


def _collect_issues(extracted_json, category, markdown):
    issues = []

    if extracted_json.get("category") != category:
        issues.append(f"Category must match known category: {category}")

    for field_name, allowed_values in ALLOWED_VALUES.items():
        if extracted_json.get(field_name) not in allowed_values:
            issues.append(f"{field_name} must be one of: {', '.join(sorted(allowed_values))}")

    if extracted_json.get("blocker") not in {"None", "Unknown"}:
        issues.append("blocker must be None unless the docs clearly name a blocker")

    if extracted_json.get("mcp_support") == "Yes":
        doc_text = markdown.lower()
        if "mcp" not in doc_text and "model context protocol" not in doc_text:
            issues.append("mcp_support should be Unknown unless the docs explicitly mention MCP")

    return issues


def verify_research(name, category, markdown, extracted_json):
    corrected = _sanitize_research(extracted_json, category)
    issues = _collect_issues(extracted_json, category, markdown)

    confidence = int(corrected.get("confidence", 0))
    if issues:
        confidence = max(0, confidence - min(25, 5 * len(issues)))
    corrected["confidence"] = confidence

    return {
        "valid": not issues,
        "manual_review": bool(issues),
        "issues": issues,
        "corrected_json": corrected,
    }