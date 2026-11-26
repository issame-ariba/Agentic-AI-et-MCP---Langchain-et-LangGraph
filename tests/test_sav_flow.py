from __future__ import annotations

import asyncio
import csv

from D_Projet_Final_SAV.routing import route_request
from D_Projet_Final_SAV.sav_graph import build_graph
from D_Projet_Final_SAV.warranty import lookup_warranty


def test_required_examples_route_to_the_expected_specialists():
    documentation = route_request(
        "Mon imprimante PX-200 affiche un voyant clignotant. "
        "Que signifie le pictogramme sur la photo jointe ? "
        "Reference img_px200_01"
    )
    warranty = route_request(
        "Est-ce que mon imprimante est encore sous garantie ? "
        "Son numero de serie est PX200-0042."
    )

    assert (documentation["category"], documentation["agent_name"]) == (
        "documentation",
        "agent_documentaire",
    )
    assert documentation["image_reference"] == "IMG_PX200_01"
    assert (warranty["category"], warranty["agent_name"]) == (
        "garantie",
        "agent_garantie",
    )
    assert warranty["serial_number"] == "PX200-0042"


def test_graph_calls_one_documentation_agent_and_ends():
    async def run():
        calls = []

        async def fake_rag(query, image_reference):
            calls.append((query, image_reference))
            return {
                "answer": "Reponse documentee [PX-200, p. 12].",
                "sources": [{"manual_id": "PX-200", "page": 12}],
            }

        graph = build_graph(documentation_runner=fake_rag)
        request = "Que signifie la photo ? Reference img_px200_01"
        result = await graph.ainvoke({"request": request})

        assert result["category"] == "documentation"
        assert result["agent_name"] == "agent_documentaire"
        assert result["answer"] == "Reponse documentee [PX-200, p. 12]."
        assert calls == [(request, "IMG_PX200_01")]

    asyncio.run(run())


def test_warranty_lookup_reads_registry_and_marks_demo_record(tmp_path):
    registry = tmp_path / "registry.csv"
    with registry.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=[
                "serial_number",
                "product",
                "warranty_start",
                "warranty_end",
                "record_kind",
            ],
        )
        writer.writeheader()
        writer.writerow(
            {
                "serial_number": "PX200-0042",
                "product": "PX-200",
                "warranty_start": "2025-01-01",
                "warranty_end": "2027-01-01",
                "record_kind": "DEMO_ONLY",
            }
        )
    before = registry.read_bytes()

    result = lookup_warranty("px200-0042", registry)

    assert result["status"] == "active"
    assert result["record_kind"] == "DEMO_ONLY"
    assert registry.read_bytes() == before


def test_required_warranty_example_uses_local_agent_only(tmp_path, monkeypatch):
    registry = tmp_path / "registry.csv"
    registry.write_text(
        "serial_number,product,warranty_start,warranty_end,record_kind\n"
        "PX200-0042,PX-200,2025-01-01,2027-01-01,DEMO_ONLY\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("WARRANTY_REGISTRY_PATH", str(registry))

    async def run():
        async def fail_if_called(query, image_reference):
            raise AssertionError(
                f"Unexpected warranty RAG call: {query!r}, {image_reference!r}"
            )

        graph = build_graph(documentation_runner=fail_if_called)
        result = await graph.ainvoke(
            {
                "request": (
                    "Est-ce que mon imprimante est encore sous garantie ? "
                    "Son numero de serie est PX200-0042."
                )
            }
        )
        assert result["category"] == "garantie"
        assert result["agent_name"] == "agent_garantie"
        assert "DEMO_ONLY" in result["answer"] or "fictive" in result["answer"]

    asyncio.run(run())
