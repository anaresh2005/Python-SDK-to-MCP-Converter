# agent_demo.py
import asyncio
import os

from agents import Agent, Runner
from agents.mcp.server import MCPServerStdio


async def main():
    mcp_server = MCPServerStdio(
        params={
            "command": "python",
            "args": ["mcp_server.py"],
            "env": {
                "GITHUB_TOKEN": os.environ.get("GITHUB_TOKEN", ""),
            },
        },
    )
    await mcp_server.connect()
    try:
        agent = Agent(
            name="sdk2mcp",
            instructions=(
                "You are a helpful assistant. When the user asks for GitHub data, "
                "use the MCP tools from the sdk2mcp server. Return concise JSON when appropriate."
            ),
            model="o4-mini",
            mcp_servers=[mcp_server],
        )

        runner = Runner()
        prompt = "Get GitHub user 'octocat' using gh_get_user and return login, id, public_repos."
        result = await runner.run(agent, prompt)
    finally:
        await mcp_server.cleanup()
    print("\n=== FINAL OUTPUT ===")
    print(result.final_output)


if __name__ == "__main__":
    asyncio.run(main())
