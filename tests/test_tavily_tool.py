import sys
import io

# Ensure UTF-8 output in Windows terminal
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

from Multi_Agent_TourAI.tools.tavily_tool import tavily_search


def test_tavily_search():
    """Test Tavily web search tool response format and execution."""
    result = tavily_search("Top attractions and hotels in Colombo Sri Lanka")
    assert isinstance(result, str)
    assert len(result) > 0
    print("✓ test_tavily_search passed")


if __name__ == "__main__":
    print("=" * 60)
    print("Running tests for tavily_tool.py")
    print("=" * 60)
    test_tavily_search()
    print("=" * 60)
    print("All tavily_tool tests passed successfully!")
    print("=" * 60)
