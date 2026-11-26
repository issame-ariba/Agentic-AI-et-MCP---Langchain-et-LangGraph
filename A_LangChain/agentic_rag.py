from __future__ import annotations

import json
import uuid

from langchain.agents import create_agent
from langchain_core.tools import tool
from langgraph.checkpoint.memory import InMemorySaver

from common.llm import create_chat_model
from common.manual_search import search_manuals


@tool
def rechercher_dans_les_manuels(
    question: str, image_reference: str | None = None
) -> str:
    """Recherche des passages et des figures source dans le corpus documentaire."""
    return json.dumps(
        search_manuals(question, image_reference=image_reference),
        ensure_ascii=False,
    )


def build_agent(model=None):
    chat_model = model or create_chat_model()
    return create_agent(
        model=chat_model,
        tools=[rechercher_dans_les_manuels],
        checkpointer=InMemorySaver(),
        system_prompt=(
            "Tu es un assistant documentaire. Pour toute question sur un appareil, "
            "appelle rechercher_dans_les_manuels. Reponds uniquement a partir des "
            "sources retournees, cite le manuel et la page, et signale clairement "
            "si aucune source pertinente n'est disponible."
        ),
    )


def main() -> None:
    agent = build_agent()
    thread_id = str(uuid.uuid4())
    print("Assistant RAG LangChain (quitter avec q).")
    while True:
        question = input("\nQuestion> ").strip()
        if question.casefold() in {"q", "quit", "exit"}:
            break
        if not question:
            continue
        result = agent.invoke(
            {"messages": [{"role": "user", "content": question}]},
            config={"configurable": {"thread_id": thread_id}},
        )
        print(result["messages"][-1].content)


if __name__ == "__main__":
    main()
