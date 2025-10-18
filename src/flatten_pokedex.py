import pandas as pd
import ast
from pathlib import Path

def safe_eval(val):
    """Convierte strings tipo lista/dict en estructuras Python seguras."""
    try:
        return ast.literal_eval(val) if isinstance(val, str) else val
    except Exception:
        return None

def extract_types(tlist):
    if isinstance(tlist, list):
        return ", ".join(t["type"]["name"] for t in tlist if "type" in t)
    return None

def extract_abilities(alist):
    if isinstance(alist, list):
        return ", ".join(a["ability"]["name"] for a in alist if "ability" in a)
    return None

def extract_stat(stats, name):
    if isinstance(stats, list):
        for s in stats:
            if s.get("stat", {}).get("name") == name:
                return s.get("base_stat")
    return None

def extract_species_field(sdict, key):
    if isinstance(sdict, dict):
        return sdict.get(key)
    return None

def flatten_pokedex(input_path="data/structured/consolidated/pokedex_full.csv"):
    print("🔄 Cargando dataset completo...")
    df = pd.read_csv(input_path)

    print("🧩 Transformando columnas JSON...")
    for col in ["types", "abilities", "stats", "species"]:
        df[col] = df[col].apply(safe_eval)

    print("✨ Extrayendo columnas derivadas...")
    df["type_names"] = df["types"].apply(extract_types)
    df["ability_names"] = df["abilities"].apply(extract_abilities)

    for stat_name in ["hp", "attack", "defense", "special-attack", "special-defense", "speed"]:
        df[stat_name] = df["stats"].apply(lambda x: extract_stat(x, stat_name))

    df["generation"] = df["species"].apply(lambda s: extract_species_field(s, "generation"))
    df["description"] = df["species"].apply(lambda s: extract_species_field(s, "description"))

    # Seleccionamos columnas útiles
    cols = [
        "id", "name", "species_name", "type_names", "ability_names",
        "hp", "attack", "defense", "special-attack", "special-defense", "speed",
        "height", "weight", "generation", "description"
    ]
    df_final = df[cols]

    out_path = Path(input_path).with_name("pokedex_flatten.csv")
    df_final.to_csv(out_path, index=False)
    print(f"✅ Archivo aplanado guardado en: {out_path}")
    print(f"📊 Total de registros: {len(df_final)}")
    print(f"📈 Columnas finales: {list(df_final.columns)}")

    return df_final

if __name__ == "__main__":
    flatten_pokedex()
