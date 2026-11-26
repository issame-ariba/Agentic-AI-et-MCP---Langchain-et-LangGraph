
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain.agents import create_agent
from langgraph.checkpoint.memory import InMemorySaver

load_dotenv()

# 1. Initialiser le modèle Groq
llm = ChatGroq(
    model="openai/gpt-oss-120b",
    temperature=0
)

# 2. Créer le système de mémoire
memory = InMemorySaver()

# 3. Créer l'agent avec mémoire
agent = create_agent(
    model=llm,
    tools=[],
    system_prompt=(
        "Tu es un assistant pédagogique spécialisé en intelligence artificielle. "
        "Tu réponds en français et tu tiens compte de l'historique de la conversation."
    ),
    checkpointer=memory
)

# Identifiant de la conversation
config = {
    "configurable": {
        "thread_id": "session_001"
    }
}

def main():

    # Premier message
    print("\n--- PREMIER MESSAGE ---")

    response1 = agent.invoke(
        {
            "messages": [
                {"role": "user", "content": "Je m'appelle Sami et j'étudie l'informatique."}
            ]
        },
        config=config
    )

    print(response1["messages"][-1].content)

    # Deuxième message
    print("\n--- DEUXIEME MESSAGE ---")

    response2 = agent.invoke(
        {
            "messages": [
                {"role": "user", "content": "Comment je m'appelle et qu'est-ce que j'étudie ?"}
            ]
        },
        config=config
    )

    print(response2["messages"][-1].content)


if __name__ == "__main__":
    main()
