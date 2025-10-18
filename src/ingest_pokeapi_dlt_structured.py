import os
import time
import random
import requests
import pandas as pd
from tqdm import tqdm
import dlt


# ╔════════════════════════════════════════════════════════════╗
# ║                     HELPER FUNCTIONS                       ║
# ╚════════════════════════════════════════════════════════════╝

def safe_get_json(url: str, retries: int = 5, backoff_factor: float = 1.5):
    """Request con reintentos y control de errores (maneja 429, 5xx, timeouts)."""
    for attempt in range(retries):
        try:
            resp = requests.get(url, timeout=10)
            if resp.status_code == 200:
                return resp.json()
            elif resp.status_code in (429, 500, 502, 503, 504):
                wait = backoff_factor ** attempt + random.random()
                print(f"⚠️ {resp.status_code} en {url}, reintentando en {wait:.1f}s...")
                time.sleep(wait)
            else:
                print(f"❌ Error {resp.status_code} en {url}")
                return None
        except requests.exceptions.RequestException as e:
            wait = backoff_factor ** attempt + random.random()
            print(f"⚠️ Excepción {e}, reintentando en {wait:.1f}s...")
            time.sleep(wait)

    print(f"❌ Falló definitivamente: {url}")
    return None


def get_species_data(pokemon_id: int, species_url: str = None) -> dict:
    """Obtiene descripción, generación y URL de cadena evolutiva.
    Usa species_url como fallback para variantes con IDs especiales (>=10000)."""
    url = species_url or f"https://pokeapi.co/api/v2/pokemon-species/{pokemon_id}/"
    species = safe_get_json(url)
    if not species:
        return {"description": None, "generation": None, "evolution_chain_url": None}

    description = next(
        (
            entry["flavor_text"].replace("\n", " ").replace("\f", " ")
            for entry in species.get("flavor_text_entries", [])
            if entry.get("language", {}).get("name") == "en"
        ),
        None,
    )
    return {
        "description": description,
        "generation": species.get("generation", {}).get("name"),
        "evolution_chain_url": species.get("evolution_chain", {}).get("url"),
    }


def get_evolution_pairs(evo_url: str) -> list[tuple[str, str]]:
    """Devuelve pares (source, target) de una cadena evolutiva."""
    if not evo_url:
        return []

    evo_data = safe_get_json(evo_url)
    if not evo_data:
        return []

    pairs = []

    def traverse(node):
        src = node["species"]["name"]
        for nxt in node.get("evolves_to", []):
            dst = nxt["species"]["name"]
            pairs.append((src, dst))
            traverse(nxt)

    traverse(evo_data["chain"])
    return pairs


def get_type_relations() -> list[dict]:
    """Tabla de ventajas/desventajas entre tipos (para GraphRAG)."""
    relations = []
    types_list = safe_get_json("https://pokeapi.co/api/v2/type/")
    if not types_list:
        return relations

    for t in tqdm(types_list.get("results", []), desc="Fetching type relations"):
        tdata = safe_get_json(t["url"])
        if not tdata:
            continue

        name = tdata["name"]
        dr = tdata.get("damage_relations", {})

        for rel in dr.get("double_damage_to", []):
            relations.append({"source": name, "relation": "STRONG_AGAINST", "target": rel["name"]})
        for rel in dr.get("double_damage_from", []):
            relations.append({"source": name, "relation": "WEAK_AGAINST", "target": rel["name"]})

    return relations


# ╔════════════════════════════════════════════════════════════╗
# ║                 GUARDADO DE BATCHES EN DISCO               ║
# ╚════════════════════════════════════════════════════════════╝

def save_partial_batch(records: list, evo_pairs: list, batch_number: int):
    """Guarda los datos de un batch a disco (CSV y JSONL)."""
    os.makedirs("data/structured/batches", exist_ok=True)
    csv_path = f"data/structured/batches/pokedex_batch_{batch_number:03}.csv"
    evo_path = f"data/structured/batches/evolutions_batch_{batch_number:03}.csv"

    df = pd.DataFrame(records)
    df.to_csv(csv_path, index=False)
    if evo_pairs:
        pd.DataFrame(sorted(set(evo_pairs)), columns=["source", "target"]).to_csv(evo_path, index=False)

    print(f"💾 Guardado: {csv_path} ({len(df)} Pokémon) — {len(evo_pairs)} evoluciones.")


# ╔════════════════════════════════════════════════════════════╗
# ║                     DLT RESOURCE                           ║
# ╚════════════════════════════════════════════════════════════╝

@dlt.resource(name="pokedex_structured", write_disposition="append")
def pokeapi_resource(limit_per_page: int = 100, start_offset: int = 0, save_every: int = 100):
    """
    Genera Pokémon desde la PokéAPI y guarda cada batch localmente.
    - limit_per_page: número de Pokémon por request.
    - start_offset: desde qué offset continuar.
    - save_every: número de Pokémon antes de guardar un archivo temporal.
    """

    base_url = f"https://pokeapi.co/api/v2/pokemon?limit={limit_per_page}&offset={start_offset}"
    all_records = []
    all_pairs = []
    batch_counter = start_offset // limit_per_page + 1

    while base_url:
        resp = safe_get_json(base_url)
        if not resp:
            print(f"⚠️ No se pudo obtener {base_url}, deteniendo paginación.")
            break

        for entry in tqdm(resp.get("results", []), desc=f"Fetching Pokémon batch {batch_counter}"):
            pokemon = safe_get_json(entry["url"])
            if not pokemon:
                continue

            # ✅ Fallback para variantes (usa species_url en lugar de id directo)
            species_data = get_species_data(pokemon["id"], pokemon["species"]["url"])
            evo_url = species_data.get("evolution_chain_url")
            all_pairs.extend(get_evolution_pairs(evo_url))

            all_records.append({
                "id": pokemon["id"],
                "name": pokemon["name"],
                "species_name": pokemon["species"]["name"],
                "types": pokemon["types"],
                "abilities": pokemon["abilities"],
                "stats": pokemon["stats"],
                "height": pokemon["height"],
                "weight": pokemon["weight"],
                "species": species_data,
            })

            # Guardar cada cierto número de Pokémon
            if len(all_records) >= save_every:
                save_partial_batch(all_records, all_pairs, batch_counter)
                all_records.clear()
                all_pairs.clear()
                batch_counter += 1

        base_url = resp.get("next")

    # Guardar lo que quede al final
    if all_records:
        save_partial_batch(all_records, all_pairs, batch_counter)
    
    yield from []


@dlt.source(name="pokeapi_structured")
def pokeapi_source(limit_per_page=100, start_offset=0, save_every=100):
    return pokeapi_resource(limit_per_page=limit_per_page, start_offset=start_offset, save_every=save_every)


# ╔════════════════════════════════════════════════════════════╗
# ║                     MAIN PIPELINE                          ║
# ╚════════════════════════════════════════════════════════════╝

if __name__ == "__main__":
    os.makedirs("data/structured", exist_ok=True)

    pipeline = dlt.pipeline(
        pipeline_name="pokedex_structured_pipeline",
        destination=dlt.destinations.filesystem(bucket_url="data/structured"),
        dataset_name="pokedex_structured",
    )

    print("🚀 Iniciando pipeline de ingesta de PokéAPI (estructurada)...")

    # Puedes ajustar estos valores para pruebas o reanudación:
    load_info = pipeline.run(pokeapi_source(limit_per_page=100, start_offset=0, save_every=100))
    print(load_info)

    # Exportar relaciones de tipos (una sola vez al final)
    type_relations = get_type_relations()
    if type_relations:
        pd.DataFrame(type_relations).to_csv("data/structured/type_relations.csv", index=False)
        print(f"✅ Saved data/structured/type_relations.csv ({len(type_relations)} relaciones)")
    else:
        print("⚠️ No se pudieron obtener relaciones de tipos.")
