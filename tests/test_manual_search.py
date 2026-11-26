from __future__ import annotations

import json

from common.manual_search import PROJECT_ROOT, search_manuals


def test_search_returns_cited_passage_and_requested_figure(tmp_path):
    corpus = tmp_path / "corpus.json"
    corpus.write_text(
        json.dumps(
            [
                {
                    "manual_id": "PX-200",
                    "title": "PX-200 manual",
                    "pages": [
                        {
                            "page": 12,
                            "text": "The blinking indicator is described here.",
                        }
                    ],
                    "figures": [
                        {
                            "figure_id": "img_px200_01",
                            "page": 12,
                            "caption": "Indicator pictogram",
                        }
                    ],
                }
            ]
        ),
        encoding="utf-8",
    )

    result = search_manuals(
        "blinking indicator pictogram",
        image_reference="img_px200_01",
        corpus_path=corpus,
    )

    assert result["sources_found"] is True
    assert {item["kind"] for item in result["results"]} == {"passage", "figure"}
    assert all(item["manual_id"] == "PX-200" for item in result["results"])


def test_bundled_demo_corpus_retrieves_labeled_synthetic_figure():
    corpus = PROJECT_ROOT / "data" / "manuals" / "corpus.example.json"
    result = search_manuals(
        "Que signifie le pictogramme du voyant orange clignotant ?",
        image_reference="img_px200_01",
        corpus_path=corpus,
    )

    figure = next(item for item in result["results"] if item["kind"] == "figure")
    image_path = PROJECT_ROOT / figure["image_path"]

    assert result["sources_found"] is True
    assert figure["manual_id"] == "PX-200-DEMO"
    assert "synthétique" in figure["caption"].lower()
    assert image_path.is_file()
