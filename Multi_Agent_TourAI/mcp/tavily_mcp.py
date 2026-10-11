import os
import certifi
from dotenv import load_dotenv
from langchain_mcp_adapters.client import MultiServerMCPClient

# SSL certificate setup for Windows
os.environ["SSL_CERT_FILE"] = certifi.where()
os.environ["REQUESTS_CA_BUNDLE"] = certifi.where()

load_dotenv()

TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

# Remote Tavily MCP Server Client
client = MultiServerMCPClient(
    {
        "tavily-remote-mcp": {
            "transport": "http",
            "url": f"https://mcp.tavily.com/mcp/?tavilyApiKey={TAVILY_API_KEY}",
        }
    }
)

# Tool Cache: stores the tavily_search tool instance
tavily_search_tool = None


async def get_all_tools():
    """Prints all available tools from Tavily MCP in the terminal."""
    tools = await client.get_tools()
    print("\nAvailable Tavily MCP Tools:")
    for tool in tools:
        print(f"- {tool.name}")
    return tools


async def get_tavily_search_tool():
    """Fetches and caches the 'tavily_search' tool to avoid repeated network calls."""
    global tavily_search_tool
    if tavily_search_tool is not None:
        return tavily_search_tool

    tools = await client.get_tools()
    tavily_search_tool = next(
        tool for tool in tools if tool.name == "tavily_search"
    )
    return tavily_search_tool


async def tavily_mcp_search(query: str) -> str:
    """
    Invokes the Tavily MCP search tool with the given query
    and returns the search results as clean text.
    """
    tool = await get_tavily_search_tool()
    
    # Execute search asynchronously
    raw_result = await tool.ainvoke({"query": query})

    # Extract text from the MCP response content blocks
    if isinstance(raw_result, list) and len(raw_result) > 0 and isinstance(raw_result[0], dict):
        return raw_result[0].get("text", str(raw_result))

    return str(raw_result)
