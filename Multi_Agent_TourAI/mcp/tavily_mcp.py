import asyncio
import os
from typing import Optional, List, Any
import certifi
from dotenv import load_dotenv
from langchain_mcp_adapters.client import MultiServerMCPClient
from Multi_Agent_TourAI.utils import get_logger

# SSL certificate setup for Windows
os.environ["SSL_CERT_FILE"] = certifi.where()
os.environ["REQUESTS_CA_BUNDLE"] = certifi.where()

load_dotenv()
logger = get_logger(__name__)

DEFAULT_TIMEOUT = 20.0


def redact_api_key(key: Optional[str]) -> str:
    """Masks an API key for safe logging, displaying only first 4 and last 4 characters."""
    if not key or not str(key).strip():
        return "[NOT SET]"
    key_str = str(key).strip()
    if len(key_str) <= 8:
        return "***"
    return f"{key_str[:4]}...{key_str[-4:]}"


def get_tavily_api_key() -> str:
    """Validates and returns the configured Tavily API key."""
    key = os.getenv("TAVILY_API_KEY")
    if not key or not key.strip():
        raise ValueError(
            "TAVILY_API_KEY is missing or empty. Please set TAVILY_API_KEY in your environment."
        )
    return key.strip()


# Internal client cache
_mcp_client: Optional[MultiServerMCPClient] = None
tavily_search_tool: Optional[Any] = None
_init_lock: Optional[asyncio.Lock] = None
_init_loop: Optional[asyncio.AbstractEventLoop] = None


def _get_init_lock() -> asyncio.Lock:
    """Returns or creates an asyncio.Lock tied to the currently active running event loop."""
    global _init_lock, _init_loop
    try:
        current_loop = asyncio.get_running_loop()
    except RuntimeError:
        current_loop = None

    if _init_lock is None or _init_loop is not current_loop:
        _init_loop = current_loop
        _init_lock = asyncio.Lock()
    return _init_lock


def get_mcp_client() -> MultiServerMCPClient:
    """
    Initializes or returns the cached MultiServerMCPClient for Tavily MCP.
    Validates presence of API key and protects credentials from plain-text logging.
    """
    global _mcp_client
    if _mcp_client is not None:
        return _mcp_client

    api_key = get_tavily_api_key()
    logger.info(f"Connecting to Tavily Remote MCP endpoint (Key: {redact_api_key(api_key)})")

    # Uses official remote Tavily MCP URL with credentials passed securely
    _mcp_client = MultiServerMCPClient(
        {
            "tavily-remote-mcp": {
                "transport": "http",
                "url": f"https://mcp.tavily.com/mcp/?tavilyApiKey={api_key}",
            }
        }
    )
    return _mcp_client


def reset_tavily_cache():
    """Resets internal client and tool caches (useful for testing and reconfiguration)."""
    global _mcp_client, tavily_search_tool, _init_lock, _init_loop
    _mcp_client = None
    tavily_search_tool = None
    _init_lock = None
    _init_loop = None


# Module-level client reference for backward compatibility
client = None


async def get_all_tools() -> list:
    """
    Fetches and returns all available tools from the Tavily MCP server.
    Safely handles connection errors and logs sanitized metadata.
    """
    mcp_client = get_mcp_client()
    try:
        tools = await asyncio.wait_for(mcp_client.get_tools(), timeout=DEFAULT_TIMEOUT)
    except asyncio.TimeoutError as te:
        logger.error(f"Timeout ({DEFAULT_TIMEOUT}s) fetching tools from Tavily MCP")
        raise RuntimeError(f"Tavily MCP tool discovery timed out after {DEFAULT_TIMEOUT}s") from te
    except Exception as e:
        logger.error(f"Failed to fetch tools from Tavily MCP: {str(e)}")
        raise RuntimeError(f"Tavily MCP tool discovery failed: {str(e)}") from e

    if not tools:
        logger.warning("Tavily MCP returned an empty tool collection.")
        return []

    tool_names = [getattr(t, "name", "unknown") for t in tools]
    logger.info(f"Available Tavily MCP Tools: {tool_names}")
    return tools


def select_tavily_search_tool(tools: list) -> Any:
    """
    Validates tool collection and extracts 'tavily_search'.
    Replaces unsafe next() lookup with explicit validation and descriptive exceptions.
    """
    if not tools:
        raise RuntimeError(
            "No tools were returned by the Tavily MCP server. Verify API key and remote server status."
        )

    tool = next((t for t in tools if getattr(t, "name", None) == "tavily_search"), None)
    if tool is None:
        available_names = [getattr(t, "name", "unknown") for t in tools]
        raise RuntimeError(
            f"Expected tool 'tavily_search' was not found in Tavily MCP server response. "
            f"Available tools: {available_names}"
        )
    return tool


async def get_tavily_search_tool():
    """
    Fetches and caches the 'tavily_search' tool from Tavily MCP with concurrent initialization safety.
    """
    global tavily_search_tool
    if tavily_search_tool is not None:
        return tavily_search_tool

    async with _get_init_lock():
        if tavily_search_tool is not None:
            return tavily_search_tool

        tools = await get_all_tools()
        tool = select_tavily_search_tool(tools)
        tavily_search_tool = tool
        return tavily_search_tool


def _parse_tavily_response(raw_result: Any) -> str:
    """Extracts text content cleanly from single or multi-part MCP response shapes."""
    if raw_result is None:
        return ""
    if isinstance(raw_result, str):
        return raw_result
    if isinstance(raw_result, list) and len(raw_result) > 0:
        extracted = []
        for block in raw_result:
            if isinstance(block, dict) and "text" in block:
                extracted.append(block["text"])
            elif hasattr(block, "text"):
                extracted.append(getattr(block, "text"))
            elif hasattr(block, "content"):
                extracted.append(str(getattr(block, "content")))
            elif isinstance(block, str):
                extracted.append(block)
            elif isinstance(block, dict):
                extracted.append(str(block.get("content", block)))
            else:
                extracted.append(str(block))
        return "\n".join(extracted) if extracted else str(raw_result)
    if isinstance(raw_result, dict):
        return raw_result.get("text", raw_result.get("content", str(raw_result)))
    if hasattr(raw_result, "content"):
        return str(getattr(raw_result, "content"))
    return str(raw_result)


async def tavily_mcp_search(query: str) -> str:
    """
    Invokes the Tavily MCP search tool with the given query
    and returns search results as clean text.
    """
    if not query or not query.strip():
        return "No search query provided."

    tool = await get_tavily_search_tool()

    try:
        raw_result = await asyncio.wait_for(
            tool.ainvoke({"query": query.strip()}),
            timeout=DEFAULT_TIMEOUT,
        )
    except asyncio.TimeoutError as te:
        logger.error(f"Tavily search execution timed out after {DEFAULT_TIMEOUT}s")
        raise RuntimeError(f"Tavily search execution timed out after {DEFAULT_TIMEOUT}s") from te
    except Exception as e:
        logger.error(f"Tavily search execution failed: {str(e)}")
        raise RuntimeError(f"Tavily search execution error: {str(e)}") from e

    return _parse_tavily_response(raw_result)


__all__ = [
    "client",
    "get_mcp_client",
    "get_all_tools",
    "get_tavily_search_tool",
    "select_tavily_search_tool",
    "tavily_mcp_search",
    "get_tavily_api_key",
    "redact_api_key",
    "reset_tavily_cache",
]
