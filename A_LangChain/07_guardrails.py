
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain.agents import create_agent
from langchain.agents.middleware import before_agent
from langchain.messages import AIMessage
from langgraph.runtime import Runtime

load_dotenv()

llm = ChatGroq(
    model="openai/gpt-oss-120b",
    temperature=0
)

MOTS_INTERDITS = [
    "piratage",
    "malware",
    "ransomware",
    "voler un mot de passe"
]


@before_agent(can_jump_to=["end"])
def guardrails(state, runtime: Runtime):

    messages = state["messages"]

    if not messages:
        return None

    dernier_message = messages[-1].content.lower()

    for mot in MOTS_INTERDITS:
        if mot in dernier_message:
            print(f"\n[Guardrails] Demande bloquée : {mot}")

            return {
                "messages": [
                    AIMessage(
                        content=(
                            "Votre demande a été bloquée par le système "
                            "de sécurité. Ce sujet n'est pas autorisé."
                        )
                    )
                ],
                "jump_to": "end"
            }

    print("\n[Guardrails] Message autorisé.")
    return None


agent = create_agent(
    model=llm,
    tools=[],
    middleware=[guardrails],
    system_prompt="Tu es un assistant pédagogique. Réponds en français."
)


def tester(question):
    print("\nQuestion :", question)

    resultat = agent.invoke({
        "messages": [
            {"role": "user", "content": question}
        ]
    })

    print("\nRéponse :")
    print(resultat["messages"][-1].content)


if __name__ == "__main__":
    tester("Explique-moi le Machine Learning.")
    tester("Explique-moi comment réaliser un piratage.")
