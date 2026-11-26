
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain.agents import create_agent

# Charger les variables du fichier .env
load_dotenv()

# Initialiser le modèle Groq
llm = ChatGroq(
    model="openai/gpt-oss-120b",
    temperature=0
)

# Créer le premier agent
agent = create_agent(
    model=llm,
    tools=[],
    system_prompt=(
        "Tu es un assistant pédagogique spécialisé en intelligence "
        "artificielle, LangChain et systèmes multi-agents. "
        "Réponds clairement en français."
    )
)

def main():
    response = agent.invoke({
        "messages": [
            {
                "role": "user",
                "content": "Explique-moi ce qu'est un agent IA."
            }
        ]
    })

    print("\nRéponse de l'agent :\n")
    print(response["messages"][-1].content)


if __name__ == "__main__":
    main()
