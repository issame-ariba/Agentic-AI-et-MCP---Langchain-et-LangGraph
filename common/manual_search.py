from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CORPUS = PROJECT_ROOT / "data" / "manuals" / "corpus.json"


def _read_corpus(corpus_path: Path) -> list[dict[str, Any]]:
    payload = json.loads(corpus_path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError(f"Manual corpus must be a JSON list: {corpus_path}")
    for item in payload:
        if not isinstance(item, dict) or not isinstance(item.get("pages", []), list):
            raise ValueError(f"Invalid manual entry in {corpus_path}")
    return payload


def search_manuals(
    query: str,
    image_reference: str | None = None,
    limit: int = 4,
    corpus_path: Path = DEFAULT_CORPUS,
) -> dict[str, Any]:
    if not query.strip():
        raise ValueError("The manual search query must not be empty.")
    if limit < 1:
        raise ValueError("The result limit must be positive.")
    if not corpus_path.is_file():
        raise FileNotFoundError(f"Manual corpus not found: {corpus_path}")

    terms = set(re.findall(r"\w+", query.casefold()))
    results: list[tuple[int, dict[str, Any]]] = []

    for manual in _read_corpus(corpus_path):
        manual_id = str(manual.get("manual_id", "unknown"))
        title = str(manual.get("title", manual_id))
        for page in manual.get("pages", []):
            text = str(page.get("text", ""))
            page_terms = set(re.findall(r"\w+", text.casefold()))
            score = len(terms & page_terms)
            if score:
                results.append(
                    (
                        score,
                        {
                            "kind": "passage",
                            "manual_id": manual_id,
                            "title": title,
                            "page": page.get("page"),
                            "text": text,
                        },
                    )
                )

        for figure in manual.get("figures", []):
            figure_id = str(figure.get("figure_id", ""))
            caption = str(figure.get("caption", ""))
            is_requested_figure = image_reference and figure_id.casefold() == (
                image_reference.casefold()
            )
            figure_terms = set(
                re.findall(r"\w+", f"{figure_id} {caption}".casefold())
            )
            score = len(terms & figure_terms)
            if is_requested_figure:
                score += len(terms) + 1
            if score:
                results.append(
                    (
                        score,
                        {
                            "kind": "figure",
                            "manual_id": manual_id,
                            "title": title,
                            "page": figure.get("page"),
                            "figure_id": figure_id,
                            "caption": caption,
                            "image_path": figure.get("image_path"),
                        },
                    )
                )

    results.sort(key=lambda result: result[0], reverse=True)
    matches = [result for _, result in results[:limit]]
    return {
        "query": query,
        "image_reference": image_reference,
        "results": matches,
        "sources_found": bool(matches),
    }
