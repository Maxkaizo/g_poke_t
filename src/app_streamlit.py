# src/app_streamlit.py
import os
from datetime import datetime
import streamlit as st
from qdrant_client import QdrantClient

# ─────────────────────────────────────────────
# Project imports
# ─────────────────────────────────────────────
from intent_router import IntentRouter
from hybrid_search_qdrant import hybrid_rrf_search
from generate_answer import generate_answer
# from mongo_query import query_mongo
# from graph_query import query_neo4j

# ─────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Pokémon RAG Assistant",
    page_icon="🧬",
    layout="wide"
)

# ─────────────────────────────────────────────
# FIX INPUT FIELD AT THE BOTTOM
# ─────────────────────────────────────────────
st.markdown(
    """
    <style>
    /* Keep chat input fixed at bottom */
    .stChatInput {
        position: fixed;
        bottom: 1rem;
        left: 0;
        right: 0;
        background-color: var(--background-color);
        padding: 0.5rem 1rem;
        z-index: 100;
        border-top: 1px solid rgba(250, 250, 250, 0.1);
    }
    /* Add bottom padding so messages are not hidden behind the input */
    .stChatMessageContainer {
        padding-bottom: 6rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ─────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────
st.title("🧬 Pokémon RAG Assistant — Multi-Source Retrieval")
st.caption("LLM-driven intent routing across Qdrant (semantic), MongoDB (factual), and Neo4j (graph).")

# ─────────────────────────────────────────────
# SESSION STATE INIT
# ─────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state["messages"] = []
if "router_log" not in st.session_state:
    st.session_state["router_log"] = []
if "last_query" not in st.session_state:
    st.session_state["last_query"] = None

# ─────────────────────────────────────────────
# QDRANT CLIENT
# ─────────────────────────────────────────────
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY", "pokedex-key")
QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION", "pokedex_hybrid")

try:
    qdrant_client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)
except Exception as e:
    st.error(f"❌ Could not connect to Qdrant: {e}")
    st.stop()

# ─────────────────────────────────────────────
# INTENT ROUTER
# ─────────────────────────────────────────────
router = IntentRouter()

# ─────────────────────────────────────────────
# LAYOUT: TABS
# ─────────────────────────────────────────────
tab_chat, tab_debug = st.tabs(["💬 Chat", "🧠 Debug"])

# ─────────────────────────────────────────────
# TAB 1 — REAL CHAT
# ─────────────────────────────────────────────
with tab_chat:
    st.subheader("Chat with the Pokémon Assistant")

    # Show previous conversation
    for msg in st.session_state["messages"]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

# ─────────────────────────────────────────────
# CHAT INPUT (fixed at bottom)
# ─────────────────────────────────────────────
if user_query := st.chat_input("Ask something about Pokémon..."):
    # Save user message
    st.session_state["messages"].append(
        {"role": "user", "content": user_query, "time": datetime.now().isoformat()}
    )
    with tab_chat:
        with st.chat_message("user"):
            st.markdown(user_query)

        with st.chat_message("assistant"):
            placeholder = st.empty()
            try:
                placeholder.markdown("🧠 **Step 1/4 — Analyzing intents...**")
                intents = router.extract_intents(user_query)
                st.session_state["router_log"].append(router.history[-1])

                placeholder.markdown("📚 **Step 2/4 — Querying Qdrant (semantic search)...**")
                semantic_results = hybrid_rrf_search(
                    client=qdrant_client,
                    query=user_query,
                    limit=3
                )

                placeholder.markdown("📄 **Step 3/4 — Fetching factual & graph data...**")
                factual_results = []  # query_mongo(intents)
                graph_results = []    # query_neo4j(intents)

                placeholder.markdown("🤖 **Step 4/4 — Generating final answer...**")
                final_answer = generate_answer(
                    user_query,
                    semantic_results=semantic_results,
                    factual_docs=factual_results,
                    graph_relations=graph_results,
                )

                placeholder.markdown(final_answer)  # replace progress with final answer
                st.session_state["messages"].append(
                    {"role": "assistant", "content": final_answer, "time": datetime.now().isoformat()}
                )

                st.session_state["last_query"] = {
                    "query": user_query,
                    "intents": intents,
                    "semantic": semantic_results,
                    "factual": factual_results,
                    "graph": graph_results,
                    "answer": final_answer,
                }

            except Exception as e:
                placeholder.markdown(f"❌ **Error:** {e}")

# ─────────────────────────────────────────────
# TAB 2 — DEBUG MODE
# ─────────────────────────────────────────────
with tab_debug:
    st.subheader("🔍 Debug Details")

    if st.session_state["last_query"]:
        last = st.session_state["last_query"]

        with st.expander("🧭 Intent Router Output", expanded=False):
            st.json(last["intents"])

        with st.expander("📚 Semantic Search (Qdrant)", expanded=False):
            for r in last["semantic"]:
                payload = getattr(r, "payload", None) or {}
                snippet = payload.get("text", "")[:250].replace("\n", " ")
                st.markdown(f"- **{payload.get('document_name', '?')}** — *{payload.get('section_name', '')}*")
                st.caption(snippet)

        with st.expander("📄 Factual Results (MongoDB)", expanded=False):
            if last["factual"]:
                st.json(last["factual"])
            else:
                st.info("No factual results returned.")

        with st.expander("🔗 Graph Results (Neo4j)", expanded=False):
            if last["graph"]:
                st.json(last["graph"])
            else:
                st.info("No graph results returned.")

        with st.expander("🧠 Final Answer", expanded=True):
            st.write(last["answer"])
    else:
        st.info("Run a chat first to see debug information.")
