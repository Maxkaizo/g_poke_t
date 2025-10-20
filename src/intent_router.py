"""
intent_router.py
────────────────────────────────────────────
LLM-powered multi-intent router for Pokémon RAG system.
────────────────────────────────────────────
"""

import os
import re
import json
import time
from datetime import datetime, timezone
from dotenv import load_dotenv, find_dotenv
from openai import OpenAI

# ─────────────────────────────────────────────
# Load environment variables
# ─────────────────────────────────────────────
load_dotenv(find_dotenv())
API_KEY = os.getenv("OPENAI_API_KEY")
if not API_KEY:
    raise ValueError("❌ Missing OPENAI_API_KEY in your environment")

# ─────────────────────────────────────────────
# Prompt template
# ─────────────────────────────────────────────
INTENT_PROMPT = """
You are an intent extraction assistant for a Pokémon knowledge system.

Your task is to analyze the user's question (which may be written in English or Spanish)
and extract *all* distinct intents it expresses.

Each intent must specify:
- The **intent type**: one of ["semantic", "factual", "relational"].
- The **main entity** (Pokémon name, type group, or None).
- The **attributes or relation keywords** in English, matching the database schema.
- A **confidence** score between 0 and 1.

Always return the JSON **in English**, regardless of the language of the question.

Definition of intent types:
- "factual": direct questions about static data or properties (type, stats, abilities, category).
- "relational": questions about links or relationships between entities (e.g., evolutions, strengths, weaknesses, comparisons).
- "semantic": conceptual or reasoning questions (why, explain, compare in general terms).

Use the following schema for attributes:
{{
  "type": "Pokémon type or element (e.g., 'Fire', 'Water')",
  "evolves_to": "Evolution target Pokémon",
  "evolves_from": "Previous evolution",
  "strong_against": "Types this Pokémon is strong against",
  "weak_against": "Types this Pokémon is weak against",
  "ability": "Pokémon abilities",
  "stat": "Numeric attributes like HP, Attack, Defense, Speed",
  "category": "General classification (e.g., Legendary, Mythical)",
  "relation": "Generic relational property between entities"
}}

Return the result strictly following this format:

{{
  "query": "...",
  "intents": [
    {{
      "type": "factual | relational | semantic",
      "entity": "Eevee",
      "attributes": ["evolves_to"],
      "confidence": 0.9
    }}
  ]
}}

If the question includes multiple topics (e.g., two Pokémon or multiple relations), 
return one intent per distinct topic.
Never include explanations, comments, or text outside the JSON.
User question: "{question}"
""".strip()


# ─────────────────────────────────────────────
# Intent Router Class
# ─────────────────────────────────────────────
class IntentRouter:
    def __init__(self, model: str = "gpt-4o-mini", temperature: float = 0.0, max_retries: int = 2):
        self.client = OpenAI(api_key=API_KEY)
        self.model = model
        self.temperature = temperature
        self.max_retries = max_retries
        self.history = []

    def _call_llm(self, prompt: str) -> str:
        """Make a chat completion call to the LLM."""
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=self.temperature,
        )
        return response.choices[0].message.content

    def _validate_json(self, text: str) -> dict | None:
        """Validate and parse JSON response safely."""
        if not text:
            return None

        try:
            return json.loads(text)
        except json.JSONDecodeError:
            # Auto-clean common LLM artifacts
            cleaned = text.strip()

            # Remove any non-JSON preamble
            match = re.search(r'({.*})', cleaned, re.DOTALL)
            if match:
                cleaned = match.group(1)

            # Replace Python-style None/True/False with JSON equivalents
            cleaned = (
                cleaned.replace("None", "null")
                       .replace("True", "true")
                       .replace("False", "false")
            )

            try:
                return json.loads(cleaned)
            except Exception:
                return None

    def extract_intents(self, query: str) -> dict:
        """Extract multiple intents from a user's query."""
        prompt = INTENT_PROMPT.format(question=query)
        start_time = time.time()
        parsed = None
        response_text = None

        # Retry loop for malformed JSON
        for attempt in range(self.max_retries):
            response_text = self._call_llm(prompt)
            parsed = self._validate_json(response_text)
            if parsed:
                break
            # Try a JSON-only fix pass
            fix_prompt = f"Return only valid JSON, fixing the following:\n\n{response_text}"
            response_text = self._call_llm(fix_prompt)
            parsed = self._validate_json(response_text)
            if parsed:
                break

        elapsed = round(time.time() - start_time, 3)
        success = parsed is not None

        log_entry = {
            "query": query,
            "response_raw": response_text,
            "parsed": parsed,
            "success": success,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "elapsed_sec": elapsed,
            "attempts": attempt + 1,
        }
        self.history.append(log_entry)

        if not success:
            raise ValueError(f"❌ Failed to produce valid JSON after {self.max_retries} attempts.\nRaw response:\n{response_text}")

        return parsed


# ─────────────────────────────────────────────
# Example usage
# ─────────────────────────────────────────────
if __name__ == "__main__":
    router = IntentRouter()
    query = "How does Eevee evolve and what type is Vaporeon?"
    print(f"🔍 Query: {query}\n")
    result = router.extract_intents(query)
    print(json.dumps(result, indent=2, ensure_ascii=False))
