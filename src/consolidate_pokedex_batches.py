import pandas as pd
from pathlib import Path
import json

# ╔════════════════════════════════════════════════════════════╗
# ║               UNIFY ALL BATCHES INTO ONE FILE              ║
# ╚════════════════════════════════════════════════════════════╝

def consolidate_pokedex_batches(base_dir="data/structured/batches"):
    batch_files = sorted(Path(base_dir).glob("pokedex_batch_*.csv"))
    if not batch_files:
        raise FileNotFoundError("❌ No se encontraron archivos pokedex_batch_*.csv")

    print(f"🔍 Encontrados {len(batch_files)} archivos de batch.")
    dfs = [pd.read_csv(f) for f in batch_files]
    df = pd.concat(dfs, ignore_index=True)
    print(f"✅ Consolidado: {len(df)} registros totales de Pokémon.")
    return df


def consolidate_evolutions(base_dir="data/structured/batches"):
    evo_files = sorted(Path(base_dir).glob("evolutions_batch_*.csv"))
    if not evo_files:
        print("⚠️ No se encontraron archivos de evolución.")
        return pd.DataFrame(columns=["source", "target"])
    
    dfs = [pd.read_csv(f) for f in evo_files]
    df = pd.concat(dfs, ignore_index=True).drop_duplicates()
    print(f"✅ Consolidado: {len(df)} relaciones de evolución.")
    return df


def load_type_relations(file_path="data/structured/type_relations.csv"):
    df = pd.read_csv(file_path)
    print(f"✅ Cargadas {len(df)} relaciones de tipos.")
    return df


if __name__ == "__main__":
    df_pokedex = consolidate_pokedex_batches()
    df_evo = consolidate_evolutions()
    df_types = load_type_relations()

    # Guardar todo en un archivo único
    out_dir = Path("data/structured/consolidated")
    out_dir.mkdir(parents=True, exist_ok=True)

    df_pokedex.to_csv(out_dir / "pokedex_full.csv", index=False)
    df_evo.to_csv(out_dir / "evolutions_full.csv", index=False)
    df_types.to_csv(out_dir / "type_relations_full.csv", index=False)

    print(f"\n💾 Guardado en {out_dir}/ (Pokémon, evoluciones y tipos).")
