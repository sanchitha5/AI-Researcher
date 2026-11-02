"""
Tavily web search service.

A small, explicit function the LangGraph agent calls when it decides
it needs to search the live web. Keeping this in its own file (and
its own function) means it's easy for workshop students to find and
understand exactly how web search works — no magic.
"""

from functools import lru_cache

from tavily import TavilyClient

from app.config import settings


class TavilyNotConfiguredError(Exception):
    """Raised when web search is attempted without an API key set."""


class TavilySearchError(Exception):
    """Raised when the Tavily API call itself fails."""


@lru_cache(maxsize=1)
def _get_client() -> TavilyClient:
    if not settings.tavily_configured:
        raise TavilyNotConfiguredError(
            "TAVILY_API_KEY is not set. Add it to backend/.env to enable web search."
        )
    return TavilyClient(api_key=settings.TAVILY_API_KEY)


def web_search(query: str, max_results: int = 5) -> list[dict]:
    """
    Search the live web via Tavily.

    Returns a list of dicts like:
        {
            "title": "...",
            "url": "https://...",
            "content": "...snippet...",
            "source": "example.com",
        }
    """
    client = _get_client()

    try:
        response = client.search(
            query=query,
            search_depth="basic",
            max_results=max_results,
            include_answer=False,
        )
    except Exception as exc:  # noqa: BLE001 - normalized into our own error type
        raise TavilySearchError(f"Tavily web search failed: {exc}") from exc

    results = []
    for item in response.get("results", []):
        url = item.get("url", "")
        domain = url.split("//")[-1].split("/")[0].replace("www.", "") if url else "web"
        results.append(
            {
                "title": item.get("title", "Untitled"),
                "url": url,
                "content": item.get("content", "").strip(),
                "source": domain,
            }
        )
    return results
