import json
import os

from dotenv import load_dotenv
from neo4j import GraphDatabase

ACTION_PROMPT = ""
MODEL = "openai:gpt-4o"

load_dotenv()


def get_neo4j_engine():
    neo4j_host = os.getenv("NEO4J_HOST", "localhost")
    neo4j_port = os.getenv("NEO4J_PORT", "7687")
    neo4j_user = os.getenv("NEO4J_USER", "neo4j")
    neo4j_password = os.getenv("NEO4J_PASSWORD", "neo4j_password")

    uri = f"neo4j://{neo4j_host}:{neo4j_port}"
    driver = GraphDatabase.driver(uri, auth=(neo4j_user, neo4j_password))

    return driver


def run_cypher(query: str, driver: GraphDatabase.driver):
    with driver.session() as session:
        result = session.run(query)
        return result


def if_node_exists(state_id: str, driver: GraphDatabase.driver) -> bool:
    query = """
    MATCH (s:AppState {state_id: $state_id})
    RETURN 1 LIMIT 1
    """
    with driver.session() as session:
        result = session.run(query, {"state_id": state_id})
        record = result.single()  # ✅ first and only access to result
        return record is not None


def generate_cypher_create_node(node_desc: dict, label: str = "AppState") -> str:
    state_description = node_desc["state_description"].replace("'", "\\'")
    enables = json.dumps(node_desc["enables"]).replace("'", "\\'")
    cypher_query = f"""
    CREATE (s:{label} {{
        state_id: '{node_desc["state_id"]}',
        state_name: '{node_desc["state_name"]}',
        state_description: '{state_description}',
        done: {'null' if node_desc["done"] is None else "'" + node_desc["done"] + "'"},
        tags: {[el for el in node_desc["tags"]]},
        enables: '{enables}'
    }})
    RETURN s;
    """

    return cypher_query


def create_node(node_desc_path: str, driver: GraphDatabase.driver):
    with open(node_desc_path, "r") as f:
        node_desc = json.load(f)

    if if_node_exists(node_desc["state_id"], driver):
        print(f"Node {node_desc['state_id']} already exists")
        return

    cypher_query = generate_cypher_create_node(node_desc)
    print(cypher_query)

    return run_cypher(cypher_query, driver)


def process_nodes(driver: GraphDatabase.driver):
    for route in os.listdir("datasets/routes"):
        for step in os.listdir(f"datasets/routes/{route}"):
            node_desc_path = f"datasets/routes/{route}/{step}/node_desc.json"
            create_node(node_desc_path, driver)


def generate_cypher_create_action(action_desc: dict) -> str:
    description = action_desc["description"].replace("'", "\\'")
    cypher_query = f"""
    MATCH (from:AppState {{state_id: '{action_desc['state_id']}'}}), (to:AppState {{state_id: '{action_desc['state_id_2']}'}})
    CREATE (from)-[:TRANSITION {{
    action: '{action_desc['action']}',
    description: '{description}',
    trigger_type: '{action_desc['trigger_type']}'
    }}]->(to);
    """

    return cypher_query


def create_action(action_desc_path: str, driver: GraphDatabase.driver):
    with open(action_desc_path, "r") as f:
        action_desc = json.load(f)

    for action in action_desc["state_transitions"]:
        cypher_query = generate_cypher_create_action(action)
        print(cypher_query)
        run_cypher(cypher_query, driver)


def process_actions(driver: GraphDatabase.driver):
    for route in os.listdir("datasets/routes"):
        for step in os.listdir(f"datasets/routes/{route}"):
            action_desc_path = f"datasets/routes/{route}/{step}/action_desc.json"
            if not os.path.exists(action_desc_path):
                continue
            create_action(action_desc_path, driver)


def process_all():
    driver = get_neo4j_engine()
    process_nodes(driver)
    process_actions(driver)


if __name__ == "__main__":
    process_all()
