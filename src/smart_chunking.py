import os
import re
import json
import uuid
from dotenv import load_dotenv, find_dotenv
from openai import OpenAI
from tqdm import tqdm

# ───────────────────────────────
# CONFIGURACIÓN
# ───────────────────────────────
load_dotenv(find_dotenv())

API_KEY = os.getenv("OPENAI_API_KEY")
if not API_KEY:
    raise ValueError("❌ Missing OPENAI_API_KEY in .env file")

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

Use the following format **exactly**:

<## Section Name##>
Section content...

---

<## Another Section Name##>
Section content...

---

<DOCUMENT>
{document}
</DOCUMENT>
""".strip()


def llm(prompt, model="gpt-4o-mini"):
    """Wrapper for OpenAI chat completion call."""
    response = openai_client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
    )
    return response.choices[0].message.content


def intelligent_chunking(text, prompt_template=PROMPT_TEMPLATE):
    """Split a text into thematic sections using an LLM."""
    prompt = prompt_template.format(document=text[:15000])  # avoid overlength
    response = llm(prompt)

    # Split by delimiter "---"
    sections = [s.strip() for s in response.split("---") if s.strip()]
    return sections


def parse_section(section_text):
    """
    Extract section_name and content from the LLM response chunk.
    Expected pattern: <## Section Name##> followed by text.
    """
    match = re.match(r"<##\s*(.*?)\s*##>\s*(.*)", section_text, re.DOTALL)
    if match:
        section_name = match.group(1).strip()
        content = match.group(2).strip()
    else:
        section_name = "Untitled"
        content = section_text.strip()
    return section_name, content


# ───────────────────────────────
# MAIN
# ───────────────────────────────
if __name__ == "__main__":
    print("🧠 Starting intelligent chunking...")
    input_files = [f for f in os.listdir(INPUT_DIR) if f.endswith(".txt")]

    for file in tqdm(input_files, desc="Processing documents"):
        file_path = os.path.join(INPUT_DIR, file)

        with open(file_path, "r", encoding="utf-8") as f:
            text = f.read()

        # Generate sections via LLM
        sections = intelligent_chunking(text)

        output_path = os.path.join(OUTPUT_DIR, file.replace(".txt", ".jsonl"))
        with open(output_path, "w", encoding="utf-8") as f_out:
            for i, section in enumerate(sections, 1):
                section_name, content = parse_section(section)

                record = {
                    "chunk_id": str(uuid.uuid4()),
                    "document_name": file.replace(".txt", ".md"),
                    "chunk_index": i,
                    "section_name": section_name,
                    "text": content,
                }

                f_out.write(json.dumps(record, ensure_ascii=False) + "\n")

        print(f"✅ {len(sections)} chunks generated → {output_path}")

    print("\n🏁 Chunking completed successfully.")
