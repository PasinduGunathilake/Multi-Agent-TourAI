import asyncio
import os
from typing import Optional, List, Dict, Any
import certifi
from dotenv import load_dotenv
from langchain_mcp_adapters.client import MultiServerMCPClient
from Multi_Agent_TourAI.utils import get_logger

# SSL certificate setup for Windows
os.environ["SSL_CERT_FILE"] = certifi.where()
os.environ["REQUESTS_CA_BUNDLE"] = certifi.where()

load_dotenv()
logger = get_logger(__name__)

DEFAULT_TIMEOUT = 25.0


def redact_api_key(key: Optional[str]) -> str:
    """Masks an API key for safe logging, displaying only first 4 and last 4 characters."""
    if not key or not str(key).strip():
        return "[NOT SET]"
    key_str = str(key).strip()
    if len(key_str) <= 8:
        return "***"
    return f"{key_str[:4]}...{key_str[-4:]}"


def get_aviationstack_api_key() -> str:
    """
    Validates and returns the configured Aviationstack API key.
    Supports both AVIATIONSTACK_API_KEY and AVIATION_STACK_API_KEY env variables.
    """
    key = os.getenv("AVIATIONSTACK_API_KEY") or os.getenv("AVIATION_STACK_API_KEY")
    if not key or not key.strip():
        raise ValueError(
            "AVIATIONSTACK_API_KEY is missing or empty. Please set AVIATIONSTACK_API_KEY in your environment."
        )
    return key.strip()


# Internal client & tool caches
_mcp_client: Optional[MultiServerMCPClient] = None
flight_tools: Dict[str, Any] = {}
_init_lock: Optional[asyncio.Lock] = None


def _get_init_lock() -> asyncio.Lock:
    """Returns or creates an asyncio.Lock tied to the active event loop."""
    global _init_lock
    if _init_lock is None:
        _init_lock = asyncio.Lock()
    return _init_lock


def get_mcp_client() -> MultiServerMCPClient:
    """
    Initializes or returns the cached MultiServerMCPClient for Aviationstack MCP (stdio transport).
    Validates presence of API key and protects credentials from plain-text logging.
    """
    global _mcp_client
    if _mcp_client is not None:
        return _mcp_client

    api_key = get_aviationstack_api_key()
    logger.info(f"Connecting to Aviationstack Local MCP Server via stdio (Key: {redact_api_key(api_key)})")

    _mcp_client = MultiServerMCPClient(
        {
            "Aviationstack MCP": {
                "transport": "stdio",
                "command": "uvx",
                "args": ["aviationstack-mcp"],
                "env": {
                    "AVIATION_STACK_API_KEY": api_key,
                    "AVIATIONSTACK_API_KEY": api_key,
                },
            }
        }
    )
    return _mcp_client


def reset_aviationstack_cache():
    """Resets internal client and tool caches (useful for testing and reconfiguration)."""
    global _mcp_client, flight_tools, _init_lock
    _mcp_client = None
    flight_tools = {}
    _init_lock = None


# Module-level client reference for backward compatibility
client = None


async def get_all_tools() -> list:
    """
    Fetches and returns all available tools from the Aviationstack MCP server.
    Logs discovered tool names and safely handles process/connection errors.
    """
    mcp_client = get_mcp_client()
    try:
        tools = await asyncio.wait_for(mcp_client.get_tools(), timeout=DEFAULT_TIMEOUT)
    except asyncio.TimeoutError as te:
        logger.error(f"Timeout ({DEFAULT_TIMEOUT}s) fetching tools from Aviationstack MCP")
        raise RuntimeError(f"Aviationstack MCP tool discovery timed out after {DEFAULT_TIMEOUT}s") from te
    except Exception as e:
        logger.error(f"Failed to fetch tools from Aviationstack MCP: {str(e)}")
        raise RuntimeError(f"Aviationstack MCP tool discovery failed: {str(e)}") from e

    if not tools:
        logger.warning("Aviationstack MCP returned an empty tool collection.")
        return []

    tool_names = [getattr(t, "name", "unknown") for t in tools]
    logger.info(f"Available Aviationstack MCP Tools: {tool_names}")
    return tools


async def init_flight_tools() -> Dict[str, Any]:
    """
    Loads tools once and caches them in a dictionary mapping tool name to tool object.
    Includes concurrent initialization safety via asyncio.Lock.
    """
    global flight_tools
    if flight_tools:
        return flight_tools

    async with _get_init_lock():
        if flight_tools:
            return flight_tools

        tools = await get_all_tools()
        flight_tools = {getattr(t, "name", f"tool_{i}"): t for i, t in enumerate(tools)}
        return flight_tools


def _parse_aviationstack_response(raw_result: Any) -> Any:
    """Extracts text or payload cleanly from MCP response blocks."""
    if raw_result is None:
        return ""
    if isinstance(raw_result, str):
        return raw_result
    if isinstance(raw_result, list) and len(raw_result) > 0:
        first = raw_result[0]
        if isinstance(first, dict) and "text" in first:
            return first["text"]
        if hasattr(first, "text"):
            return getattr(first, "text")
        if hasattr(first, "content"):
            return str(getattr(first, "content"))
        return raw_result
    if isinstance(raw_result, dict) and "text" in raw_result:
        return raw_result["text"]
    if hasattr(raw_result, "content"):
        return str(getattr(raw_result, "content"))
    return raw_result


async def aviationstack_mcp_search(tool_name: str, tool_args: Optional[dict] = None) -> Any:
    """
    Invokes a specific Aviationstack MCP tool by name with the provided arguments.
    Safely handles timeouts, tool resolution, and response parsing.
    """
    if not tool_name or not tool_name.strip():
        raise ValueError("tool_name must be a non-empty string.")

    tool_name = tool_name.strip()
    tools_dict = await init_flight_tools()

    if tool_name not in tools_dict:
        available_tools = list(tools_dict.keys())
        raise ValueError(
            f"Tool '{tool_name}' not found. Available tools: {available_tools}"
        )

    tool = tools_dict[tool_name]

    try:
        raw_result = await asyncio.wait_for(
            tool.ainvoke(tool_args or {}),
            timeout=DEFAULT_TIMEOUT,
        )
    except asyncio.TimeoutError as te:
        logger.error(f"Aviationstack tool '{tool_name}' timed out after {DEFAULT_TIMEOUT}s")
        raise RuntimeError(f"Aviationstack tool '{tool_name}' timed out after {DEFAULT_TIMEOUT}s") from te
    except Exception as e:
        logger.error(f"Aviationstack tool '{tool_name}' execution failed: {str(e)}")
        raise RuntimeError(f"Aviationstack tool '{tool_name}' execution error: {str(e)}") from e

    return _parse_aviationstack_response(raw_result)


__all__ = [
    "client",
    "get_mcp_client",
    "get_all_tools",
    "init_flight_tools",
    "aviationstack_mcp_search",
    "get_aviationstack_api_key",
    "redact_api_key",
    "reset_aviationstack_cache",
]
