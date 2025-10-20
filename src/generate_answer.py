# src/generate_answer.py
import os
from openai import OpenAI
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())
API_KEY = os.getenv("OPENAI_API_KEY")

if not API_KEY:
    raise ValueError("Missing OPENAI_API_KEY")

client = OpenAI(api_key=API_KEY)

def generate_answer(user_query: str, semantic_results=None, factual_docs=None, graph_relations=None, model="gpt-4o-mini"):
    """Generate a final answer using multi-source context."""

    # Convert contexts into readable snippets
    def join_snippets(items, key="text", n=3):
        if not items:
            return "No data available."
        if isinstance(items[0], dict):
            return "\n".join(f"- {it.get(key, str(it))[:300]}" for it in items[:n])
        return "\n".join(f"- {str(it)[:300]}" for it in items[:n])

    context_text = f"""
User question: {user_query}

Semantic context (Qdrant):
{join_snippets(semantic_results)}

Factual context (MongoDB):
{join_snippets(factual_docs)}

Relational context (Neo4j):
{join_snippets(graph_relations)}

Respond clearly and in a friendly explanatory tone.
If some parts of the answer are uncertain, say so briefly.
"""

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "You are a knowledgeable Pokémon assistant."},
            {"role": "user", "content": context_text},
        ],
        temperature=0.4,
    )

    return response.choices[0].message.content.strip()
