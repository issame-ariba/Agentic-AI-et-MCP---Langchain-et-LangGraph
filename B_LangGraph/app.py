from __future__ import annotations

import uuid

import streamlit as st
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.memory import InMemorySaver

from B_LangGraph.agentic_rag import build_graph

graph = build_graph(checkpointer=InMemorySaver())


st.set_page_config(page_title="Agentic RAG - LangGraph", page_icon="RAG")
st.title("Chatbot Agentic RAG")
st.caption("Les réponses doivent être étayées par les manuels indexés.")

if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid.uuid4())
if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

question = st.chat_input("Posez une question sur un appareil...")
if question:
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        with st.spinner("Recherche dans les sources..."):
            result = graph.invoke(
                {"messages": [HumanMessage(content=question)]},
                config={"configurable": {"thread_id": st.session_state.thread_id}},
            )
            answer = str(result["messages"][-1].content)
            st.markdown(answer)
    st.session_state.messages.append({"role": "assistant", "content": answer})
