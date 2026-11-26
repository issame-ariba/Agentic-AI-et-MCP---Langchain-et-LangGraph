# LangGraph and Streamlit

Run the basic graph:

```powershell
python B_LangGraph\langgraph_basics.py
```

Run the chatbot after setting `GROQ_API_KEY`:

```powershell
streamlit run B_LangGraph\app.py
```

`agentic_rag.py` exports `graph` for LangGraph Studio, which supplies its own
persistence. The Streamlit app compiles the same graph with an in-memory
checkpointer for conversation history. From the project root, start Studio with
`langgraph dev`. The graph uses the same manual corpus as the LangChain
exercise; add real sources before asking it for device-specific instructions.
