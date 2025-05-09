import json

from neo4j import GraphDatabase

from src.rag.utils import get_neo4j_engine, run_cypher


def generate_cypher_shortest_path(traget_node_id: str, start_node_id: str) -> str:
    cypher_query = f"""
    MATCH (start:AppState {{state_id: '{start_node_id}'}})
    MATCH (end:AppState {{state_id: '{traget_node_id}'}})
    MATCH path = shortestPath((start)-[*..50]->(end))
    RETURN
        [n IN nodes(path) | {{id: id(n), labels: labels(n), properties: properties(n)}}] AS nodes,
        [r IN relationships(path) | {{id: id(r), type: type(r), properties: properties(r)}}] AS relationships;
    """
    return cypher_query


def format_path_for_llm(path: list) -> str:
    steps = []
    step_num = 1

    for i in range(0, len(path), 2):  # Each state is followed by action
        state = path[i][1]
        action_taken = path[i + 1][1] if i + 1 < len(path) else None

        state_block = f"Step {step_num}:\n"
        state_block += f"[State: {state['state_name']}]\n"
        state_block += f"Description: {state['state_description']}\n"
        state_block += "Available actions:\n"
        for en in state.get("enables", []):
            state_block += f"- {en['name']}: {en['description']} (action: {en['action']})\n"

        if action_taken:
            state_block += f"\n→ ACTION TAKEN: {action_taken['action']} — {action_taken['description']}\n"

        steps.append(state_block)
        step_num += 1

    return "\n\n".join(steps)


def pretify_path(nodes: list, relationships: list) -> str:
    pretified_nodes = []
    for i, _ in enumerate(nodes):
        node = nodes[i]["properties"]
        del node["neo4jImportId"]
        node["enables"] = json.loads(node["enables"])
        pretified_nodes.append(node)

    pretified_relationships = [rel["properties"] for rel in relationships]

    graph_path = {i * 2: node for i, node in enumerate(pretified_nodes)}
    graph_path.update({i * 2 + 1: rel for i, rel in enumerate(pretified_relationships)})
    graph_path = dict(sorted(graph_path.items()))
    graph_path = [("state" if k % 2 == 0 else "action", v) for k, v in graph_path.items()]
    graph_path = format_path_for_llm(graph_path)

    return graph_path


def find_nearest_graph_path(driver: GraphDatabase.driver, traget_node_id: str, start_node_id: str = "1_1"):
    cypher_query = generate_cypher_shortest_path(traget_node_id, start_node_id)
    result = run_cypher(cypher_query, driver)[0]
    result = pretify_path(result["nodes"], result["relationships"])
    return result


if __name__ == "__main__":
    from dotenv import load_dotenv
    from rich import print

    load_dotenv()

    driver = get_neo4j_engine()
    r = find_nearest_graph_path(driver, "5_3")
    print(r)
