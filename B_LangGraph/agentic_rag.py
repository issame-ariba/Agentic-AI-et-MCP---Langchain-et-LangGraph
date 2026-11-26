from __future__ import annotations

from typing import cast

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, SystemMessage
from langchain_core.tools import tool
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode

from common.llm import create_chat_model
from common.manual_search import search_manuals


@tool
def rechercher_dans_les_manuels(
    question: str, image_reference: str | None = None
) -> str:
    """Recherche des passages et figures des manuels avec leurs sources."""
    result = search_manuals(question, image_reference=image_reference)
    if not result["sources_found"]:
        return "Aucune source pertinente n'a ete trouvee dans le corpus."
    return str(result)


tools = [rechercher_dans_les_manuels]
tool_node = ToolNode(tools)


def build_graph(
    model: BaseChatModel | None = None,
    checkpointer: InMemorySaver | None = None,
):
    def call_agent(state: MessagesState) -> dict[str, list[AIMessage]]:
        chat_model = model or create_chat_model()
        response = chat_model.bind_tools(tools).invoke(
            [
                SystemMessage(
                    content=(
                        "Tu es un assistant documentaire. Utilise les outils pour "
                        "chercher dans les manuels, cite les sources et n'invente "
                        "pas de faits absents des resultats."
                    )
                ),
                *state["messages"],
            ]
        )
        return {"messages": [cast(AIMessage, response)]}

    def route_after_agent(state: MessagesState) -> str:
        last_message = state["messages"][-1]
        if isinstance(last_message, AIMessage) and last_message.tool_calls:
            return "tools"
        return END

    builder = StateGraph(MessagesState)
    builder.add_node("agent", call_agent)
    builder.add_node("tools", tool_node)
    builder.add_edge(START, "agent")
    builder.add_conditional_edges("agent", route_after_agent)
    builder.add_edge("tools", "agent")
    return builder.compile(checkpointer=checkpointer)


graph = build_graph()
