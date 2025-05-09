from langchain.embeddings import init_embeddings

from src.rag.utils import get_qdrant_engine


def embed(text: str) -> list:
    embed_model = init_embeddings("openai:text-embedding-3-small")
    vector = embed_model.embed_query(text)

    return vector


def get_target_node(user_input: str) -> str:
    qdrant = get_qdrant_engine()
    vector = embed(user_input)
    result = qdrant.search(
        collection_name="dora-ai",
        query_vector=vector,
        limit=1,
    )

    return result[0].payload["state_id"]


if __name__ == "__main__":
    from dotenv import load_dotenv
    from rich import print

    load_dotenv()
    r = get_target_node("How to remove all malware from my computer?")
    print(r)
