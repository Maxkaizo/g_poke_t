import os
import json
import glob
import uuid
from tqdm import tqdm
from qdrant_client import QdrantClient
from qdrant_client.http import models

# ───────────────────────────────────────────────
# CONFIG
# ───────────────────────────────────────────────
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY", "pokedex-key")
COLLECTION_NAME = os.getenv("QDRANT_COLLECTION", "pokedex_hybrid")
CHUNKS_DIR = os.getenv("CHUNKS_DIR", "data/chunks")


# ───────────────────────────────────────────────
# LOAD CHUNKS
# ───────────────────────────────────────────────
def read_jsonl(path):
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                yield json.loads(line)

def load_all_chunks(base_dir):
    files = glob.glob(os.path.join(base_dir, "*.jsonl"))
    records = []
    for fp in files:
        records.extend(list(read_jsonl(fp)))
    return records


# ───────────────────────────────────────────────
# MAIN
# ───────────────────────────────────────────────
def main():
    print("🚀 Starting hybrid indexing (dense + sparse, official syntax)...")

    client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)
    records = load_all_chunks(CHUNKS_DIR)
    if not records:
        raise RuntimeError("❌ No records found in data/chunks/")


    # ───────────────────────────────────────────────
    # RESET COLLECTION (opcional)
    # ───────────────────────────────────────────────
    if COLLECTION_NAME in [c.name for c in client.get_collections().collections]:
        print(f"🗑️  Deleting existing collection '{COLLECTION_NAME}'...")
        client.delete_collection(collection_name=COLLECTION_NAME)



    # ───────────────────────────────────────────────
    # CREATE COLLECTION (multi-vector, hybrid)
    # ───────────────────────────────────────────────
    collections = [c.name for c in client.get_collections().collections]

    if COLLECTION_NAME not in collections:
        print(f"🧱 Creating collection '{COLLECTION_NAME}'...")
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config={
                # Dense vector subspace for Jina embeddings
                "jina-small": models.VectorParams(
                    size=512,
                    distance=models.Distance.COSINE,
                ),
            },
            sparse_vectors_config={
                # Sparse subspace for BM25
                "bm25": models.SparseVectorParams(
                    modifier=models.Modifier.IDF,
                ),
            },
        )

    # ───────────────────────────────────────────────
    # UPSERT DOCUMENTS
    # ───────────────────────────────────────────────
    points = []
    for rec in tqdm(records, desc="Indexing chunks"):
        text = rec["text"]
        points.append(
            models.PointStruct(
                id=rec["chunk_id"],
                vector={
                    "jina-small": models.Document(
                        text=text,
                        model="jinaai/jina-embeddings-v2-small-en",
                    ),
                    "bm25": models.Document(
                        text=text,
                        model="Qdrant/bm25",
                    ),
                },
                payload={
                    "chunk_id": rec["chunk_id"],
                    "document_name": rec["document_name"],
                    "section_name": rec.get("section_name"),
                    "chunk_index": rec.get("chunk_index"),
                    "text": text[:512],
                },
            )
        )

    client.upsert(collection_name=COLLECTION_NAME, points=points)
    print(f"✅ Indexed {len(points)} chunks into '{COLLECTION_NAME}' collection.")

    # ───────────────────────────────────────────────
    # QUICK VALIDATION
    # ───────────────────────────────────────────────
    sample_query = records[0]["text"][:200]
    print("\n🔎 Running hybrid validation query...")

    results = client.query_points(
        collection_name=COLLECTION_NAME,
        prefetch=[
            models.Prefetch(
                query=models.Document(
                    text=sample_query,
                    model="jinaai/jina-embeddings-v2-small-en",
                ),
                using="jina-small",
                limit=10,
            ),
            models.Prefetch(
                query=models.Document(
                    text=sample_query,
                    model="Qdrant/bm25",
                ),
                using="bm25",
                limit=10,
            ),
        ],
        query=models.FusionQuery(fusion=models.Fusion.RRF),
        limit=3,
        with_payload=True,
    )

    print("✅ Validation results:")
    for i, r in enumerate(results.points, 1):
        meta = r.payload or {}
        print(f"  {i}. score={r.score:.3f}  doc={meta.get('document_name')} section={meta.get('section_name')}")

    print("\n🏁 Hybrid indexing completed successfully.")


if __name__ == "__main__":
    main()
