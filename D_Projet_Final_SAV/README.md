# Synthese SAV

## Architecture

The LangGraph orchestrator routes each request to exactly one specialized node:

- `agent_documentaire` calls the remote MCP tool `rag_multimodal`.
- `agent_garantie` calls the local read-only `consulter_garantie` tool.

The documentation MCP server searches page excerpts and indexed figure captions
in `data/manuals/corpus.json`. The bundled `corpus.example.json` and
`img_px200_01_demo.png` are synthetic `DEMO_ONLY` teaching data, not an official
PX-200 manual or a real device photo. They let you exercise retrieval and
citation, but cannot establish a real device diagnosis. For real use, replace
them with an authorized manual and the actual image. If an indexed figure has an
image path and `GROQ_API_KEY` is configured, it is sent to the Groq vision model.
The model defaults to `qwen/qwen3.8-27b`; set `GROQ_VISION_MODEL` to override it.
Final answers cite the retrieved manual/page/figure evidence.

The instructor's [RAG-as-MCP reference](https://github.com/mohamedYoussfi/agent-rag-as-tool-mcp-v2)
demonstrates the same general MCP/RAG pattern with a different sample corpus.

## Start the remote documentation tool

In one terminal, configure `GROQ_API_KEY` and optionally `GROQ_VISION_MODEL`,
then run:

```powershell
python -m D_Projet_Final_SAV.rag_mcp_server
```

By default the Streamable HTTP endpoint is `http://127.0.0.1:8000/mcp`.
Set `SAV_RAG_PORT` to change the server port and `RAG_MCP_URL` to point the
orchestrator at that endpoint. For example, when port 8000 is already in use,
set the server variable in its terminal:

```powershell
$env:SAV_RAG_PORT = "8001"
python -m D_Projet_Final_SAV.rag_mcp_server
```

In the terminal used to start the orchestrator, set the matching client URL:

```powershell
$env:RAG_MCP_URL = "http://127.0.0.1:8001/mcp"
python -m D_Projet_Final_SAV.main
```

## Warranty registry

The local CSV is opened only for reading. `data/warranty_registry.example.csv`
contains a clearly marked fictitious record for the required example serial.
Replace it with an authorized registry before making real warranty decisions:

```powershell
$env:WARRANTY_REGISTRY_PATH = "C:\path\to\authorized_registry.csv"
```

## Index manuals and test the required examples

Copy `data/manuals/corpus.example.json` to `data/manuals/corpus.json` to run the
synthetic demonstration, or replace it with reviewed excerpts from an
authorized manual and metadata for its real figures. Example shape:

```json
[
  {
    "manual_id": "PX-200",
    "title": "PX-200 official manual",
    "pages": [{"page": 12, "text": "Curated, verified excerpt..."}],
    "figures": [
      {
        "figure_id": "img_px200_01",
        "page": 12,
        "caption": "Verified caption from the manual",
        "image_path": "data/manuals/figures/px200-indicator.png"
      }
    ]
  }
]
```

Run the documentation MCP server first, then in another terminal:

```powershell
python -m D_Projet_Final_SAV.main
```

The local example registry and bundled manual/illustration are test data only.
The actual PX-200 manual and photograph were not supplied, so any response from
the bundled corpus must be treated as fictional demonstration output.
