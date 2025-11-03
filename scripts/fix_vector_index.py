#!/usr/bin/env python3
"""
Fix Vector Index Dimensions
Erstellt Vector Index mit korrekter Dimension neu
"""

import os
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")
EMBEDDING_DIMENSIONS = int(os.getenv("EMBEDDING_DIMENSIONS", "1536"))

def main():
    print("\n" + "="*80)
    print("🔧 Fix Vector Index Dimensions")
    print("="*80)
    
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))
    
    with driver.session() as session:
        # Drop old index
        print("\n1. Lösche alten Vector Index...")
        try:
            session.run("DROP INDEX chunk_embeddings IF EXISTS")
            print("✅ Alter Index gelöscht")
        except Exception as e:
            print(f"⚠️  {e}")
        
        # Create new index
        print(f"\n2. Erstelle neuen Vector Index (dimensions: {EMBEDDING_DIMENSIONS})...")
        try:
            query = """
                CREATE VECTOR INDEX chunk_embeddings IF NOT EXISTS
                FOR (c:Chunk)
                ON c.embedding
                OPTIONS {
                    indexConfig: {
                        `vector.dimensions`: $dimensions,
                        `vector.similarity_function`: 'cosine'
                    }
                }
            """
            session.run(query, dimensions=EMBEDDING_DIMENSIONS)
            print("✅ Neuer Index erstellt")
        except Exception as e:
            print(f"❌ Fehler: {e}")
            driver.close()
            return 1
        
        # Verify
        print("\n3. Verifiziere Indexes...")
        result = session.run("SHOW INDEXES WHERE name = 'chunk_embeddings'")
        record = result.single()
        
        if record:
            print(f"✅ Vector Index gefunden:")
            print(f"   Name: {record.get('name')}")
            print(f"   Type: {record.get('type')}")
            print(f"   State: {record.get('state')}")
        else:
            print("❌ Vector Index nicht gefunden!")
    
    driver.close()
    
    print("\n" + "="*80)
    print("✅ Vector Index bereit!")
    print("="*80)
    print("\nTeste mit:")
    print("  python scripts/test_vector_search.py 'Widerspruch' --mock --sgb X")
    print()
    
    return 0

if __name__ == "__main__":
    exit(main())
