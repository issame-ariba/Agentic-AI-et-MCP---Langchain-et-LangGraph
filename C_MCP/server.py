from __future__ import annotations

import os

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

load_dotenv()
mcp = FastMCP(
    "agentic-ai-demo",
    host=os.getenv("MCP_DEMO_HOST", "127.0.0.1"),
    port=24000,
)

DEMO_EMPLOYEES = {
    "sami demo": {"department": "Support", "record_kind": "DEMO_ONLY"},
    "amina demo": {"department": "Documentation", "record_kind": "DEMO_ONLY"},
}


@mcp.tool()
def get_employee_infos(name: str) -> dict[str, str]:
    """Return a fictitious employee demo record by name."""
    record = DEMO_EMPLOYEES.get(name.strip().casefold())
    if record is None:
        return {
            "name": name,
            "found": "false",
            "message": "No demo employee record matches this name.",
        }
    return {"name": name, "found": "true", **record}


@mcp.tool()
def search(query: str) -> str:
    """Search the web with Tavily for the requested topic."""
    if not os.getenv("TAVILY_API_KEY"):
        raise RuntimeError("TAVILY_API_KEY is required to use the search tool.")
    from langchain_tavily import TavilySearch

    return str(TavilySearch(max_results=5).invoke({"query": query}))


if __name__ == "__main__":
    mcp.run(transport="streamable-http")
