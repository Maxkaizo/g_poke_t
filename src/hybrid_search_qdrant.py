"""
hybrid_search_qdrant.py
──────────────────────────────────────────────
Hybrid (dense + sparse) semantic search for Pokémon RAG system.
──────────────────────────────────────────────
"""

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
# HYBRID SEARCH (RRF)
# ───────────────────────────────────────────────
def hybrid_rrf_search(client, query: str, limit: int = 5):
    """
    Perform hybrid search (dense + sparse) using Reciprocal Rank Fusion (RRF).
    Returns only the final fused results.
    """
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
# DISPLAY RESULTS
# ───────────────────────────────────────────────
def show_results(results):
    print(f"\n🔎 Hybrid (RRF) Search Results")
    if not results:
        print("   (no results found)")
        return

    for i, r in enumerate(results, 1):
        payload = r.payload or {}
        doc = payload.get("document_name")
        section = payload.get("section")
        snippet = (payload.get("text") or "")[:200].replace("\n", " ")
        print(f"  {i}. [score={r.score:.3f}] {doc} — {section}")
        print(f"     {snippet}...\n")


# ───────────────────────────────────────────────
# MAIN DEMO
# ───────────────────────────────────────────────
def main():
    client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)

    while True:
        print("\n───────────────────────────────────────────────")
        query = input("🧠 Enter your query (or 'exit' to quit): ").strip()
        if query.lower() in {"exit", "quit"}:
            print("👋 Exiting search tool.")
            break

        results = hybrid_rrf_search(client, query)
        show_results(results)


if __name__ == "__main__":
    main()
