"""
mongo_query.py
──────────────────────────────────────────────
Resilient factual lookup for Pokémon knowledge base.
──────────────────────────────────────────────
"""

import os
from typing import List, Dict
from dotenv import load_dotenv, find_dotenv
from pymongo import MongoClient, errors

# ───────────────────────────────────────────────
# CONFIG
# ───────────────────────────────────────────────
load_dotenv(find_dotenv())

MONGO_URI = os.getenv("MONGO_URI", "mongodb://admin:admin123@localhost:27017/")
MONGO_DB = os.getenv("MONGO_DB", "pokedex")
MONGO_COLLECTION = os.getenv("MONGO_COLLECTION", "pokemon")


# ───────────────────────────────────────────────
# FACTUAL QUERY FUNCTION
# ───────────────────────────────────────────────
def lookup_factual(intents: List[Dict]) -> List[Dict]:
    """
    Given a list of intents from the IntentRouter, try to resolve factual data from MongoDB.
    Returns a list of factual results (empty list if not found or error).
    """

    results = []
    try:
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=2000)
        db = client[MONGO_DB]
        collection = db[MONGO_COLLECTION]

        for intent in intents:
            if intent.get("type") != "factual":
                continue

            entity = intent.get("entity")
            attributes = intent.get("attributes", [])

            # Case-insensitive search by entity name
            query = {}
            if entity:
                query = {"name": {"$regex": f"^{entity}$", "$options": "i"}}

            # Fields to return (projection)
            projection = {
                "name": 1,
                "types": 1,
                "abilities": 1,
                "stats": 1,
                "category": 1,
                "description": 1,
            }

            doc = collection.find_one(query, projection) if query else None
            if not doc:
                continue

            # Build simplified response
            attr_values = {}

            for attr in attributes:
                if attr == "type" and "types" in doc:
                    attr_values["type"] = doc["types"]
                elif attr == "ability" and "abilities" in doc:
                    attr_values["abilities"] = doc["abilities"]
                elif attr == "stat" and "stats" in doc:
                    attr_values["stats"] = doc["stats"]
                elif attr == "category" and "category" in doc:
                    attr_values["category"] = doc["category"]
                elif attr == "relation":
                    # Skip relational requests here (not factual)
                    continue

            # If no attributes matched, include basic info
            if not attr_values:
                attr_values = {
                    "type": doc.get("types"),
                    "abilities": doc.get("abilities"),
                    "category": doc.get("category"),
                    "description": doc.get("description"),
                }

            results.append({
                "entity": doc.get("name", entity),
                "attributes": attr_values,
                "source": "mongo",
            })

    except errors.PyMongoError as e:
        print(f"⚠️ MongoDB error: {e}")
        return []  # fail silently

    finally:
        try:
            client.close()
        except Exception:
            pass

    return results
