import os
from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels

# ───────────────────────────────────────────────
# CONFIG
# ───────────────────────────────────────────────
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY", "pokedex-key")
COLLECTION_NAME = os.getenv("QDRANT_COLLECTION", "pokedex_hybrid")


# ───────────────────────────────────────────────
# SEARCH FUNCTIONS
# ───────────────────────────────────────────────
def dense_search(client, query: str, limit: int = 5):
    """Search only using dense embeddings (Jina)."""
    results = client.query_points(
        collection_name=COLLECTION_NAME,
        query=qmodels.Document(
            text=query,
            model="jinaai/jina-embeddings-v2-small-en",
        ),
        using="jina-small",
        limit=limit,
        with_payload=True,
    )
    return results.points


def sparse_search(client, query: str, limit: int = 5):
    """Search only using sparse BM25 vectors."""
    results = client.query_points(
        collection_name=COLLECTION_NAME,
        query=qmodels.Document(
            text=query,
            model="Qdrant/bm25",
        ),
        using="bm25",
        limit=limit,
        with_payload=True,
    )
    return results.points


def hybrid_rrf_search(client, query: str, limit: int = 5):
    """Combine dense + sparse search results using Reciprocal Rank Fusion (RRF)."""
    results = client.query_points(
        collection_name=COLLECTION_NAME,
        prefetch=[
            qmodels.Prefetch(
                query=qmodels.Document(
                    text=query,
                    model="jinaai/jina-embeddings-v2-small-en",
                ),
                using="jina-small",
                limit=5 * limit,
            ),
            qmodels.Prefetch(
                query=qmodels.Document(
                    text=query,
                    model="Qdrant/bm25",
                ),
                using="bm25",
                limit=5 * limit,
            ),
        ],
        query=qmodels.FusionQuery(fusion=qmodels.Fusion.RRF),
        limit=limit,
        with_payload=True,
    )
    return results.points


# ───────────────────────────────────────────────
# MAIN DEMO
# ───────────────────────────────────────────────
def show_results(title: str, results):
    print(f"\n🔎 {title}")
    if not results:
        print("   (no results found)")
        return
    for i, r in enumerate(results, 1):
        payload = r.payload or {}
        doc = payload.get("document_name")
        section = payload.get("section_name")
        snippet = (payload.get("text") or "")[:150].replace("\n", " ")
        print(f"  {i}. ({r.score:.3f}) {doc} — {section}")
        print(f"     {snippet}...\n")


def main():
    client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)

    while True:
        print("\n───────────────────────────────────────────────")
        query = input("🧠 Enter your query (or 'exit' to quit): ").strip()
        if query.lower() in {"exit", "quit"}:
            print("👋 Exiting search tool.")
            break

        dense_results = dense_search(client, query)
        sparse_results = sparse_search(client, query)
        hybrid_results = hybrid_rrf_search(client, query)

        show_results("Dense (Embeddings) Search", dense_results)
        show_results("Sparse (BM25) Search", sparse_results)
        show_results("Hybrid (RRF Fusion) Search", hybrid_results)


if __name__ == "__main__":
    main()
