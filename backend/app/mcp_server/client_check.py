"""Small MCP client smoke test for the ResearchX MCP server (SDK v1.x)."""
import asyncio
import os
import httpx
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

async def main() -> None:
    url = os.getenv("RESEARCHX_MCP_URL", "http://127.0.0.1:8002/mcp")
    token = os.getenv("MCP_API_TOKEN", "")
    if not token:
        raise RuntimeError("Set MCP_API_TOKEN before running the MCP client check.")

    async with httpx.AsyncClient(headers={"Authorization": f"Bearer {token}"}) as http_client:
        async with streamable_http_client(url, http_client=http_client) as (read, write, _):
            async with ClientSession(read, write) as session:
                await session.initialize()
                tools = await session.list_tools()
                resources = await session.list_resources()
                prompts = await session.list_prompts()
                print("Tools:", [item.name for item in tools.tools])
                print("Resources:", [str(item.uri) for item in resources.resources])
                print("Prompts:", [item.name for item in prompts.prompts])
                result = await session.call_tool("search_research_papers", {"query": ""})
                print("Paper search result:", result.structuredContent or result.content)


if __name__ == "__main__":
    asyncio.run(main())
