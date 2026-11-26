"""A minimal StateGraph example with two sequential nodes."""

from __future__ import annotations

from typing import TypedDict

from langgraph.graph import END, START, StateGraph


class LessonState(TypedDict):
    topic: str
    steps: list[str]


def receive_topic(state: LessonState) -> dict[str, list[str]]:
    return {"steps": [f"Requete recue: {state['topic']}"]}


def prepare_summary(state: LessonState) -> dict[str, list[str]]:
    return {"steps": [*state["steps"], "Resume prepare par un noeud du graphe."]}


builder = StateGraph(LessonState)
builder.add_node("receive_topic", receive_topic)
builder.add_node("prepare_summary", prepare_summary)
builder.add_edge(START, "receive_topic")
builder.add_edge("receive_topic", "prepare_summary")
builder.add_edge("prepare_summary", END)
graph = builder.compile()


if __name__ == "__main__":
    print(graph.invoke({"topic": "Bases de LangGraph", "steps": []}))
