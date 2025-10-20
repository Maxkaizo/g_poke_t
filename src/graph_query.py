"""
graph_query.py
──────────────────────────────────────────────
Handles relational queries using Neo4j + Cypher.
──────────────────────────────────────────────
"""

import os
from dotenv import load_dotenv, find_dotenv
from neo4j import GraphDatabase, basic_auth
from typing import Dict, List, Any

# ───────────────────────────────────────────────
# CONFIG
# ───────────────────────────────────────────────
load_dotenv(find_dotenv())

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "supersecure123")

# ───────────────────────────────────────────────
# CONNECTION
# ───────────────────────────────────────────────
driver = GraphDatabase.driver(NEO4J_URI, auth=basic_auth(NEO4J_USER, NEO4J_PASSWORD))

# ───────────────────────────────────────────────
# QUERY HANDLER
# ───────────────────────────────────────────────
def query_relational(intent: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Executes a relational query on Neo4j based on the provided intent.
    Supports: evolves_to, strong_against, weak_against.
    """
    entity = intent.get("entity")
    attributes = intent.get("attributes", [])
    results = []

    if not entity or not attributes:
        return results

    for attr in attributes:
        if attr == "evolves_to":
            cypher = """
            MATCH (p:Pokemon {name: $entity})-[:EVOLVES_TO]->(e:Pokemon)
            RETURN e.name AS target
            """
        elif attr == "strong_against":
            cypher = """
            MATCH (a:Type {name: $entity})-[:STRONG_AGAINST]->(b:Type)
            RETURN b.name AS target
            """
        elif attr == "weak_against":
            cypher = """
            MATCH (a:Type {name: $entity})-[:WEAK_AGAINST]->(b:Type)
            RETURN b.name AS target
            """
        else:
            continue

        try:
            with driver.session() as session:
                query_result = session.run(cypher, {"entity": entity})
                targets = [record["target"] for record in query_result]

                if targets:
                    results.append({
                        "entity": entity,
                        "relation": attr,
                        "targets": targets,
                        "source": "neo4j"
                    })

        except Exception as e:
            print(f"⚠️ Neo4j query failed for {entity} ({attr}): {e}")
            continue

    return results


# ───────────────────────────────────────────────
# TEST
# ───────────────────────────────────────────────
if __name__ == "__main__":
    test_intent = {
        "type": "relational",
        "entity": "Eevee",
        "attributes": ["evolves_to"],
    }
    output = query_relational(test_intent)
    print(output)
