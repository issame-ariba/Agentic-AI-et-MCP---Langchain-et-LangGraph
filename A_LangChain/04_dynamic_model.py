
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain.agents import create_agent
from langchain.agents.middleware import (
    wrap_model_call,
    ModelRequest,
    ModelResponse,
)

load_dotenv()

modele_rapide = ChatGroq(
    model="openai/gpt-oss-20b",
    temperature=0
)

modele_puissant = ChatGroq(
    model="openai/gpt-oss-120b",
    temperature=0
)


@wrap_model_call
def dynamic_model(request: ModelRequest, handler) -> ModelResponse:

    # Récupérer le dernier message utilisateur
    dernier_message = request.messages[-1].content

    # Mesurer la complexité avec la longueur de la question
    if len(dernier_message) > 150:
        print("\n[Dynamic Model] Modèle puissant : gpt-oss-120b")
        modele = modele_puissant
    else:
        print("\n[Dynamic Model] Modèle rapide : gpt-oss-20b")
        modele = modele_rapide

    return handler(request.override(model=modele))


agent = create_agent(
    model=modele_rapide,
    tools=[],
    middleware=[dynamic_model],
    system_prompt="Tu es un assistant pédagogique. Réponds en français."
)


def tester(question):
    print("\nQuestion :", question)

    resultat = agent.invoke({
        "messages": [
            {"role": "user", "content": question}
        ]
    })

    print("\nRéponse :", resultat["messages"][-1].content)


if __name__ == "__main__":

    tester("Bonjour, présente-toi en une phrase.")

    tester(
        "Explique en détail le fonctionnement de l'architecture Transformer, "
        "son mécanisme d'attention, ses avantages, ses limites et ses applications "
        "dans les domaines du traitement du langage naturel et de la vision par ordinateur."
    )
