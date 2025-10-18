import ast
from pymongo import MongoClient
from tqdm import tqdm

# ╔════════════════════════════════════════════════════════════╗
# ║                   DATABASE CONNECTION                      ║
# ╚════════════════════════════════════════════════════════════╝

client = MongoClient("mongodb://admin:admin123@localhost:27017/")
db = client["pokedex"]

# Campos que deben ser convertidos de string a estructuras reales (list/dict)
FIELDS_TO_NORMALIZE = ["types", "abilities", "stats", "species"]


# ╔════════════════════════════════════════════════════════════╗
# ║                      HELPER FUNCTIONS                      ║
# ╚════════════════════════════════════════════════════════════╝

def safe_parse(val):
    """
    Convierte un string con estructura Python (listas o dicts) a objeto real.
    Usa ast.literal_eval para parsear valores tipo: 
    "[{'slot': 1, 'type': {'name': 'steel'}}]"
    """
    if not isinstance(val, str):
        return val
    try:
        parsed = ast.literal_eval(val)
        return parsed
    except Exception:
        return val


# ╔════════════════════════════════════════════════════════════╗
# ║                   NORMALIZATION PROCESS                    ║
# ╚════════════════════════════════════════════════════════════╝

def normalize_collection():
    """
    Recorre todos los documentos de la colección 'pokemon' y convierte
    los campos que están guardados como string (representación de lista/dict)
    a estructuras Python reales.
    """
    projection = {"_id": 1, **{f: 1 for f in FIELDS_TO_NORMALIZE}}
    docs = db.pokemon.find({}, projection)

    updated = 0
    total = db.pokemon.count_documents({})

    for doc in tqdm(docs, total=total, desc="Normalizando documentos"):
        updates = {}
        for field in FIELDS_TO_NORMALIZE:
            if field in doc and isinstance(doc[field], str):
                parsed = safe_parse(doc[field])
                # Solo actualiza si se convierte correctamente
                if isinstance(parsed, (list, dict)):
                    updates[field] = parsed

        if updates:
            db.pokemon.update_one({"_id": doc["_id"]}, {"$set": updates})
            updated += 1

    print(f"✅ Normalizados {updated} de {total} documentos totales.")


# ╔════════════════════════════════════════════════════════════╗
# ║                          MAIN                              ║
# ╚════════════════════════════════════════════════════════════╝

if __name__ == "__main__":
    print("🚀 Iniciando normalización de datos en MongoDB...")
    normalize_collection()
    print("🏁 Proceso completado correctamente.")
