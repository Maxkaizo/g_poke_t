# 🧠 Pokémon Trainer Assistant  
**A RAG-based Pokémon Strategy Assistant powered by GPT-4o-mini, Qdrant, and FastEmbed**

---

## 🎯 Objective

Build an intelligent assistant that helps Pokémon players make better battle decisions.

The system retrieves contextual information (types, abilities, weaknesses) from a **Pokédex knowledge base**, enriches it using a **graph of Pokémon type relationships**, and generates personalized strategies through **GPT-4o-mini**.

---

## 🧩 Core Architecture

```

PokéAPI → dlt → pokedex.csv → FastEmbed → Qdrant
│
Neo4j (GraphRAG-lite)
│
Streamlit app + GPT-4o-mini

```

---

## ⚙️ Technologies

| Component | Tool | Notes |
|------------|------|-------|
| **Data ingestion** | [`dlt`](https://dlthub.com/) | Automated pipeline from PokéAPI |
| **Vector DB** | [Qdrant](https://qdrant.tech/) | Semantic search and retrieval |
| **Embeddings** | [FastEmbed](https://github.com/qdrant/fastembed) | Lightweight, high-speed embeddings |
| **Graph database** | [Neo4j](https://neo4j.com/) | Models Pokémon type relationships |
| **LLM** | OpenAI GPT-4o-mini | Cost-efficient and fast |
| **Interface** | Streamlit | For end-user interaction |
| **Evaluation** | Arize Phoenix | Retrieval and response quality monitoring |
| **Containerization** | Docker (optional) | For full reproducibility |

---

## 📁 Repository Structure

```

pokemon_trainer_assistant/
│
├── data/
│   ├── raw/                   # Raw PokéAPI extractions
│   ├── processed/             # Cleaned and merged data
│   │   ├── pokedex.csv
│   │   └── relationships.csv
│
├── src/
│   ├── ingest_pokeapi_dlt.py  # Fetch & transform data using dlt
│   ├── embed_index.py         # Generate embeddings and build Qdrant index
│   ├── retriever.py           # Query semantic matches
│   ├── generator.py           # Compose prompts and call GPT-4o-mini
│   ├── graph_integration.py   # Load and query Neo4j graph
│   ├── evaluate.py            # Evaluate retrieval and LLM output
│   └── app.py                 # Streamlit front-end
│
├── requirements.txt
├── .env
└── README.md (this file)

````

---

## 📅 Project Roadmap (Phased Execution)

### 🗓️ **Phase 1 — Ingestion (Thursday)**
**Goal:** Create a clean Pokédex dataset from PokéAPI using `dlt`.

**Deliverables:**
- `src/ingest_pokeapi_dlt.py`
- `data/processed/pokedex.csv`
- Logs or preview showing 50 Pokémon loaded successfully

---

### 🗓️ **Phase 2 — Vectorization (Friday)**
**Goal:** Convert text fields (types, abilities, descriptions) into embeddings with FastEmbed and store them in Qdrant.

**Deliverables:**
- `src/embed_index.py`
- Working local Qdrant instance or memory index
- Test retrieval working in `retriever.py`

---

### 🗓️ **Phase 3 — Generation (Friday–Saturday)**
**Goal:** Connect retriever output to GPT-4o-mini and build the end-to-end RAG pipeline.

**Deliverables:**
- `src/generator.py` combining context + prompt
- Working text responses from LLM

---

### 🗓️ **Phase 4 — Graph Integration (Saturday)**
**Goal:** Add a graph-based layer using Neo4j to model type advantages and weaknesses.

**Deliverables:**
- `src/graph_integration.py` with Cypher queries
- Type advantage enrichment integrated into retrieval flow

---

### 🗓️ **Phase 5 — Evaluation and Monitoring (Saturday–Sunday)**
**Goal:** Evaluate the RAG pipeline and analyze retrieval quality with Arize Phoenix.

**Deliverables:**
- `src/evaluate.py` script
- Phoenix dashboard or evaluation notebook

---

### 🗓️ **Phase 6 — Interface and Final Delivery (Sunday)**
**Goal:** Create a Streamlit app and finalize project documentation.

**Deliverables:**
- `src/app.py` — minimal Streamlit chat
- Updated README with setup instructions
- Short screencast video (demo run)

---

## 🧠 Example Interaction

**User:**  
> Tengo un Pikachu y quiero enfrentar a un Squirtle. ¿Qué estrategia recomiendas?

**Assistant:**  
> Squirtle es de tipo agua, débil frente a ataques eléctricos. Pikachu es una excelente opción: usa *Impactrueno* o *Electro Ball*.  
> Consejo del entrenador: prioriza la velocidad para atacar primero.

---

## 🧰 Suggested Requirements

```txt
qdrant-client==1.10.0
fastembed==0.3.0
openai==1.51.0
streamlit==1.39.0
pandas==2.2.2
python-dotenv==1.0.1
arize-phoenix==0.13.0
neo4j==5.19.0
dlt==0.5.4
````

---

## 🧱 Evaluation Targets (Zoomcamp Rubric)

| Criterion            | Implementation Plan                        | Points |
| -------------------- | ------------------------------------------ | ------ |
| Problem description  | Clear Pokémon strategy context             | 2      |
| Retrieval flow       | Qdrant + GPT-4o-mini RAG pipeline          | 2      |
| Retrieval evaluation | Compare BM25 vs vector, analyze in Phoenix | 2      |
| LLM evaluation       | Two prompts (coach vs technical)           | 2      |
| Interface            | Streamlit app                              | 2      |
| Ingestion pipeline   | Automated with dlt                         | 2      |
| Monitoring           | Phoenix dashboard or feedback              | 2      |
| Containerization     | Optional Docker setup                      | 1–2    |
| Reproducibility      | Easy setup + accessible data               | 2      |
| Best practices       | Hybrid retrieval or graph enrichment       | +1     |
| **Total Expected**   | **18–19 points (passing + bonus)**         |        |

---

## 🧭 Execution Philosophy

* Prioritize **functionality over complexity**.
* Focus on **RAG pipeline completeness** (ingestion → retrieval → generation).
* Use **mock or minimal datasets** when needed.
* Delay polishing and UI aesthetics until the end.
* If short on time: make Neo4j optional (graph mock with NetworkX is acceptable).

---

## 📌 Next Step

**Start Phase 1 now:**

* Create repository.
* Add this guide as `README.md`.
* Implement `ingest_pokeapi_dlt.py` and verify Pokédex ingestion with `dlt`.

---

*Prepared October 2025 — Project guide for the LLM Zoomcamp final submission by MaxKaizo.*
