import dlt
import requests
import pandas as pd
from tqdm import tqdm

# ────────────────────────────────────────────────
#  Helpers
# ────────────────────────────────────────────────

def get_species_data(pokemon_id: int):
    """Obtiene especie y descripción (flavor text)."""
    try:
        species = requests.get(f"https://pokeapi.co/api/v2/pokemon-species/{pokemon_id}/").json()
        description = next(
            (entry["flavor_text"].replace("\n", " ").replace("\f", " ")
             for entry in species["flavor_text_entries"]
             if entry["language"]["name"] == "en"),
            None
        )
        evo_url = species.get("evolution_chain", {}).get("url")
        return description, evo_url
    except Exception:
        return None, None


def get_evolution_pairs(evo_url: str):
    """Devuelve pares (source, target) de una cadena evolutiva."""
    if not evo_url:
        return []

    evo_data = requests.get(evo_url).json()
    pairs = []

    def traverse(node):
        species_name = node["species"]["name"]
        for evolution in node["evolves_to"]:
            evo_name = evolution["species"]["name"]
            pairs.append((species_name, evo_name))
            traverse(evolution)

    traverse(evo_data["chain"])
    return pairs


# ────────────────────────────────────────────────
#  dlt resource
# ────────────────────────────────────────────────

@dlt.resource(name="pokedex", write_disposition="replace")
def pokeapi_resource(limit_per_page: int = 100):
    base_url = f"https://pokeapi.co/api/v2/pokemon?limit={limit_per_page}&offset=0"
    all_pairs = []

    while base_url:
        resp = requests.get(base_url).json()

        for entry in tqdm(resp["results"], desc="Fetching Pokémon batch"):
            pokemon = requests.get(entry["url"]).json()
            desc, evo_url = get_species_data(pokemon["id"])
            pairs = get_evolution_pairs(evo_url)
            all_pairs.extend(pairs)

            # ─────────────── Flatten ────────────────
            types = [t["type"]["name"] for t in pokemon["types"]]
            abilities = [a["ability"]["name"] for a in pokemon["abilities"]]
            stats = {s["stat"]["name"]: s["base_stat"] for s in pokemon["stats"]}

            yield {
                "id": pokemon["id"],
                "name": pokemon["name"],
                "type_primary": types[0] if len(types) > 0 else None,
                "type_secondary": types[1] if len(types) > 1 else None,
                "abilities": ", ".join(abilities),
                "height": pokemon["height"],
                "weight": pokemon["weight"],
                "hp": stats.get("hp"),
                "attack": stats.get("attack"),
                "defense": stats.get("defense"),
                "speed": stats.get("speed"),
                "special_attack": stats.get("special-attack"),
                "special_defense": stats.get("special-defense"),
                "description": desc,
            }

        base_url = resp.get("next")

    # Guardar evoluciones
    df_evo = pd.DataFrame(all_pairs, columns=["source", "target"]).drop_duplicates()
    df_evo.to_csv("data/processed/evolutions.csv", index=False)
    print(f"✅ Evolution pairs exported: {len(df_evo)} relations")


@dlt.source(name="pokeapi")
def pokeapi_source():
    return pokeapi_resource()


# ────────────────────────────────────────────────
#  Pipeline execution
# ────────────────────────────────────────────────

if __name__ == "__main__":
    pipeline = dlt.pipeline(
        pipeline_name="pokedex_pipeline",
        destination=dlt.destinations.filesystem(bucket_url="data/processed"),
        dataset_name="pokedex_data"
    )

    load_info = pipeline.run(pokeapi_source())
    print(load_info)

    # Export consolidado (flattened)
    df = pd.DataFrame(list(pokeapi_resource()))
    df.to_csv("data/processed/pokedex_full.csv", index=False)
    print(f"✅ Pokédex exported: {len(df)} entries → data/processed/pokedex_full.csv")
