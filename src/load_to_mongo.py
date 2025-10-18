import pandas as pd
from pymongo import MongoClient
from pathlib import Path
import ast

# ──────────────────────────────────────────────
# CONFIGURACIÓN DE CONEXIÓN
# ──────────────────────────────────────────────
client = MongoClient("mongodb://admin:admin123@localhost:27017/")
db = client["pokedex"]

# ──────────────────────────────────────────────
# CARGA DE DATASETS
# ──────────────────────────────────────────────
def load_csv(path):
    print(f"📂 Leyendo {path}...")
    df = pd.read_csv(path)
    return df

def insert_collection(df, collection_name):
    """Inserta los documentos del DataFrame en MongoDB"""
    print(f"💾 Insertando en colección '{collection_name}' ({len(df)} documentos)...")
    records = df.to_dict(orient="records")
    db[collection_name].delete_many({})  # limpia colección previa
    db[collection_name].insert_many(records)
    print(f"✅ {collection_name}: {db[collection_name].count_documents({})} registros totales.")

# ──────────────────────────────────────────────
# PROCESO PRINCIPAL
# ──────────────────────────────────────────────
if __name__ == "__main__":
    base_path = Path("data/structured/consolidated")

    pokedex = load_csv(base_path / "pokedex_full.csv")
    evolutions = load_csv(base_path / "evolutions_full.csv")
    types = load_csv(base_path / "type_relations_full.csv")

    insert_collection(pokedex, "pokemon")
    insert_collection(evolutions, "evolutions")
    insert_collection(types, "type_relations")

    print("\n🏁 Carga completada correctamente.")
