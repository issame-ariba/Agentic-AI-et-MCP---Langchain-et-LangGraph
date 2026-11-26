from __future__ import annotations

import asyncio

from D_Projet_Final_SAV.sav_graph import graph

EXAMPLES = [
    "Mon imprimante PX-200 affiche un voyant clignotant. "
    "Que signifie le pictogramme sur la photo jointe ? "
    "Reference img_px200_01",
    "Est-ce que mon imprimante est encore sous garantie ? "
    "Son numero de serie est PX200-0042.",
]


async def main() -> None:
    for request in EXAMPLES:
        result = await graph.ainvoke({"request": request})
        print(f"\nCategorie : {result['category']}")
        print(f"Agent : {result['agent_name']}")
        print(f"Reponse : {result['answer']}")
        print(f"Sources : {result.get('sources', [])}")


if __name__ == "__main__":
    asyncio.run(main())
