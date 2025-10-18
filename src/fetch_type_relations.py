import pandas as pd
from ingest_pokeapi_dlt_structured import get_type_relations

print("🔄 Descargando relaciones de daño entre tipos...")
type_relations = get_type_relations()

if type_relations:
    pd.DataFrame(type_relations).to_csv("data/structured/type_relations.csv", index=False)
    print(f"✅ Saved data/structured/type_relations.csv ({len(type_relations)} relaciones)")
else:
    print("⚠️ No se pudieron obtener relaciones de tipos.")
