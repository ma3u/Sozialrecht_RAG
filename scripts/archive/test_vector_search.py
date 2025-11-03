#!/usr/bin/env python3
"""
Test Vector Search - Semantische Suche
Testet die Vector Search Funktionalität mit Neo4j

Usage:
    python scripts/test_vector_search.py "Wie funktioniert Widerspruch?"
    python scripts/test_vector_search.py "Datenschutz Sozialdaten" --limit 5
"""

import os
import sys
import argparse
from typing import List, Optional
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")

# OpenAI Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
EMBEDDING_DIMENSIONS = int(os.getenv("EMBEDDING_DIMENSIONS", "1536"))

# Azure OpenAI Configuration
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT", "")
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY", "")
AZURE_OPENAI_EMBEDDING_DEPLOYMENT = os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT", "text-embedding-3-large")
AZURE_OPENAI_EMBEDDING_DIMENSIONS = int(os.getenv("AZURE_OPENAI_EMBEDDING_DIMENSIONS", "3072"))
AZURE_OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION", "2024-08-01-preview")


def get_query_embedding(query: str, use_mock: bool = False) -> Optional[List[float]]:
    """Generiert Embedding für Query"""
    
    if use_mock:
        import numpy as np
        # Use Azure dimensions if available, otherwise fall back to standard
        dimensions = AZURE_OPENAI_EMBEDDING_DIMENSIONS if AZURE_OPENAI_ENDPOINT else EMBEDDING_DIMENSIONS
        vec = np.random.randn(dimensions)
        vec = vec / np.linalg.norm(vec)
        return vec.tolist()
    
    # Try Azure OpenAI first
    if AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_API_KEY:
        try:
            from openai import AzureOpenAI
            
            client = AzureOpenAI(
                api_key=AZURE_OPENAI_API_KEY,
                api_version=AZURE_OPENAI_API_VERSION,
                azure_endpoint=AZURE_OPENAI_ENDPOINT
            )
            
            response = client.embeddings.create(
                model=AZURE_OPENAI_EMBEDDING_DEPLOYMENT,
                input=query,
                dimensions=AZURE_OPENAI_EMBEDDING_DIMENSIONS
            )
            
            print(f"✅ Azure OpenAI Embedding generiert ({AZURE_OPENAI_EMBEDDING_DEPLOYMENT})")
            return response.data[0].embedding
            
        except Exception as e:
            print(f"⚠️  Azure OpenAI Fehler: {e}")
            print("   Versuche Standard OpenAI...")
    
    # Fall back to standard OpenAI
    if OPENAI_API_KEY and OPENAI_API_KEY != "sk-your-openai-api-key-here":
        try:
            import openai
            client = openai.OpenAI(api_key=OPENAI_API_KEY)
            
            response = client.embeddings.create(
                model=EMBEDDING_MODEL,
                input=query,
                dimensions=EMBEDDING_DIMENSIONS if "3" in EMBEDDING_MODEL else None
            )
            
            return response.data[0].embedding
            
        except Exception as e:
            print(f"⚠️  OpenAI Fehler: {e}")
            print("   Verwende Mock-Embedding")
            return get_query_embedding(query, use_mock=True)
    
    # No API keys available
    print("⚠️  Kein OpenAI/Azure API Key - verwende Mock-Embedding")
    return get_query_embedding(query, use_mock=True)


def vector_search(driver, query_embedding: List[float], limit: int = 5, sgb_filter: Optional[str] = None):
    """Führt Vector Search in Neo4j aus"""
    
    cypher_query = """
        CALL db.index.vector.queryNodes('chunk_embeddings', $limit, $query_embedding)
        YIELD node, score
        
        MATCH (node)<-[:HAS_CHUNK]-(norm:LegalNorm)<-[:CONTAINS_NORM]-(doc:LegalDocument)
    """
    
    if sgb_filter:
        cypher_query += " WHERE doc.sgb_nummer = $sgb"
    
    cypher_query += """
        RETURN 
            doc.sgb_nummer as sgb,
            norm.paragraph_nummer as paragraph,
            norm.enbez as titel,
            node.text as chunk_text,
            score,
            node.chunk_id as chunk_id
        ORDER BY score DESC
        LIMIT $limit
    """
    
    params = {
        "query_embedding": query_embedding,
        "limit": limit
    }
    
    if sgb_filter:
        params["sgb"] = sgb_filter
    
    with driver.session() as session:
        result = session.run(cypher_query, **params)
        return [dict(record) for record in result]


def main():
    parser = argparse.ArgumentParser(description="Test Vector Search")
    parser.add_argument("query", type=str, help="Such-Query")
    parser.add_argument("--limit", type=int, default=5, help="Anzahl Ergebnisse (default: 5)")
    parser.add_argument("--sgb", type=str, help="Filter auf SGB (z.B. 'X')")
    parser.add_argument("--mock", action="store_true", help="Mock-Embedding verwenden")
    
    args = parser.parse_args()
    
    print("\n" + "="*80)
    print("🔍 Vector Search Test")
    print("="*80)
    print(f"\nQuery: \"{args.query}\"")
    print(f"Limit: {args.limit}")
    print(f"SGB Filter: {args.sgb or 'Alle'}")
    
    if args.mock:
        mode = 'Mock'
    elif AZURE_OPENAI_ENDPOINT:
        mode = 'Azure OpenAI'
    elif OPENAI_API_KEY:
        mode = 'OpenAI'
    else:
        mode = 'Mock (kein API Key)'
    
    print(f"Modus: {mode}")
    
    # Connect Neo4j
    print(f"\n📊 Verbinde zu Neo4j...")
    try:
        driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))
        driver.verify_connectivity()
        print("✅ Verbindung erfolgreich")
    except Exception as e:
        print(f"❌ Fehler: {e}")
        return 1
    
    # Generate query embedding
    print(f"\n🤖 Generiere Query-Embedding...")
    query_embedding = get_query_embedding(args.query, use_mock=args.mock)
    
    if not query_embedding:
        print("❌ Embedding-Generierung fehlgeschlagen")
        driver.close()
        return 1
    
    print(f"✅ Embedding generiert (Dimension: {len(query_embedding)})")
    
    # Search
    print(f"\n🔎 Suche relevante Chunks...")
    try:
        results = vector_search(driver, query_embedding, args.limit, args.sgb)
    except Exception as e:
        print(f"❌ Vector Search Fehler: {e}")
        print("\nMögliche Ursachen:")
        print("  - Vector Index noch nicht erstellt")
        print("  - Keine Chunks mit Embeddings vorhanden")
        print("\nFühre aus:")
        print("  python scripts/generate_embeddings.py --mock --execute")
        driver.close()
        return 1
    
    if not results:
        print("⚠️  Keine Ergebnisse gefunden")
        driver.close()
        return 0
    
    print(f"✅ {len(results)} Chunks gefunden")
    
    # Display results
    print("\n" + "="*80)
    print("📄 ERGEBNISSE")
    print("="*80)
    
    for i, result in enumerate(results, 1):
        score = result['score']
        sgb = result['sgb']
        para = result['paragraph']
        titel = result['titel']
        text = result['chunk_text']
        
        print(f"\n{i}. Score: {score:.4f} | SGB {sgb} § {para} ({titel})")
        print(f"   {'-' * 70}")
        
        # Truncate text for display
        display_text = text[:300] + "..." if len(text) > 300 else text
        print(f"   {display_text}")
    
    print("\n" + "="*80)
    print("✅ Vector Search erfolgreich!")
    print("="*80)
    
    # Suggestions
    print("\n💡 Weitere Test-Queries:")
    print("  python scripts/test_vector_search.py 'Widerspruchsverfahren' --sgb X")
    print("  python scripts/test_vector_search.py 'Sozialdatenschutz' --limit 10")
    print("  python scripts/test_vector_search.py 'Datenschutz DSGVO' --sgb X")
    print()
    
    driver.close()
    return 0


if __name__ == "__main__":
    exit(main())
