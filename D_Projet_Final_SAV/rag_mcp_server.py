from __future__ import annotations

import base64
import json
import mimetypes
import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_groq import ChatGroq
from mcp.server.fastmcp import FastMCP

from common.llm import create_chat_model
from common.manual_search import PROJECT_ROOT, search_manuals

load_dotenv()
mcp = FastMCP(
    "sav-multimodal-rag",
    host=os.getenv("SAV_RAG_HOST", "127.0.0.1"),
    port=int(os.getenv("SAV_RAG_PORT", "8000")),
)


def _figure_file(evidence: dict[str, Any]) -> Path | None:
    image_path = evidence.get("image_path")
    if not image_path:
        return None
    path = (PROJECT_ROOT / str(image_path)).resolve()
    if not path.is_relative_to(PROJECT_ROOT.resolve()):
        raise ValueError("Figure paths must stay inside the project directory.")
    if not path.is_file():
        return None
    if path.stat().st_size > 15_000_000:
        raise ValueError("Indexed figure exceeds the 15 MB limit.")
    return path


def _analyze_figure(path: Path) -> str | None:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return None
    mime_type, _ = mimetypes.guess_type(path.name)
    if mime_type not in {"image/jpeg", "image/png", "image/webp", "image/gif"}:
        raise ValueError(f"Unsupported indexed figure type: {path.suffix}")
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    image_url = f"data:{mime_type};base64,{encoded}"
    model = ChatGroq(
        model=os.getenv("GROQ_VISION_MODEL", "qwen/qwen3.8-27b"),
        temperature=0,
        api_key=api_key,
    )
    response = model.invoke(
        [
            SystemMessage(
                content=(
                    "Describe only visible device indicators and text. Do not infer "
                    "a diagnosis not supported by the image."
                )
            ),
            HumanMessage(
                content=[
                    {"type": "text", "text": "Describe this manual figure."},
                    {"type": "image_url", "image_url": {"url": image_url}},
                ]
            ),
        ]
    )
    return str(response.content)


@mcp.tool()
def rag_multimodal(query: str, image_reference: str | None = None) -> dict[str, Any]:
    """Retrieve cited manual passages/figures and answer only from that evidence."""
    retrieval = search_manuals(query, image_reference=image_reference)
    if not retrieval["sources_found"]:
        return {
            "answer": (
                "Aucune source pertinente n'a ete trouvee dans les manuels indexes. "
                "Ajoutez le manuel et l'index de ses figures avant de conclure."
            ),
            "sources": [],
            "evidence": [],
        }

    evidence = retrieval["results"]
    figure_analysis: list[dict[str, str]] = []
    for item in evidence:
        if item["kind"] != "figure":
            continue
        image_file = _figure_file(item)
        if image_file is None:
            continue
        description = _analyze_figure(image_file)
        if description is None:
            figure_analysis.append(
                {
                    "figure_id": item["figure_id"],
                    "note": (
                        "GROQ_API_KEY is not configured; using the indexed "
                        "manual caption only."
                    ),
                }
            )
        else:
            figure_analysis.append(
                {"figure_id": item["figure_id"], "description": description}
            )

    evidence_payload = {
        "retrieved_items": evidence,
        "figure_analysis": figure_analysis,
    }
    response = create_chat_model().invoke(
        [
            SystemMessage(
                content=(
                    "Reponds en francais, uniquement a partir des elements fournis. "
                    "Cite chaque fait avec le manuel, la page ou l'identifiant de "
                    "figure. Si les elements ne suffisent pas, dis-le."
                )
            ),
            HumanMessage(
                content=(
                    f"Question: {query}\nReference image: {image_reference}\n"
                    f"Elements sources: {json.dumps(evidence_payload, ensure_ascii=False)}"
                )
            ),
        ]
    )
    sources = [
        {
            "manual_id": item["manual_id"],
            "page": item.get("page"),
            "figure_id": item.get("figure_id"),
        }
        for item in evidence
    ]
    return {
        "answer": str(response.content),
        "sources": sources,
        "evidence": evidence_payload,
    }


if __name__ == "__main__":
    mcp.run(transport="streamable-http")
