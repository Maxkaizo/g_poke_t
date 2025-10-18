# ✅ Pokémon Trainer Assistant — Project Checklist  
**Goal:** Deliver a functional, evaluated, and reproducible RAG-based Pokémon strategy assistant for the LLM Zoomcamp.

---

## ⚙️ Environment Setup

- [ ] Initialize project repository `pokemon_trainer_assistant`
- [ ] Create `.gitignore` (add `.env`, `/data/raw`, `/__pycache__`)
- [ ] Initialize environment using **uv**  
  ```bash
  uv init
  uv add qdrant-client fastembed openai streamlit pandas python-dotenv arize-phoenix neo4j dlt
````

* [ ] Create `.env` file with API keys:

  ```env
  OPENAI_API_KEY=sk-...
  QDRANT_URL=http://localhost:6333
  NEO4J_URI=bolt://localhost:7687
  NEO4J_USER=neo4j
  NEO4J_PASSWORD=example
  ```
* [ ] Verify environment by running:

  ```bash
  uv run python -m streamlit hello
  ```

---

## 🗓️ PHASE 1 — Data Ingestion (PokéAPI via dlt)

**Goal:** Automate the creation of a local Pokédex dataset.

* [ ] Create file `src/ingest_pokeapi_dlt.py`
* [ ] Define `dlt` pipeline that fetches first 50 Pokémon from PokéAPI
* [ ] Save output to `data/processed/pokedex.csv`
* [ ] Preview data with pandas to ensure correctness
* [ ] Commit `data/processed/pokedex.csv` (or generate on demand)
* [ ] Verify that ingestion runs end-to-end:

  ```bash
  uv run python src/ingest_pokeapi_dlt.py
  ```

---

## 🧠 PHASE 2 — Embeddings + Qdrant Index

**Goal:** Generate semantic representations of Pokédex entries.

* [ ] Create file `src/embed_index.py`
* [ ] Load Pokédex CSV
* [ ] Generate embeddings with **FastEmbed**
* [ ] Store vectors and metadata in **Qdrant**
* [ ] Confirm insertion via `qdrant-client` (e.g., count points)
* [ ] Add configuration in `.env` or use default localhost setup
* [ ] Quick test retrieval with a random Pokémon name

---

## 🔍 PHASE 3 — Retrieval + Generator (RAG Core)

**Goal:** Connect search results to GPT-4o-mini for contextual answers.

* [ ] Create `src/retriever.py` to query Qdrant based on user input
* [ ] Create `src/generator.py` to:

  * [ ] Build a contextual prompt from retrieved documents
  * [ ] Call **GPT-4o-mini** through OpenAI API
* [ ] Test flow manually:

  ```bash
  uv run python -m src.generator "¿Cómo puedo vencer a Squirtle?"
  ```
* [ ] Verify end-to-end RAG response quality

---

## 🕸️ PHASE 4 — GraphRAG Integration (Neo4j)

**Goal:** Model Pokémon type relationships as a graph and enrich retrieval.

* [ ] Run or connect to local **Neo4j** instance
* [ ] Create `src/graph_integration.py`
* [ ] Define relationships (e.g. fuego → planta, agua → fuego)
* [ ] Implement functions:

  * [ ] `load_relations()` — populate graph
  * [ ] `get_advantages(type)` — query strong matchups
* [ ] Integrate Neo4j context into retrieval flow
* [ ] Optional: store graph edges in `data/processed/relationships.csv`

---

## 📊 PHASE 5 — Evaluation and Monitoring

**Goal:** Measure retrieval and response quality.

* [ ] Create `src/evaluate.py`
* [ ] Implement metrics:

  * [ ] `hit_rate`, `mrr`
  * [ ] Cosine similarity on retrieved vs. ground truth
* [ ] Install and configure **Arize Phoenix**
* [ ] Send test results to Phoenix dashboard
* [ ] Log two retrieval strategies (BM25 vs. Qdrant)
* [ ] Identify which performs better

---

## 💬 PHASE 6 — Streamlit App (Interface)

**Goal:** Provide an interactive interface for users.

* [ ] Create `src/app.py`
* [ ] Add chat UI with:

  * [ ] Input box for user queries
  * [ ] Display area for assistant responses
  * [ ] Feedback buttons 👍 / 👎
* [ ] Integrate RAG pipeline (retriever + generator)
* [ ] Display debug info (retrieved Pokémon names, response tokens)
* [ ] Run and test locally:

  ```bash
  uv run streamlit run src/app.py
  ```

---

## 🧾 PHASE 7 — Documentation and Delivery

**Goal:** Prepare final version for submission.

* [ ] Create `README.md` (use project guide as base)
* [ ] Add **setup instructions** with `uv` commands
* [ ] Include screenshots of Streamlit app
* [ ] Record short **demo video** (Loom or GIF)
* [ ] Push final commit
* [ ] Submit GitHub repo link and commit hash in form

---

## 🧱 Optional: Containerization (Docker)

**Goal:** Make the environment reproducible for reviewers.

* [ ] Create `Dockerfile` (base: `python:3.11-slim`)
* [ ] Install `uv` inside container
* [ ] Add service in `docker-compose.yml` for Qdrant + app
* [ ] Test build:

  ```bash
  docker compose up
  ```

---

## 📋 Final Review Checklist

| Task                           | Status |
| ------------------------------ | ------ |
| RAG pipeline runs end-to-end   | [ ]    |
| Data ingestion via dlt works   | [ ]    |
| Vector retrieval functional    | [ ]    |
| Graph layer adds context       | [ ]    |
| GPT-4o-mini responds correctly | [ ]    |
| Evaluation metrics implemented | [ ]    |
| Streamlit interface tested     | [ ]    |
| README and demo video ready    | [ ]    |
| Submitted to project form      | [ ]    |

---

### 🧭 Execution Notes

* Focus on **working pipeline first**, documentation last.
* Neo4j is optional but valuable for GraphRAG enrichment.
* Arize Phoenix can be run locally if cloud access is slow.
* Avoid overfitting UI — priority is delivery by **Sunday night**.
* Use `uv run` consistently to avoid dependency drift.

---

*LLM Zoomcamp Final Project — Execution Checklist (October 2025)*
*Author: MaxKaizo*
