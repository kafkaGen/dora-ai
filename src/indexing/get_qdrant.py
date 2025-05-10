from langchain.embeddings import init_embeddings
from neo4j import GraphDatabase
from qdrant_client import models

from src.rag.utils import get_neo4j_engine, get_qdrant_engine, run_cypher


def get_all_nodes(driver: GraphDatabase.driver) -> list:
    cypher_query = """
    MATCH (n)
    RETURN n.state_id, labels(n), properties(n);
    """
    result = run_cypher(cypher_query, driver)
    result = [r["properties(n)"] for r in result]
    return result


def embed(text: str) -> list:
    embed_model = init_embeddings("openai:text-embedding-3-small")
    vector = embed_model.embed_query(text)

    return vector


def process_all():
    driver = get_neo4j_engine()
    qdrant = get_qdrant_engine()

    for node in get_all_nodes(driver):
        chunk = f"""
        State Name: {node['state_name']}.
        \nState Description: {node['state_description']}.
        \nState Tags: {node['tags']}.
        """
        if len(node.get("done", "")) > 10:
            chunk += f"\nState Done: {node['done']}"
        node["chunk"] = chunk
        embedding = embed(chunk)
        qdrant.upsert(
            collection_name="dora-ai",
            points=[
                models.PointStruct(
                    id=int(node["neo4jImportId"]),
                    vector=embedding,
                    payload=node,
                )
            ],
        )


if __name__ == "__main__":
    from dotenv import load_dotenv

    load_dotenv()
    process_all()
