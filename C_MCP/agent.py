from __future__ import annotations

import asyncio
import os

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_mcp_adapters.client import MultiServerMCPClient

from common.llm import create_chat_model

load_dotenv()


async def main() -> None:
    client = MultiServerMCPClient(
        {
            "mcp_demo": {
                "transport": "streamable_http",
                "url": os.getenv(
                    "MCP_DEMO_URL", "http://127.0.0.1:24000/mcp"
                ),
            }
        }
    )
    tools = await client.get_tools()
    if not tools:
        raise RuntimeError("The MCP server exposed no tools.")

    agent = create_agent(
        model=create_chat_model(),
        tools=tools,
        system_prompt=(
            "Tu es un agent de demonstration MCP. Utilise les outils disponibles "
            "pour repondre, et signale les donnees de demonstration."
        ),
    )
    print("Agent MCP pret (tapez q pour quitter).")
    while True:
        question = input("\nQuestion> ").strip()
        if question.casefold() in {"q", "quit", "exit"}:
            break
        if question:
            result = await agent.ainvoke(
                {"messages": [{"role": "user", "content": question}]}
            )
            print(result["messages"][-1].content)


if __name__ == "__main__":
    asyncio.run(main())
