
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain.agents import create_agent
from langchain.agents.middleware import (
    dynamic_prompt,
    ModelRequest,
)

load_dotenv()

llm = ChatGroq(
    model="openai/gpt-oss-120b",
    temperature=0
)


@dynamic_prompt
def personnaliser_prompt(request: ModelRequest) -> str:

    messages = request.messages

    dernier_message = messages[-1].content.lower()

    if "débutant" in dernier_message:
        print("\n[Dynamic Prompt] Profil débutant sélectionné.")

        return """
        Tu es un professeur patient.
        Explique les concepts avec des mots simples,
        des exemples concrets et des analogies.
        Réponds toujours en français.
        """

    else:
        print("\n[Dynamic Prompt] Profil ingénieur sélectionné.")

        return """
        Tu es un expert en intelligence artificielle
        et en informatique.

        Fournis des explications techniques,
        structurées et détaillées.
        Utilise des termes scientifiques précis.
        Réponds toujours en français.
        """


agent = create_agent(
    model=llm,
    tools=[],
    middleware=[personnaliser_prompt]
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

    tester(
        "Je suis débutant. Explique-moi simplement "
        "ce qu'est le Machine Learning."
    )

    tester(
        "Je suis étudiant ingénieur. Explique-moi "
        "le fonctionnement technique du Machine Learning."
    )
