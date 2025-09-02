import asyncio

import mcp.types as types
from mcp.server.lowlevel import Server, NotificationOptions
from mcp.server.models import InitializationOptions
import mcp.server.stdio

from registry import build_registry
from executor import call_tool

REGISTRY = build_registry("config/github.yaml")
server = Server("sdk2mcp")


def _schema():
    return {"type": "object"}


@server.list_tools()
async def list_tools():
    return [
        types.Tool(
            name=ms.tool_name,
            inputSchema=_schema(),
        )
        for ms in REGISTRY.values()
    ]


@server.call_tool()
async def call_tool_handler(name: str, arguments):
    ms = REGISTRY.get(name)
    if not ms:
        raise ValueError(f"Unknown tool: {name}")
    return call_tool(ms, arguments or {})


async def main():
    async with mcp.server.stdio.stdio_server() as (read, write):
        await server.run(
            read,
            write,
            InitializationOptions(
                server_name="sdk2mcp",
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )


if __name__ == "__main__":
    asyncio.run(main())
