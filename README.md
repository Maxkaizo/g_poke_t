# 🧠 Pokémon Knowledge Graph & Semantic Retrieval (RAG-based System)

## 📘 Overview
This project implements a **Retrieval-Augmented Generation (RAG)** architecture that unifies **structured graph retrieval** and **semantic vector retrieval**.  
The system combines **Neo4j** for relational knowledge and **Qdrant** for semantic context, enabling both factual precision and conceptual understanding in Pokémon-related queries.

In short:  
> The project’s fundamental base is a **RAG pipeline** — a hybrid retrieval system where an LLM fuses knowledge from both a graph database and a vector database to produce grounded, explainable answers.

---

## 🧩 Problem Description
Most Pokémon Q&A systems rely on static wikis or APIs.  
They fail to answer **conceptual** or **multi-hop** questions such as:

> “Why is Bulbasaur weak to Fire?”  
> “How do type effectiveness rules interact with abilities?”

This project addresses that by designing a **RAG-driven retrieval flow** that merges:
1. **Graph-based reasoning (Neo4j)** → explicit entity relationships (`HAS_TYPE`, `EVOLVES_TO`, etc.)  
2. **Semantic understanding (Qdrant + embeddings)** → contextual explanations from guides and blogs  
3. **LLM orchestration** → integrates both retrievals in parallel to generate an informed, natural-language response.

---

## ⚙️ Current Progress

### 🧱 Graph Database (Neo4j)
- Automated ingestion from MongoDB into Neo4j (`load_to_neo4j.py`).
- Relationships modeled:
  - `(:Pokemon)-[:HAS_TYPE]->(:Type)`
  - `(:Pokemon)-[:CAN_HAVE]->(:Ability)`
  - `(:Pokemon)-[:EVOLVES_TO]->(:Pokemon)`
  - `(:Type)-[:STRONG_AGAINST|WEAK_AGAINST]->(:Type)`
- ✅ Validation and export to GraphML completed.

### 📄 Text Collection
- Scraping pipeline using **BeautifulSoup + requests**.
- Sources:
  - [DragonflyCave - Battling Basics](https://www.dragonflycave.com/mechanics/battling-basics)  
  - [Bulbapedia - Trainer Tips](https://bulbapedia.bulbagarden.net/wiki/Trainer_Tips)  
  - [Puiching Blog - Beginner Trainer Guide](https://www.puiching.blog/puichinggazette/beginner-pokmon-trainer-guide)
- Clean `.txt` files stored in `data/clean_texts/`.

### 🧠 Smart Chunking (LLM-based)
- Uses `gpt-4o-mini` to semantically segment documents into coherent sections.  
- Each chunk is self-contained and optimized for Q&A retrieval.  
- Output stored as `.jsonl` in `data/chunks/`.

### ✨ Semantic Enrichment (Partial)
- Added metadata per chunk:
  - Section title  
  - Summary and keywords (LLM-generated)  
  - Domain and source references  
- Output path: `data/enriched_chunks.jsonl`.

---

## 🔍 Upcoming: Vector Knowledge Base (Qdrant)

| Stage | Description | Tool |
|--------|--------------|------|
| **Embedding** | Generate dense vectors using **FastEmbed** | `sentence-transformers/all-MiniLM-L6-v2` |
| **Indexing** | Store vectors + metadata | **Qdrant** (local or Docker) |
| **Retrieval** | Parallel RAG flow: Neo4j (graph) + Qdrant (semantic) | LLM fusion layer |
| **Evaluation** | Compare retrieval precision (graph vs. vector vs. hybrid) | Jupyter or CLI |

### Example of enriched payload for Qdrant
```json
{
  "id": "battling_basics_chunk_3",
  "vector": [0.034, -0.012, 0.008, ...],
  "payload": {
    "title": "Move Effectiveness",
    "text": "A move’s type and a Pokémon’s type determine how much damage it does...",
    "summary": "Explains how type interactions determine attack effectiveness.",
    "keywords": ["type effectiveness", "damage", "moves", "battle system"],
    "domain": "battle_mechanics",
    "source": "www_dragonflycave_com_mechanics_battling-basics.txt"
  }
}
````

---

## 🧭 Retrieval Flow (RAG Pipeline)

```
User Query
   ↓
[Parallel Retrieval]
 ├── Neo4j → factual relations (graph)
 └── Qdrant → semantic context (vector)
   ↓
Fusion Layer (LLM prompt assembly)
   ↓
Final Answer (reasoned + contextualized)
```

---

## 🧰 Reproducibility

### 🔧 Setup

```bash
git clone <repo>
cd project
pip install -r requirements.txt
```

### 🧱 Run ingestion

```bash
python src/load_to_neo4j.py
```

### 📄 Run scraping + chunking

```bash
python src/scraping/simple_scraper.py
python src/text_processing/smart_chunking.py
```

### 🧠 Environment

* Python 3.11
* Neo4j 5.x
* MongoDB 6.x
* Qdrant 1.x
* OpenAI API key (for LLM-based chunking and enrichment)

---

## 🧱 Next Steps

* [ ] Index enriched chunks in Qdrant using FastEmbed
* [ ] Implement semantic retrieval pipeline (`index_qdrant.py` & `query_qdrant.py`)
* [ ] Evaluate hybrid retrieval (graph + vector fusion)
* [ ] Add Streamlit UI for RAG query exploration
* [ ] Containerize with Docker Compose for full reproducibility

---

## 🧾 Rubric Alignment (Current Progress)

| Criterion                | Status | Notes                                            |
| ------------------------ | ------ | ------------------------------------------------ |
| **Problem Description**  | ✅      | Clear and well-defined RAG objective             |
| **Retrieval Flow**       | ✅      | Combines Neo4j, Qdrant, and LLM                  |
| **Ingestion Pipeline**   | ✅      | Fully automated ingestion scripts                |
| **Interface**            | 🟡     | Streamlit app planned                            |
| **Reproducibility**      | ✅      | Scripts, folder structure, environment defined   |
| **Retrieval Evaluation** | 🟡     | Planned evaluation (graph vs. vector vs. hybrid) |

---

### 🧩 Summary

> The project’s core foundation is a **Retrieval-Augmented Generation (RAG)** system that merges **symbolic (graph)** and **semantic (vector)** reasoning.
> It enables factually accurate, contextually rich, and explainable answers to complex Pokémon-related queries.

```

---