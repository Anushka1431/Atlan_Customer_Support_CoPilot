# mcp_client.py
import asyncio
from contextlib import AsyncExitStack
from typing import Any, Optional
from mcp import ClientSession
from mcp.client.sse import sse_client

class SupportMCPClient:
    def __init__(self, server_url: str = "http://localhost:8000/sse"):
        self.server_url = server_url
        self.session: Optional[ClientSession] = None
        self.exit_stack = AsyncExitStack()
        self.tools = {}

    async def connect(self):
        self._streams_context = sse_client(url=self.server_url)
        streams = await self._streams_context.__aenter__()
        self._session_context = ClientSession(*streams)
        self.session = await self._session_context.__aenter__()
        await self.session.initialize()

        tools = await self.session.list_tools()
        self.tools = {tool.name: tool for tool in tools.tools}
        print("✅ Connected. Tools:", list(self.tools.keys()))

    async def run_tool(self, tool_name: str, input_dict: dict[str, Any]):
        if not self.session:
            raise RuntimeError("Not connected to MCP session.")
        response = await self.session.call_tool(tool_name, input_dict)
        return response

    async def list_resources(self):
        resources = await self.session.list_resources()
        return resources.resources

    async def cleanup(self):
        if hasattr(self, "_session_context"):
            await self._session_context.__aexit__(None, None, None)
        if hasattr(self, "_streams_context"):
            await self._streams_context.__aexit__(None, None, None)
