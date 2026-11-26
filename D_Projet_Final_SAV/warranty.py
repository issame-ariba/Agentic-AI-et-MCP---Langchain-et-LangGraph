from __future__ import annotations

import csv
import json
import os
from datetime import date
from pathlib import Path
from typing import Any

from langchain_core.tools import tool

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REGISTRY = PROJECT_ROOT / "data" / "warranty_registry.example.csv"


def _registry_path() -> Path:
    configured = os.getenv("WARRANTY_REGISTRY_PATH")
    if not configured:
        return DEFAULT_REGISTRY
    path = Path(configured)
    return path if path.is_absolute() else PROJECT_ROOT / path


def lookup_warranty(serial_number: str, registry_path: Path | None = None) -> dict[str, Any]:
    normalized = serial_number.strip().upper()
    if not normalized:
        raise ValueError("A serial number is required.")

    path = registry_path or _registry_path()
    if not path.is_file():
        raise FileNotFoundError(f"Warranty registry not found: {path}")

    with path.open(newline="", encoding="utf-8-sig") as file:
        for row in csv.DictReader(file):
            if row.get("serial_number", "").strip().upper() != normalized:
                continue
            start = date.fromisoformat(row["warranty_start"])
            end = date.fromisoformat(row["warranty_end"])
            today = date.today()
            status = (
                "not_started"
                if today < start
                else "active"
                if today <= end
                else "expired"
            )
            return {
                "serial_number": normalized,
                "product": row.get("product", ""),
                "status": status,
                "warranty_start": start.isoformat(),
                "warranty_end": end.isoformat(),
                "record_kind": row.get("record_kind", "PRODUCTION"),
            }

    return {
        "serial_number": normalized,
        "status": "not_found",
        "message": "Aucun enregistrement trouve dans le registre.",
    }


@tool
def consulter_garantie(serial_number: str) -> str:
    """Consulte le registre local de garantie en lecture seule."""
    return json.dumps(lookup_warranty(serial_number), ensure_ascii=False)
