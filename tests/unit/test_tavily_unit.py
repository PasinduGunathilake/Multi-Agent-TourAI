import sys
import io
from unittest.mock import MagicMock

# Ensure UTF-8 output in Windows terminal
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

import Multi_Agent_TourAI.tools.tavily_tool as tavily_module


def test_tavily_search_snippet_truncation():
    """Unit test: verifies that snippets exceeding 300 chars are truncated at the word boundary with '...'"""
    # Create mock TavilyClient
    mock_client = MagicMock()
    mock_client.search.return_value = {
        "results": [
            {
                "title": "Grand Hotel Colombo",
                "url": "https://example.com/grand-hotel",
                "content": "A " * 200,  # 400 characters long text
            }
        ]
    }

    original_client = tavily_module.client
    try:
        tavily_module.client = mock_client
        result = tavily_module.tavily_search("hotels in colombo")
        assert "Grand Hotel Colombo" in result
        assert "https://example.com/grand-hotel" in result
        assert result.endswith("...")
        print("✓ [Unit] test_tavily_search_snippet_truncation passed")
    finally:
        tavily_module.client = original_client


def test_tavily_search_missing_client():
    """Unit test: verifies graceful error message when client is None (no API key)."""
    original_client = tavily_module.client
    try:
        tavily_module.client = None
        result = tavily_module.tavily_search("hotels")
        assert "Tavily search unavailable: TAVILY_API_KEY is not configured." in result
        print("✓ [Unit] test_tavily_search_missing_client passed")
    finally:
        tavily_module.client = original_client


def test_tavily_search_empty_results():
    """Unit test: verifies message when search returns 0 results."""
    mock_client = MagicMock()
    mock_client.search.return_value = {"results": []}

    original_client = tavily_module.client
    try:
        tavily_module.client = mock_client
        result = tavily_module.tavily_search("non-existing query")
        assert "No results found for query" in result
        print("✓ [Unit] test_tavily_search_empty_results passed")
    finally:
        tavily_module.client = original_client


if __name__ == "__main__":
    print("=" * 60)
    print("Running Unit Tests: tavily_tool")
    print("=" * 60)
    test_tavily_search_snippet_truncation()
    test_tavily_search_missing_client()
    test_tavily_search_empty_results()
    print("=" * 60)
    print("All tavily_tool unit tests passed successfully!")
    print("=" * 60)
