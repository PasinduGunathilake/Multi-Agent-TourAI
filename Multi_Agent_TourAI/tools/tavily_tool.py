# fetch hotel details
import os
from tavily import TavilyClient
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("TAVILY_API_KEY", "")

client = TavilyClient(api_key=api_key) if api_key else None


def tavily_search(query: str) -> str:
    """Search the web for hotel, travel, and attraction information using Tavily."""
    if not client:
        return "Tavily search unavailable: TAVILY_API_KEY is not configured."

    try:
        response = client.search(
            query=query,
            max_results=5  # return 5 results
        )

        results = []  # store search results in list

        # filter metadata
        for i, r in enumerate(response.get("results", []), 1):
            title = r.get("title", "Unknown")
            url = r.get("url", "")
            snippet = r.get("content", "").strip()
            # keep only the first 300 characters to avoid wall-of-text
            if len(snippet) > 300:
                snippet = snippet[:300].rsplit(" ", 1)[0] + "..."

            results.append(f"{i}. **{title}**\n   {url}\n   {snippet}")

        if not results:
            return f"No results found for query: '{query}'."

        return "\n\n".join(results)
    except Exception as e:
        return f"Error executing Tavily search: {e}"