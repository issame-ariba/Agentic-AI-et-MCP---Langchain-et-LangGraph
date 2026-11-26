
import os
from dotenv import load_dotenv

from langchain_groq import ChatGroq
from langchain.agents import create_agent
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_tavily import TavilySearch
from langchain_experimental.tools import PythonREPLTool

load_dotenv()

# 1. Initialisation du modèle Groq
llm = ChatGroq(
    model="openai/gpt-oss-120b",
    temperature=0
)

# 2. Initialisation des outils
duckduckgo = DuckDuckGoSearchRun()

python_tool = PythonREPLTool()

# Tavily nécessite une clé API
tools = [
    duckduckgo,
    python_tool
]

if os.getenv("TAVILY_API_KEY"):
    tavily = TavilySearch(max_results=5)
    tools.append(tavily)
print("\nOutils disponibles :", [tool.name for tool in tools])

if os.getenv("TAVILY_API_KEY"):
    print("\n=== TEST DIRECT DE TAVILY ===")
    resultat = tavily.invoke({
        "query": "Quelles sont les nouveautés de Python 3.14 ?"
    })
    print(resultat)

# 3. Création de l'agent
agent = create_agent(
    model=llm,
    tools=tools,
    system_prompt="""
    Tu es un assistant intelligent utilisant Groq.

    Tu disposes de trois outils :
    - DuckDuckGo : recherche sur Internet.
    - Tavily : recherche web avancée.
    - Python REPL : calculs et exécution de code Python.

    Choisis l'outil adapté à chaque question.
    Réponds toujours en français.
    """
)

# 4. Fonction de test
def tester_agent(question):
    print("\nQuestion :", question)

    response = agent.invoke({
        "messages": [
            {"role": "user", "content": question}
        ]
    })

    print("\nRéponse :", response["messages"][-1].content)


if __name__ == "__main__":

    tester_agent("Calcule 125 * 48 avec Python.")

    tester_agent(
        "Recherche sur Internet les principales nouveautés de Python 3.14."
    )

