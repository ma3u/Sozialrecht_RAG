#!/usr/bin/env python3
"""
Setup Neo4j Performance Indexes
Erstellt Indexes für optimale Query-Performance der 14 Use Cases

Usage:
    python scripts/setup_neo4j_indexes.py
"""

import os
from neo4j import GraphDatabase
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")


def create_indexes(driver):
    """Erstellt Performance Indexes für LegalNorm, LegalDocument und Chunk"""
    
    indexes = [
        # Norm Indexes
        "CREATE INDEX norm_paragraph IF NOT EXISTS FOR (n:LegalNorm) ON (n.paragraph_nummer)",
        "CREATE INDEX norm_sgb IF NOT EXISTS FOR (n:LegalNorm) ON (n.sgb_nummer)",
        "CREATE INDEX norm_enbez IF NOT EXISTS FOR (n:LegalNorm) ON (n.enbez)",
        
        # Document Indexes
        "CREATE INDEX doc_sgb IF NOT EXISTS FOR (d:LegalDocument) ON (d.sgb_nummer)",
        "CREATE INDEX doc_title IF NOT EXISTS FOR (d:LegalDocument) ON (d.title)",
        
        # Chunk Indexes
        "CREATE INDEX chunk_text IF NOT EXISTS FOR (c:Chunk) ON (c.text)",
        "CREATE INDEX chunk_id IF NOT EXISTS FOR (c:Chunk) ON (c.chunk_id)",
    ]
    
    with driver.session() as session:
        print("\n" + "="*80)
        print("🔧 Erstelle Neo4j Performance Indexes")
        print("="*80 + "\n")
        
        for idx, query in enumerate(indexes, 1):
            try:
                session.run(query)
                index_name = query.split("INDEX ")[1].split(" IF")[0]
                print(f"✅ Index {idx}/{len(indexes)}: {index_name}")
            except Exception as e:
                print(f"⚠️  Index {idx}/{len(indexes)} fehlgeschlagen: {e}")
        
        print("\n" + "="*80)
        print("📊 Verifiziere Indexes")
        print("="*80 + "\n")
        
        # Show all indexes
        result = session.run("SHOW INDEXES")
        indexes_found = []
        
        for record in result:
            name = record.get("name", "unknown")
            state = record.get("state", "unknown")
            type_ = record.get("type", "unknown")
            
            if "norm_" in name or "doc_" in name or "chunk_" in name:
                indexes_found.append(name)
                print(f"  ✓ {name} ({type_}, {state})")
        
        print("\n" + "="*80)
        print(f"✅ {len(indexes_found)} Performance Indexes erstellt!")
        print("="*80 + "\n")
        
        return indexes_found


def verify_performance(driver):
    """Testet Query-Performance mit PROFILE"""
    
    test_queries = [
        {
            "name": "UC10: Widerspruch Quick Check",
            "query": """
                MATCH (doc:LegalDocument {sgb_nummer: 'X'})
                      -[:CONTAINS_NORM]->(norm:LegalNorm)
                WHERE norm.paragraph_nummer IN ['79', '80', '84', '85']
                OPTIONAL MATCH (norm)-[:HAS_CHUNK]->(chunk:Chunk)
                RETURN count(DISTINCT norm) as normen, count(DISTINCT chunk) as chunks
            """
        },
        {
            "name": "UC14: Datenschutz Quick Check",
            "query": """
                MATCH (doc:LegalDocument {sgb_nummer: 'X'})
                      -[:CONTAINS_NORM]->(norm:LegalNorm)
                WHERE toInteger(norm.paragraph_nummer) >= 67 
                  AND toInteger(norm.paragraph_nummer) <= 85
                OPTIONAL MATCH (norm)-[:HAS_CHUNK]->(chunk:Chunk)
                RETURN count(DISTINCT norm) as normen, count(DISTINCT chunk) as chunks
            """
        }
    ]
    
    print("\n" + "="*80)
    print("⚡ Performance Tests")
    print("="*80 + "\n")
    
    with driver.session() as session:
        for test in test_queries:
            try:
                # Run query and measure
                result = session.run(test["query"])
                data = result.single()
                
                # Get execution plan stats
                summary = result.consume()
                
                print(f"✅ {test['name']}")
                print(f"   Normen: {data['normen']}, Chunks: {data['chunks']}")
                print(f"   Zeit: {summary.result_available_after}ms")
                print()
                
            except Exception as e:
                print(f"❌ {test['name']}: {e}\n")
    
    print("="*80)


def main():
    """Main function"""
    
    print("\n" + "="*80)
    print("🚀 Neo4j Index Setup für 14 Use Cases")
    print("="*80)
    print(f"\nVerbinde zu: {NEO4J_URI}")
    print(f"Username: {NEO4J_USERNAME}")
    
    try:
        driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))
        
        # Verify connection
        driver.verify_connectivity()
        print("✅ Verbindung erfolgreich!\n")
        
        # Create indexes
        indexes = create_indexes(driver)
        
        # Verify performance
        verify_performance(driver)
        
        print("\n" + "="*80)
        print("🎉 SUCCESS!")
        print("="*80)
        print("\nNächste Schritte:")
        print("1. Öffne Neo4j Browser: http://localhost:7474")
        print("2. Teste Queries aus ~/Documents/Neo4j/guides/")
        print("3. Führe Health-Check aus: python scripts/test_uc10_uc14.py")
        print("\n")
        
        driver.close()
        
    except Exception as e:
        print(f"\n❌ FEHLER: {e}\n")
        print("Prüfe:")
        print("  - Neo4j läuft auf Port 7687")
        print("  - Credentials in .env sind korrekt")
        print("  - curl http://localhost:7474 gibt 200 OK\n")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
