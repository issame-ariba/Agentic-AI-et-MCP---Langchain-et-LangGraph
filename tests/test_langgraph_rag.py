from __future__ import annotations

from typing import Any

from langchain_core.language_models.fake_chat_models import FakeMessagesListChatModel
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

from B_LangGraph.agentic_rag import build_graph


class ToolCallingFakeModel(FakeMessagesListChatModel):
    def bind_tools(self, _tools: list[Any], **_kwargs: Any):
        return self


def test_agentic_rag_calls_search_tool_then_returns_final_answer():
    model = ToolCallingFakeModel(
        responses=[
            AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "rechercher_dans_les_manuels",
                        "args": {"question": "voyant"},
                        "id": "search_1",
                        "type": "tool_call",
                    }
                ],
            ),
            AIMessage(content="Je ne trouve pas de source pour cette question."),
        ]
    )
    graph = build_graph(model=model)

    result = graph.invoke(
        {"messages": [HumanMessage(content="Que signifie ce voyant ?")]},
        config={"configurable": {"thread_id": "rag-test"}},
    )

    assert any(isinstance(message, ToolMessage) for message in result["messages"])
    assert result["messages"][-1].content == (
        "Je ne trouve pas de source pour cette question."
    )
