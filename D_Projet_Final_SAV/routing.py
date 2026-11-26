from __future__ import annotations

import re
import unicodedata
from typing import Literal, TypedDict


Category = Literal["documentation", "garantie"]


class RoutingResult(TypedDict):
    category: Category
    agent_name: Literal["agent_documentaire", "agent_garantie"]
    serial_number: str | None
    image_reference: str | None


def _fold(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text.casefold())
    return "".join(char for char in normalized if not unicodedata.combining(char))


def route_request(request: str) -> RoutingResult:
    if not request.strip():
        raise ValueError("The SAV request must not be empty.")

    upper_request = request.upper()
    serial_match = re.search(r"\b[A-Z]{2,}\d{2,}-\d+\b", upper_request)
    image_match = re.search(r"\bIMG_[A-Z0-9_-]+\b", upper_request)
    folded = _fold(request)
    warranty_terms = ("garantie", "warranty", "numero de serie", "serial number")

    if serial_match or any(term in folded for term in warranty_terms):
        return {
            "category": "garantie",
            "agent_name": "agent_garantie",
            "serial_number": serial_match.group(0) if serial_match else None,
            "image_reference": None,
        }

    return {
        "category": "documentation",
        "agent_name": "agent_documentaire",
        "serial_number": None,
        "image_reference": image_match.group(0) if image_match else None,
    }
