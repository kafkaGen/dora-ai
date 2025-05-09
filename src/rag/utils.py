import os

from neo4j import GraphDatabase
from qdrant_client import QdrantClient, models

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
        result = session.run(query).data()
        return result


def get_qdrant_engine():
    qdrant_host = os.getenv("QDRANT_HOST", "localhost")
    qdrant_port = int(os.getenv("QDRANT_PORT", "6333"))
    collection_name = os.getenv("QDRANT_COLLECTION_NAME", "dora-ai")

    client = QdrantClient(host=qdrant_host, port=qdrant_port)

    collections = client.get_collections().collections
    collection_names = [collection.name for collection in collections]

    if collection_name not in collection_names:
        # Create a new collection with the specified name
        # Using 1536 dimensions for OpenAI embeddings
        client.create_collection(
            collection_name=collection_name,
            vectors_config=models.VectorParams(size=1536, distance=models.Distance.COSINE),  # OpenAI embedding dimensions
        )
        print(f"Created new Qdrant collection: {collection_name}")

    return client
