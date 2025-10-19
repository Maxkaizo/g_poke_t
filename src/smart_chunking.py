import os
import json
from dotenv import load_dotenv, find_dotenv
from openai import OpenAI
from tqdm import tqdm

# ───────────────────────────────
# CONFIGURACIÓN
# ───────────────────────────────
load_dotenv(find_dotenv())

API_KEY = os.getenv("OPENAI_API_KEY")
if not API_KEY:
    raise ValueError("❌ Falta la variable OPENAI_API_KEY en tu archivo .env")

openai_client = OpenAI(api_key=API_KEY)

INPUT_DIR = "data/clean_texts"
OUTPUT_DIR = "data/chunks"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ───────────────────────────────
# PROMPT BASE
# ───────────────────────────────
PROMPT_TEMPLATE = """
You are a text analysis assistant.

Split the provided document into meaningful, logically consistent sections
for use in a question-answering or retrieval system.

Each section should:
- Cover one specific topic or idea.
- Be self-contained and coherent.
- Retain all relevant details (no summaries).
- Be clearly separated using '---' between sections.

<DOCUMENT>
{document}
</DOCUMENT>

Return the result using this format:

## Section Name

Section content...

---

## Another Section Name

Another section content...

---
""".strip()


def llm(prompt, model="gpt-4o-mini"):
    """Wrapper para llamada al modelo LLM."""
    response = openai_client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
    )
    return response.choices[0].message.content


def intelligent_chunking(text, prompt_template=PROMPT_TEMPLATE):
    """Divide un texto en secciones temáticas usando LLM."""
    prompt = prompt_template.format(document=text[:15000])  # limitar por tokens
    response = llm(prompt)
    sections = response.split("---")
    return [s.strip() for s in sections if s.strip()]


# ───────────────────────────────
# MAIN
# ───────────────────────────────
if __name__ == "__main__":
    print("🧠 Iniciando chunking inteligente...")
    input_files = [f for f in os.listdir(INPUT_DIR) if f.endswith(".txt")]

    for file in tqdm(input_files, desc="Procesando documentos"):
        file_path = os.path.join(INPUT_DIR, file)

        with open(file_path, "r", encoding="utf-8") as f:
            text = f.read()

        chunks = intelligent_chunking(text)

        output_path = os.path.join(OUTPUT_DIR, file.replace(".txt", ".jsonl"))
        with open(output_path, "w", encoding="utf-8") as f:
            for i, chunk in enumerate(chunks, 1):
                record = {
                    "id": f"{file.replace('.txt', '')}_chunk_{i}",
                    "text": chunk,
                    "source": file,
                }
                f.write(json.dumps(record, ensure_ascii=False) + "\n")

        print(f"✅ {len(chunks)} chunks generados → {output_path}")

    print("\n🏁 Chunking finalizado correctamente.")
