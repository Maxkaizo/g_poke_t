# ======================================================
# 🧬 Pokémon RAG System — Makefile (uv-based)
# ======================================================

SHELL := /bin/bash

# ─────────────────────────────────────────────
# Configuración
# ─────────────────────────────────────────────
PYTHON := uv run python
STREAMLIT := uv run streamlit run
APP := src/app_streamlit.py

# ─────────────────────────────────────────────
# Targets
# ─────────────────────────────────────────────

.PHONY: help setup run clean

help:
	@echo ""
	@echo "🧩 Available commands:"
	@echo "  make setup     → Run full ingestion, normalization, and indexing pipeline"
	@echo "  make run       → Launch Streamlit RAG Orchestrator"
	@echo "  make clean     → Remove generated cache files"
	@echo ""

# ─────────────────────────────────────────────
# Full pipeline setup
# ─────────────────────────────────────────────
setup:
	@echo ""
	@echo "🚀 [1/8] Ingesting structured data from PokéAPI..."
	$(PYTHON) src/ingest_pokeapi_dlt_structured.py

	@echo "📦 [2/8] Consolidating Pokedex batches..."
	$(PYTHON) src/consolidate_pokedex_batches.py

	@echo "🧮 [3/8] Loading data into MongoDB..."
	$(PYTHON) src/load_to_mongo.py

	@echo "🧹 [4/8] Normalizing Mongo data..."
	$(PYTHON) src/normalize_mongo_data.py

	@echo "🕸 [5/8] Building graph CSVs from Mongo..."
	$(PYTHON) src/build_graph_from_mongo.py

	@echo "🔗 [6/8] Loading data into Neo4j..."
	$(PYTHON) src/load_to_neo4j.py

	@echo "✂️ [7/8] Performing smart chunking (LLM-based)..."
	$(PYTHON) src/smart_chunking.py

	@echo "📚 [8/8] Indexing chunks into Qdrant..."
	$(PYTHON) src/hybrid_index_qdrant.py

	@echo ""
	@echo "✅ Setup complete! All data loaded and indexed."
	@echo ""

# ─────────────────────────────────────────────
# Run Streamlit app
# ─────────────────────────────────────────────
run:
	@echo ""
	@echo "💬 Starting Pokémon RAG Orchestrator..."
	$(STREAMLIT) $(APP)

# ─────────────────────────────────────────────
# Clean temp files
# ─────────────────────────────────────────────
clean:
	@echo "🧹 Cleaning cache and temporary files..."
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	@echo "✅ Clean complete!"
