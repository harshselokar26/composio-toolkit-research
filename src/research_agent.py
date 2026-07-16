from firecrawl import FirecrawlApp

from config import FIRECRAWL_API_KEY
from llm import extract_research
from verifier import verify_research

firecrawl = FirecrawlApp(api_key=FIRECRAWL_API_KEY)


def _normalize_category(category):
    normalized = str(category).strip()
    if normalized.lower() in {"sales", "crm", "crm and sales"}:
        return "CRM and Sales"
    return normalized


def research_app(name, website, category):
    category = _normalize_category(category)

    print("=" * 70)
    print(f"Researching {name}")
    print("=" * 70)

    try:

        search = firecrawl.search(
            query=f"""
{name} developer documentation API overview getting started authentication
"""
        )

        if not search.web:
            print("No documentation found.")
            return None

        preferred = []

        for page in search.web:
            url = page.url if hasattr(page, "url") else page["url"]

            if any(keyword in url.lower() for keyword in [
                "developers",
                "developer",
                "docs",
                "api",
                "reference"
            ]):
                preferred.append(page)

        pages = (preferred or search.web)[:3]

        combined_markdown = ""
        evidence_urls = []

        for page in pages:
            url = page.url if hasattr(page, "url") else page["url"]

            evidence_urls.append(url)

            print(f"\nScraping: {url}")

            try:
                scraped = firecrawl.scrape_url(
                    url=url,
                    formats=["markdown"]
                )

                markdown = (
                    scraped["markdown"]
                    if isinstance(scraped, dict)
                    else scraped.markdown
                )

                combined_markdown += f"\n\n--- PAGE: {url} ---\n\n"
                combined_markdown += markdown[:1500]

            except Exception as e:
                print(f"Failed to scrape {url}")
                print(e)

        research = extract_research(name, website, category, combined_markdown)
        verification = verify_research(
            name,
            category,
            combined_markdown,
            research.model_dump()
        )

        print(verification)

        if verification.get("corrected_json"):
            research = research.model_copy(update=verification["corrected_json"])

        research.manual_review = verification.get("manual_review", False)
        research.issues = verification.get("issues", [])

        research.evidence_url = ", ".join(evidence_urls)

        return research.model_dump()

    except Exception as e:
        print(f"\nError researching {name}")
        print(e)
        return None