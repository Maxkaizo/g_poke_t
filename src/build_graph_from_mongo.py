import os
from pathlib import Path
from typing import Dict, Set, List

import pandas as pd
from pymongo import MongoClient
from tqdm import tqdm

# ─────────────────────────────────────────────────────────────
# CONFIG: conexión a Mongo y directorio de salida
# ─────────────────────────────────────────────────────────────
MONGO_URI = "mongodb://admin:admin123@localhost:27017/"
DB_NAME = "pokedex"
OUT_DIR = Path("data/graph")
OUT_DIR.mkdir(parents=True, exist_ok=True)

# ─────────────────────────────────────────────────────────────
# Conexión
# ─────────────────────────────────────────────────────────────
client = MongoClient(MONGO_URI)
db = client[DB_NAME]

# ─────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────
def to_int_or_none(x):
    try:
        return int(x)
    except Exception:
        return None

def clean_str(x):
    if x is None:
        return None
    return str(x).strip()

# ─────────────────────────────────────────────────────────────
# 1) NODOS: Pokémon
#    Campos: id, name, species_name, height, weight, generation, description
#    Fuente: colección "pokemon"
# ─────────────────────────────────────────────────────────────
def export_pokemon_nodes():
    print("📦 Exportando nodos de Pokémon desde Mongo...")
    cursor = db.pokemon.find(
        {},
        {
            "_id": 0,
            "id": 1,
            "name": 1,
            "species_name": 1,
            "height": 1,
            "weight": 1,
            "species": 1,
        },
    )

    rows = []
    for doc in tqdm(cursor):
        species = doc.get("species") or {}
        rows.append(
            {
                "id": to_int_or_none(doc.get("id")),
                "name": clean_str(doc.get("name")),
                "species_name": clean_str(doc.get("species_name")),
                "height": to_int_or_none(doc.get("height")),
                "weight": to_int_or_none(doc.get("weight")),
                "generation": clean_str(species.get("generation")),
                "description": clean_str(species.get("description")),
            }
        )

    df = pd.DataFrame(rows).drop_duplicates(subset=["name"]).sort_values("id", na_position="last")
    out_path = OUT_DIR / "pokemon_nodes.csv"
    df.to_csv(out_path, index=False)
    print(f"✅ pokemon_nodes.csv → {len(df)} nodos")
    return df


# ─────────────────────────────────────────────────────────────
# 2) NODOS: Tipos
#    Fuente: tipos desde:
#      a) pokemon.types[].type.name
#      b) type_relations.{source,target}
# ─────────────────────────────────────────────────────────────
def export_type_nodes():
    print("📦 Exportando nodos de Tipos desde Mongo...")
    type_names: Set[str] = set()

    # a) desde pokemon
    cursor_p = db.pokemon.find({}, {"_id": 0, "types": 1})
    for doc in tqdm(cursor_p, desc="Recorriendo tipos en pokemon"):
        tlist = doc.get("types")
        if isinstance(tlist, list):
            for t in tlist:
                tname = (((t or {}).get("type") or {}).get("name"))
                if tname:
                    type_names.add(str(tname).strip())

    # b) desde type_relations
    cursor_r = db.type_relations.find({}, {"_id": 0, "source": 1, "target": 1})
    for rel in tqdm(cursor_r, desc="Recorriendo tipos en type_relations"):
        s = rel.get("source")
        t = rel.get("target")
        if s: type_names.add(str(s).strip())
        if t: type_names.add(str(t).strip())

    df = pd.DataFrame(sorted(type_names), columns=["name"])
    out_path = OUT_DIR / "type_nodes.csv"
    df.to_csv(out_path, index=False)
    print(f"✅ type_nodes.csv → {len(df)} nodos")
    return df


# ─────────────────────────────────────────────────────────────
# 3) ARISTAS: HAS_TYPE
#    (Pokemon)-[:HAS_TYPE]->(Type)
#    Fuente: pokemon.types[].type.name
# ─────────────────────────────────────────────────────────────
def export_has_type_edges():
    print("🔗 Exportando aristas HAS_TYPE...")
    edges: List[Dict[str, str]] = []

    cursor = db.pokemon.find({}, {"_id": 0, "name": 1, "types": 1})
    for doc in tqdm(cursor):
        pname = clean_str(doc.get("name"))
        tlist = doc.get("types")
        if not pname or not isinstance(tlist, list):
            continue
        for t in tlist:
            tname = (((t or {}).get("type") or {}).get("name"))
            if tname:
                edges.append({"pokemon": pname, "type": str(tname).strip()})

    df = pd.DataFrame(edges).drop_duplicates()
    out_path = OUT_DIR / "has_type_edges.csv"
    df.to_csv(out_path, index=False)
    print(f"✅ has_type_edges.csv → {len(df)} aristas")
    return df


# ─────────────────────────────────────────────────────────────
# 4) ARISTAS: EVOLVES_TO
#    (Pokemon)-[:EVOLVES_TO]->(Pokemon)
#    Fuente: colección "evolutions" {source, target}
# ─────────────────────────────────────────────────────────────
def export_evolutions_edges():
    print("🔗 Exportando aristas EVOLVES_TO...")
    cursor = db.evolutions.find({}, {"_id": 0, "source": 1, "target": 1})
    rows = []
    for doc in tqdm(cursor):
        s = clean_str(doc.get("source"))
        t = clean_str(doc.get("target"))
        if s and t:
            rows.append({"source": s, "target": t})

    df = pd.DataFrame(rows).drop_duplicates()
    out_path = OUT_DIR / "evolutions_edges.csv"
    df.to_csv(out_path, index=False)
    print(f"✅ evolutions_edges.csv → {len(df)} aristas")
    return df


# ─────────────────────────────────────────────────────────────
# 5) ARISTAS: Relaciones de Tipos
#    (Type)-[:STRONG_AGAINST]->(Type)
#    (Type)-[:WEAK_AGAINST]->(Type)
#    Fuente: colección "type_relations" {source, relation, target}
# ─────────────────────────────────────────────────────────────
def export_type_relations_edges():
    print("🔗 Exportando aristas de relaciones entre Tipos...")
    cursor = db.type_relations.find({}, {"_id": 0, "source": 1, "relation": 1, "target": 1})
    rows = []
    for doc in tqdm(cursor):
        s = clean_str(doc.get("source"))
        r = clean_str(doc.get("relation"))
        t = clean_str(doc.get("target"))
        if s and r and t:
            rows.append({"source": s, "relation": r, "target": t})

    df = pd.DataFrame(rows).drop_duplicates()
    out_path = OUT_DIR / "type_relations_edges.csv"
    df.to_csv(out_path, index=False)
    print(f"✅ type_relations_edges.csv → {len(df)} aristas")
    return df


# ─────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("🚀 Construyendo archivos de grafo desde MongoDB...")
    export_pokemon_nodes()
    export_type_nodes()
    export_has_type_edges()
    export_evolutions_edges()
    export_type_relations_edges()
    print(f"🏁 Listo. Archivos en: {OUT_DIR.resolve()}")
