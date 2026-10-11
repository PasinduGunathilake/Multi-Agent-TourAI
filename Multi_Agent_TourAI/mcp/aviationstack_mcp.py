import os
import certifi
from dotenv import load_dotenv
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_mcp_adapters.tools import load_mcp_tools

# SSL certificate setup for Windows
os.environ["SSL_CERT_FILE"] = certifi.where()
os.environ["REQUESTS_CA_BUNDLE"] = certifi.where()

load_dotenv()

AVIATION_STACK_API_KEY = os.getenv("AVIATIONSTACK_API_KEY")

# Local Aviationstack MCP Server Client
client = MultiServerMCPClient(
    {
        "Aviationstack MCP": {
            "transport": "stdio",
            "command": "uvx",
            "args": ["aviationstack-mcp"],
            "env": {
                "AVIATION_STACK_API_KEY": AVIATION_STACK_API_KEY
            }
        }
    }
)

# Tool Cache Dictionary: maps tool name to tool object
flight_tools = {}


async def get_all_tools():
    """Prints all available tools in the terminal and returns the list."""
    tools = await client.get_tools()
    print("\nAvailable Aviationstack MCP Tools:")
    for tool in tools:
        print(f"- {tool.name}")
    return tools


async def init_flight_tools():
    """Loads tools once and caches them in a dictionary to avoid repeated fetching."""
    global flight_tools
    if flight_tools:
        return flight_tools

    tools = await client.get_tools()
    flight_tools = {t.name: t for t in tools}
    return flight_tools


async def aviationstack_mcp_search(tool_name: str, tool_args: dict = None):
    """
    Invokes a specific Aviationstack MCP tool by name with the provided arguments.
    """
    tools_dict = await init_flight_tools()

    if tool_name not in tools_dict:
        raise ValueError(
            f"Tool '{tool_name}' not found. Available tools: {list(tools_dict.keys())}"
        )

    tool = tools_dict[tool_name]
    # Asynchronously invoke the tool with arguments
    result = await tool.ainvoke(tool_args or {})
    return result
