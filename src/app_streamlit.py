"""
app_streamlit.py
────────────────────────────────────────────
Stage 1: Streamlit UI for intent routing demo.
────────────────────────────────────────────
"""

import json
import streamlit as st
from intent_router import IntentRouter

# ─────────────────────────────────────────────
# Page configuration
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Pokémon RAG Assistant (Intent Router Demo)",
    page_icon="🧠",
    layout="wide"
)

st.title("Pokémon RAG Assistant — Stage 1 🧭")
st.caption("Interactive demo of the multi-intent router powered by LLMs")

# ─────────────────────────────────────────────
# Sidebar configuration
# ─────────────────────────────────────────────
st.sidebar.header("⚙️ Configuration")
model = st.sidebar.selectbox("Model", ["gpt-4o-mini"], index=0)
temperature = st.sidebar.slider("Temperature", 0.0, 1.0, 0.0, 0.1)

# Initialize router
router = IntentRouter(model=model, temperature=temperature)

# ─────────────────────────────────────────────
# Main input
# ─────────────────────────────────────────────
query = st.text_area("Ask a question about Pokémon:", height=100, placeholder="e.g., How does Eevee evolve and what type is Vaporeon?")


if st.button("Analyze Intents 🧠", use_container_width=True):
    if not query.strip():
        st.warning("Please enter a question first.")
    else:
        with st.spinner("Analyzing..."):
            try:
                result = router.extract_intents(query)
                st.success("✅ Intents extracted successfully!")

                # Show parsed JSON
                st.subheader("📘 Parsed Intents")
                st.json(result, expanded=True)

                # Optional: show log info
                st.subheader("🧾 Router Log")
                log_entry = router.history[-1]
                st.code(json.dumps(log_entry, indent=2, ensure_ascii=False), language="json")

            except Exception as e:
                st.error(f"Error: {e}")

# ─────────────────────────────────────────────
# Footer
# ─────────────────────────────────────────────
st.markdown("---")
st.caption("Stage 1 of Pokémon RAG Assistant — Intent detection only (no retrieval yet)")
