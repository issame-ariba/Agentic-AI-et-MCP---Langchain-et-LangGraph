"""
A4.5 — Middleware Human-in-the-Loop (HITL)

Principe :
    L'agent peut appeler deux outils :
      - lister_emails_envoyes : lecture seule  -> exécuté sans validation
      - envoyer_email         : action sensible -> exécution SUSPENDUE

    Quand le LLM décide d'appeler `envoyer_email`, le middleware
    `HumanInTheLoopMiddleware` déclenche un `interrupt()` LangGraph :
    le graphe s'arrête, son état est sauvegardé par le checkpointer
    (InMemorySaver), puis on demande une décision à l'humain :

      - approve : l'outil s'exécute avec les arguments proposés
      - edit    : l'humain modifie les arguments avant l'exécution
      - reject  : l'outil n'est PAS exécuté, le LLM est informé du refus

    On reprend ensuite le workflow avec `Command(resume=...)` sur le
    même `thread_id`.

Effet réel de l'outil :
    L'email n'est pas envoyé sur Internet : il est écrit dans
    data/outbox/ (boîte d'envoi locale). C'est un effet de bord réel et
    vérifiable (un fichier est créé uniquement si l'humain approuve).

Exécution :
    python A_LangChain\\08_human_in_the_loop.py
"""

from __future__ import annotations

import json
import re
import uuid
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain.agents.middleware import HumanInTheLoopMiddleware
from langchain_core.tools import tool
from langchain_groq import ChatGroq
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command

load_dotenv()

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTBOX_DIR = PROJECT_ROOT / "data" / "outbox"
EMAIL_REGEX = re.compile(r"^[\w.+-]+@[\w-]+\.[\w.-]+$")

llm = ChatGroq(model="openai/gpt-oss-120b", temperature=0)


# ---------------------------------------------------------------------------
# Outils
# ---------------------------------------------------------------------------
@tool
def envoyer_email(destinataire: str, sujet: str, corps: str) -> str:
    """Envoie un email (déposé dans la boîte d'envoi locale data/outbox).

    Args:
        destinataire: adresse email du destinataire.
        sujet: objet de l'email.
        corps: contenu du message.
    """
    if not EMAIL_REGEX.match(destinataire):
        raise ValueError(f"Adresse email invalide : {destinataire!r}")

    OUTBOX_DIR.mkdir(parents=True, exist_ok=True)
    horodatage = datetime.now().strftime("%Y%m%d_%H%M%S")
    fichier = OUTBOX_DIR / f"email_{horodatage}_{uuid.uuid4().hex[:6]}.txt"
    fichier.write_text(
        f"À : {destinataire}\nObjet : {sujet}\nDate : {datetime.now():%Y-%m-%d %H:%M:%S}\n\n{corps}\n",
        encoding="utf-8",
    )
    return f"Email envoyé à {destinataire} (fichier : {fichier.name})."


@tool
def lister_emails_envoyes() -> str:
    """Liste les emails déjà présents dans la boîte d'envoi (lecture seule)."""
    if not OUTBOX_DIR.exists():
        return "Aucun email envoyé."
    fichiers = sorted(OUTBOX_DIR.glob("email_*.txt"))
    if not fichiers:
        return "Aucun email envoyé."
    return "\n".join(f.name for f in fichiers)


# ---------------------------------------------------------------------------
# Agent avec middleware HITL
# ---------------------------------------------------------------------------
hitl_middleware = HumanInTheLoopMiddleware(
    interrupt_on={
        # Action sensible : validation obligatoire (3 décisions possibles)
        "envoyer_email": {
            "allowed_decisions": ["approve", "edit", "reject"],
            "description": "Envoi d'un email : validation humaine requise",
        },
        # Lecture seule : pas d'interruption
        "lister_emails_envoyes": False,
    },
)

# Le checkpointer est OBLIGATOIRE : c'est lui qui sauvegarde l'état du
# graphe au moment de l'interruption pour pouvoir le reprendre ensuite.
agent = create_agent(
    model=llm,
    tools=[envoyer_email, lister_emails_envoyes],
    middleware=[hitl_middleware],
    checkpointer=InMemorySaver(),
    system_prompt=(
        "Tu es un assistant administratif. Tu peux envoyer des emails avec "
        "l'outil envoyer_email et consulter la boîte d'envoi avec "
        "lister_emails_envoyes. Si un envoi est refusé par l'humain, ne le "
        "relance pas et explique-le à l'utilisateur. Réponds en français."
    ),
)


# ---------------------------------------------------------------------------
# Interaction humaine (console)
# ---------------------------------------------------------------------------
def demander_decision(action: dict, allowed: list[str]) -> dict:
    """Affiche une action en attente et retourne la décision de l'humain."""
    print("\n" + "=" * 60)
    print("⏸  EXÉCUTION SUSPENDUE — validation humaine requise")
    print("=" * 60)
    print(f"Description : {action.get('description', '')}")
    print(f"Outil       : {action['name']}")
    print("Arguments   :")
    print(json.dumps(action["args"], indent=2, ensure_ascii=False))

    choix_map = {"a": "approve", "e": "edit", "r": "reject"}
    while True:
        choix = input("\nDécision ? [a]pprouver / [e]diter / [r]efuser : ").strip().lower()
        decision = choix_map.get(choix)
        if decision in allowed:
            break
        print(f"Choix invalide. Décisions autorisées : {allowed}")

    if decision == "approve":
        return {"type": "approve"}

    if decision == "reject":
        motif = input("Motif du refus (optionnel) : ").strip()
        return {"type": "reject", "message": motif} if motif else {"type": "reject"}

    # edit : l'humain peut remplacer chaque argument (Entrée = conserver)
    nouveaux_args = dict(action["args"])
    for cle, valeur in action["args"].items():
        saisie = input(f"  {cle} [{valeur}] : ").strip()
        if saisie:
            nouveaux_args[cle] = saisie
    return {
        "type": "edit",
        "edited_action": {"name": action["name"], "args": nouveaux_args},
    }


def executer_avec_validation(question: str, thread_id: str) -> None:
    """Lance l'agent et gère les interruptions jusqu'à la réponse finale."""
    config = {"configurable": {"thread_id": thread_id}}
    print(f"\n### Question : {question}")

    resultat = agent.invoke(
        {"messages": [{"role": "user", "content": question}]},
        config=config,
    )

    # Tant que le graphe est interrompu, on collecte les décisions puis on reprend
    while "__interrupt__" in resultat:
        hitl_request = resultat["__interrupt__"][0].value
        decisions = [
            demander_decision(action, review["allowed_decisions"])
            for action, review in zip(
                hitl_request["action_requests"], hitl_request["review_configs"]
            )
        ]
        print("\n▶  Reprise du workflow...")
        resultat = agent.invoke(Command(resume={"decisions": decisions}), config=config)

    print("\n### Réponse finale de l'agent :")
    print(resultat["messages"][-1].content)


if __name__ == "__main__":
    # Scénario 1 : action sensible -> interruption (testez « a » ou « e »)
    executer_avec_validation(
        "Envoie un email à prof.ia@ecole.ma avec pour sujet 'Rendu TP Agentic AI' "
        "et pour message 'Bonjour, je vous confirme le rendu du TP. Cordialement.'",
        thread_id="hitl_001",
    )

    # Scénario 2 : nouvelle demande d'envoi -> testez « r » (refus)
    executer_avec_validation(
        "Envoie un email à tous@ecole.ma avec le sujet 'Test' et le message 'Ceci est un test'.",
        thread_id="hitl_002",
    )

    # Scénario 3 : outil en lecture seule -> AUCUNE interruption
    executer_avec_validation(
        "Liste les emails présents dans la boîte d'envoi.",
        thread_id="hitl_003",
    )
