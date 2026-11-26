
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain.agents import create_agent
from langchain.agents.middleware import wrap_tool_call
from langchain.messages import ToolMessage
from langchain_core.tools import tool

load_dotenv()

llm = ChatGroq(
    model="openai/gpt-oss-120b",
    temperature=0
)


@tool
def diviser(a: float, b: float) -> float:
    """Divise deux nombres."""
    return a / b


@wrap_tool_call
def gestion_erreurs(request, handler):
    try:
        return handler(request)
    except Exception as erreur:
        print("\n[Tool Error Handling] Erreur interceptée :", erreur)

        return ToolMessage(
            content="Une erreur est survenue pendant l'exécution de l'outil. "
                    "Vérifie les paramètres et réessaie.",
            tool_call_id=request.tool_call["id"]
        )


agent = create_agent(
    model=llm,
    tools=[diviser],
    middleware=[gestion_erreurs],
    system_prompt="Tu es un assistant pédagogique. Réponds en français."
)


if __name__ == "__main__":
    resultat = agent.invoke({
        "messages": [
            {
                "role": "user",
                "content": (
                    "Utilise obligatoirement l'outil diviser "
                    "pour calculer 10 divisé par 0. "
                    "N'effectue pas le calcul toi-même."
                )
            }
        ]
    })

    print("\nRéponse de l'agent :")
    print(resultat["messages"][-1].content)
