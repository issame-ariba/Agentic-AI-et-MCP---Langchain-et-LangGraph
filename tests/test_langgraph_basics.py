from B_LangGraph.langgraph_basics import graph


def test_basic_graph_runs_nodes_in_order():
    result = graph.invoke({"topic": "StateGraph", "steps": []})

    assert result["steps"] == [
        "Requete recue: StateGraph",
        "Resume prepare par un noeud du graphe.",
    ]
