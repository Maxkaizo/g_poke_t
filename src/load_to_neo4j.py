import os
from neo4j import GraphDatabase
from tqdm import tqdm

# ───────────────────────────────────────────────
# 🔧 CONFIG
# ───────────────────────────────────────────────
NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "supersecure123"
IMPORT_DIR = "/import"
LOCAL_DIR = "data/graph"
EXPORT_DIR = "data/exports"

# ───────────────────────────────────────────────
# 🧠 FUNCIONES AUXILIARES
# ───────────────────────────────────────────────
def run_query(session, query: str):
    """Ejecuta un bloque Cypher dentro de una sesión Neo4j."""
    session.run(query)

def load_csv(session, file_name, query_template):
    """Carga un CSV específico aplicando un bloque de Cypher."""
    file_path = f"file:///{file_name}"
    query = query_template.format(file=file_path)
    run_query(session, query)

def check_count(session, label=None, rel_type=None):
    """Imprime el número de nodos o relaciones existentes."""
    if label:
        result = session.run(f"MATCH (n:{label}) RETURN count(n) AS c").single()
        print(f"📊 {label}: {result['c']} nodos")
    if rel_type:
        result = session.run(f"MATCH ()-[r:{rel_type}]->() RETURN count(r) AS c").single()
        print(f"📊 {rel_type}: {result['c']} relaciones")

def export_graphml(session, export_path):
    """Exporta todo el grafo completo a un archivo GraphML local (modo stream)."""
    print("\n💾 Exportando grafo completo a GraphML (modo stream)...")
    query = """
        CALL apoc.export.graphml.all(null, {
            stream: true,
            useTypes: true,
            storeNodeIds: true
        }) YIELD data
        RETURN data;
    """
    result = session.run(query).single()
    graphml_data = result["data"]

    os.makedirs(EXPORT_DIR, exist_ok=True)
    output_path = os.path.join(EXPORT_DIR, export_path)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(graphml_data)

    print(f"✅ Grafo exportado correctamente a '{output_path}'")

# ───────────────────────────────────────────────
# 🚀 SCRIPT PRINCIPAL
# ───────────────────────────────────────────────
def main():
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

    with driver.session(database="neo4j") as session:
        print("🚀 Conectado a Neo4j — inicializando importación...")

        # 1️⃣ Limpiar y crear constraints
        print("🧹 Limpiando base y creando índices...")
        session.run("MATCH (n) DETACH DELETE n")
        session.run("CREATE CONSTRAINT unique_pokemon IF NOT EXISTS FOR (p:Pokemon) REQUIRE p.name IS UNIQUE")
        session.run("CREATE CONSTRAINT unique_type IF NOT EXISTS FOR (t:Type) REQUIRE t.name IS UNIQUE")

        # 2️⃣ Importar nodos Pokémon
        print("📦 Cargando Pokémon...")
        load_csv(session, "pokemon_nodes.csv", """
            LOAD CSV WITH HEADERS FROM '{file}' AS row
            CREATE (:Pokemon {{
                id: toInteger(row.id),
                name: row.name,
                height: toInteger(row.height),
                weight: toInteger(row.weight),
                description: row.description,
                generation: row.generation
            }})
        """)
        check_count(session, label="Pokemon")

        # 3️⃣ Importar nodos Tipo
        print("📦 Cargando Tipos...")
        load_csv(session, "type_nodes.csv", """
            LOAD CSV WITH HEADERS FROM '{file}' AS row
            CREATE (:Type {{name: row.name}})
        """)
        check_count(session, label="Type")

        # 4️⃣ Relaciones HAS_TYPE
        print("🔗 Creando relaciones HAS_TYPE...")
        file_path = "file:///has_type_edges.csv"
        query = f"""
            LOAD CSV WITH HEADERS FROM '{file_path}' AS row
            MATCH (p:Pokemon {{name: row.pokemon}})
            MATCH (t:Type {{name: row.type}})
            MERGE (p)-[:HAS_TYPE]->(t);
        """
        run_query(session, query)
        check_count(session, rel_type="HAS_TYPE")

        # 5️⃣ Relaciones de evolución
        print("🔗 Creando relaciones EVOLVES_TO...")
        load_csv(session, "evolutions_edges.csv", """
            LOAD CSV WITH HEADERS FROM '{file}' AS row
            MATCH (src:Pokemon {{name: row.source}})
            MATCH (dst:Pokemon {{name: row.target}})
            MERGE (src)-[:EVOLVES_TO]->(dst)
        """)
        check_count(session, rel_type="EVOLVES_TO")

        # 6️⃣ Relaciones entre tipos
        print("🔗 Creando relaciones entre Tipos (STRONG_AGAINST / WEAK_AGAINST)...")
        file_path = "file:///type_relations_edges.csv"
        query = f"""
            LOAD CSV WITH HEADERS FROM '{file_path}' AS row
            MATCH (src:Type {{name: row.source}})
            MATCH (dst:Type {{name: row.target}})
            WITH src, dst, row
            CALL apoc.merge.relationship(src, row.relation, {{}}, {{}}, dst, {{}}) YIELD rel
            RETURN count(rel);
        """
        run_query(session, query)
        print("📊 Relaciones de tipo cargadas (verificar en Neo4j Browser con MATCH (:Type)-[]->(:Type))")

        # 🧩 Validación final automática
        print("\n🧩 Validación final del grafo:")
        stats_queries = {
            "Pokémon": "MATCH (p:Pokemon) RETURN count(p) AS total;",
            "Tipos": "MATCH (t:Type) RETURN count(t) AS total;",
            "HAS_TYPE": "MATCH ()-[r:HAS_TYPE]->() RETURN count(r) AS total;",
            "EVOLVES_TO": "MATCH ()-[r:EVOLVES_TO]->() RETURN count(r) AS total;",
            "Relaciones entre Tipos": "MATCH (:Type)-[r]->(:Type) RETURN count(r) AS total;"
        }

        for name, q in stats_queries.items():
            result = session.run(q).single()
            print(f"📊 {name}: {result['total']}")

        print("\n🔍 Ejemplo de relaciones:")
        sample_queries = {
            "HAS_TYPE": """
                MATCH (p:Pokemon)-[:HAS_TYPE]->(t:Type)
                RETURN p.name AS Pokemon, t.name AS Type LIMIT 5;
            """,
            "EVOLVES_TO": """
                MATCH (p1:Pokemon)-[:EVOLVES_TO]->(p2:Pokemon)
                RETURN p1.name AS From, p2.name AS To LIMIT 5;
            """
        }

        for name, q in sample_queries.items():
            print(f"\n➡️  Ejemplos de {name}:")
            for row in session.run(q):
                print(dict(row))

        # 💾 Exportación GraphML directa al sistema local
        export_filename = "pokemon_graph.graphml"
        export_graphml(session, export_filename)

        print("\n✅ Importación y exportación completadas correctamente.\n")

    driver.close()


if __name__ == "__main__":
    main()
