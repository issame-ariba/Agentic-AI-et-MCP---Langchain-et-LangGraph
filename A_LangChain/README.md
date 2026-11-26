# LangChain RAG agent

Configure `GROQ_API_KEY`, then run:

```powershell
python -m A_LangChain.agentic_rag
```

The agent has an in-memory conversation checkpoint and a manual/figure search
tool. Copy `data/manuals/corpus.example.json` to `data/manuals/corpus.json`, then
add real manual page excerpts and figure captions before relying on its answers.
Unsupported questions must be answered as unsupported, not guessed.
