import os
import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from tqdm import tqdm

# ───────────────────────────────
# CONFIG
# ───────────────────────────────
URLS = [
    "https://www.dragonflycave.com/mechanics/battling-basics",
    "https://bulbapedia.bulbagarden.net/wiki/Trainer_Tips",
    "https://www.puiching.blog/puichinggazette/beginner-pokmon-trainer-guide",
]

OUT_DIR = "data/clean_texts"
os.makedirs(OUT_DIR, exist_ok=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; DataCollector/1.0; +https://github.com/Maxkaizo)"
}

EXCLUDE_KEYWORDS = [
    "navigation", "privacy", "disclaimer", "cookie", "about",
    "login", "help", "license", "site map", "main page",
    "contact", "search", "jump to", "policy"
]

# ───────────────────────────────
# FUNCIONES AUXILIARES
# ───────────────────────────────
def slugify(url):
    """Convierte la URL en un nombre de archivo válido."""
    parsed = urlparse(url)
    slug = parsed.netloc.replace(".", "_") + parsed.path.replace("/", "_").strip("_")
    return slug or "page"

def fetch_html(url):
    """Descarga el HTML de una página con manejo básico de errores."""
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        r.raise_for_status()
        return r.text
    except Exception as e:
        print(f"⚠️ Error al descargar {url}: {e}")
        return None

def extract_text(html):
    """Extrae texto visible y limpia ruido común."""
    soup = BeautifulSoup(html, "html.parser")
    body = soup.body
    if not body:
        return ""

    texts = []
    for tag in body.find_all(["h1", "h2", "h3", "p", "ul", "ol", "li"]):
        txt = tag.get_text(" ", strip=True)
        if txt:
            texts.append(txt)

    # Limpieza: eliminar líneas cortas o irrelevantes
    lines = [ln.strip() for ln in texts if len(ln.strip().split()) > 2]

    # Filtros por palabra clave (evita menús, pies de página, etc.)
    lines = [
        ln for ln in lines
        if not any(k in ln.lower() for k in EXCLUDE_KEYWORDS)
    ]

    # Quitar duplicados
    seen = set()
    cleaned = []
    for ln in lines:
        if ln not in seen:
            cleaned.append(ln)
            seen.add(ln)

    return "\n".join(cleaned)

# ───────────────────────────────
# MAIN
# ───────────────────────────────
if __name__ == "__main__":
    print("🚀 Iniciando scraping...")
    for url in tqdm(URLS, desc="Descargando páginas"):
        html = fetch_html(url)
        if not html:
            continue

        text = extract_text(html)
        if not text or len(text.split()) < 50:
            print(f"⚠️ {url} parece tener poco contenido, revisar manualmente.")
            continue

        filename = slugify(url) + ".txt"
        out_path = os.path.join(OUT_DIR, filename)

        with open(out_path, "w", encoding="utf-8") as f:
            f.write(text)

        print(f"✅ Guardado: {out_path}")
        time.sleep(2)  # Evita sobrecargar los servidores

    print("\n🏁 Scraping finalizado correctamente.")
