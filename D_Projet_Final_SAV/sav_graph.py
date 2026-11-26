from __future__ import annotations

import json
import os
from collections.abc import Awaitable, Callable
from typing import Any, TypedDict

from dotenv import load_dotenv
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.graph import END, START, StateGraph

from D_Projet_Final_SAV.routing import RoutingResult, route_request
from D_Projet_Final_SAV.warranty import consulter_garantie

load_dotenv()

DocumentationRunner = Callable[
    [str, str | None], Awaitable[dict[str, Any] | str | list[dict[str, Any]]]
]


class SAVState(TypedDict, total=False):
    request: str
    category: str
    agent_name: str
    serial_number: str | None
    image_reference: str | None
    answer: str
    sources: list[dict[str, Any]]


async def _call_remote_rag(
    query: str, image_reference: str | None
) -> dict[str, Any] | str | list[dict[str, Any]]:
    url = os.getenv("RAG_MCP_URL", "http://127.0.0.1:8000/mcp")
    client = MultiServerMCPClient(
        {
            "sav_rag": {
                "transport": "streamable_http",
                "url": url,
            }
        }
    )
    tools = await client.get_tools()
    rag_tool = next(
        (tool for tool in tools if tool.name.endswith("rag_multimodal")),
        None,
    )
    if rag_tool is None:
        raise RuntimeError(f"No rag_multimodal tool is exposed by {url}.")
    return await rag_tool.ainvoke(
        {"query": query, "image_reference": image_reference}
    )


def _decode_rag_result(
    result: dict[str, Any] | str | list[dict[str, Any]],
) -> dict[str, Any]:
    if isinstance(result, dict):
        return result
    if isinstance(result, list):
        text_blocks = [
            item["text"]
            for item in result
            if item.get("type") == "text" and isinstance(item.get("text"), str)
        ]
        if not text_blocks:
            raise ValueError("The remote rag_multimodal tool returned no text result.")
        result = "\n".join(text_blocks)
    try:
        parsed = json.loads(result)
    except json.JSONDecodeError:
        return {"answer": result, "sources": []}
    if isinstance(parsed, dict):
        return parsed
    raise ValueError("The remote rag_multimodal tool returned an invalid response.")


def build_graph(
    documentation_runner: DocumentationRunner | None = None,
):
    async def agent_documentaire(state: SAVState) -> dict[str, Any]:
        runner = documentation_runner or _call_remote_rag
        result = await runner(
            state["request"], state.get("image_reference")
        )
        decoded = _decode_rag_result(result)
        return {
            "answer": str(decoded.get("answer", "")),
            "sources": decoded.get("sources", []),
        }

    def agent_garantie(state: SAVState) -> dict[str, Any]:
        if not state.get("serial_number"):
            return {
                "answer": (
                    "Veuillez fournir le numero de serie pour consulter la garantie."
                ),
                "sources": [],
            }
        raw_result = consulter_garantie.invoke(
            {"serial_number": state["serial_number"]}
        )
        result = json.loads(raw_result)
        status = result["status"]
        if result.get("record_kind") == "DEMO_ONLY":
            answer = (
                "Donnee fictive de demonstration, ne pas utiliser pour une "
                f"decision reelle : statut={status}, fin={result['warranty_end']}."
            )
        elif status == "not_found":
            answer = result["message"]
        else:
            answer = (
                f"Statut de garantie : {status}. Fin de couverture : "
                f"{result['warranty_end']}."
            )
        return {"answer": answer, "sources": [{"registry": "local_read_only"}]}

    def orchestrator(state: SAVState) -> dict[str, Any]:
        routing: RoutingResult = route_request(state["request"])
        return dict(routing)

    builder = StateGraph(SAVState)
    builder.add_node("orchestrator", orchestrator)
    builder.add_node("agent_documentaire", agent_documentaire)
    builder.add_node("agent_garantie", agent_garantie)
    builder.add_edge(START, "orchestrator")
    builder.add_conditional_edges(
        "orchestrator",
        lambda state: state["category"],
        {
            "documentation": "agent_documentaire",
            "garantie": "agent_garantie",
        },
    )
    builder.add_edge("agent_documentaire", END)
    builder.add_edge("agent_garantie", END)
    return builder.compile()


graph = build_graph()
