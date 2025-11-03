#!/usr/bin/env python3
"""
Generate Embeddings for RAG System
Erstellt Embeddings für alle Chunks in Neo4j

Usage:
    # Dry-Run (keine Änderungen)
    python scripts/generate_embeddings.py --dry-run
    
    # Embeddings generieren
    python scripts/generate_embeddings.py --execute
    
    # Nur bestimmte SGB
    python scripts/generate_embeddings.py --execute --sgb X
"""

import os
import sys
import argparse
from typing import List, Dict, Optional
from neo4j import GraphDatabase
from dotenv import load_dotenv

# Load environment
load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")

# OpenAI or Azure OpenAI
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
EMBEDDING_DIMENSIONS = int(os.getenv("EMBEDDING_DIMENSIONS", "1536"))

# Azure OpenAI Configuration
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT", "")
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY", "")
AZURE_OPENAI_EMBEDDING_DEPLOYMENT = os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT", "text-embedding-3-large")
AZURE_OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION", "2024-08-01-preview")


def check_openai_available():
    """Prüft ob OpenAI verfügbar ist"""
    try:
        import openai
        return True
    except ImportError:
        return False


def get_openai_embedding(text: str) -> Optional[List[float]]:
    """Generiert Embedding mit OpenAI oder Azure OpenAI"""
    try:
        import openai
        
        # Check if Azure OpenAI is configured
        if AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_API_KEY:
            client = openai.AzureOpenAI(
                api_key=AZURE_OPENAI_API_KEY,
                api_version=AZURE_OPENAI_API_VERSION,
                azure_endpoint=AZURE_OPENAI_ENDPOINT
            )
            
            response = client.embeddings.create(
                model=AZURE_OPENAI_EMBEDDING_DEPLOYMENT,
                input=text,
                dimensions=EMBEDDING_DIMENSIONS
            )
        # Otherwise use standard OpenAI
        elif OPENAI_API_KEY and OPENAI_API_KEY != "sk-your-openai-api-key-here":
            client = openai.OpenAI(api_key=OPENAI_API_KEY)
            
            response = client.embeddings.create(
                model=EMBEDDING_MODEL,
                input=text,
                dimensions=EMBEDDING_DIMENSIONS if "3" in EMBEDDING_MODEL else None
            )
        else:
            return None
        
        return response.data[0].embedding
        
    except Exception as e:
        print(f"⚠️  OpenAI API Fehler: {e}")
        return None


def get_mock_embedding(dimensions: int = 1536) -> List[float]:
    """Generiert Mock-Embedding für Testing"""
    import numpy as np
    # Normalisierter Zufallsvektor
    vec = np.random.randn(dimensions)
    vec = vec / np.linalg.norm(vec)
    return vec.tolist()


def get_chunks_without_embeddings(driver, sgb_filter: Optional[str] = None):
    """Lädt alle Chunks ohne Embeddings"""
    
    query = """
        MATCH (chunk:Chunk)
        WHERE chunk.embedding IS NULL
    """
    
    if sgb_filter:
        query += """
            AND EXISTS {
                MATCH (chunk)<-[:HAS_CHUNK]-(:LegalNorm)<-[:CONTAINS_NORM]-(doc:LegalDocument)
                WHERE doc.sgb_nummer = $sgb
            }
        """
    
    query += """
        RETURN 
            chunk.chunk_id as chunk_id,
            chunk.text as text,
            chunk.norm_id as norm_id
        LIMIT 1000
    """
    
    with driver.session() as session:
        result = session.run(query, sgb=sgb_filter)
        return [dict(record) for record in result]


def update_chunk_embedding(driver, chunk_id: str, embedding: List[float]):
    """Speichert Embedding in Neo4j"""
    
    query = """
        MATCH (chunk:Chunk {chunk_id: $chunk_id})
        SET chunk.embedding = $embedding
        RETURN chunk.chunk_id as updated_id
    """
    
    with driver.session() as session:
        result = session.run(query, chunk_id=chunk_id, embedding=embedding)
        return result.single()


def create_vector_index(driver):
    """Erstellt Vector Index für semantische Suche"""
    
    # Check if index exists
    check_query = "SHOW INDEXES WHERE name = 'chunk_embeddings'"
    
    with driver.session() as session:
        result = session.run(check_query)
        if result.single():
            print("ℹ️  Vector Index 'chunk_embeddings' existiert bereits")
            return True
    
    # Create vector index
    create_query = """
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
    
    try:
        with driver.session() as session:
            session.run(create_query, dimensions=EMBEDDING_DIMENSIONS)
            print(f"✅ Vector Index erstellt (dimensions: {EMBEDDING_DIMENSIONS})")
            return True
    except Exception as e:
        print(f"⚠️  Vector Index Fehler: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Generiere Embeddings für RAG System")
    parser.add_argument("--execute", action="store_true", help="Embeddings generieren (ohne: Dry-Run)")
    parser.add_argument("--sgb", type=str, help="Nur bestimmte SGB (z.B. 'X')")
    parser.add_argument("--mock", action="store_true", help="Mock-Embeddings verwenden (Testing)")
    parser.add_argument("--limit", type=int, default=1000, help="Max. Anzahl Chunks (default: 1000)")
    
    args = parser.parse_args()
    
    print("\n" + "="*80)
    print("🤖 RAG System - Embedding Generator")
    print("="*80)
    print(f"\nModus: {'EXECUTE' if args.execute else 'DRY-RUN'}")
    print(f"SGB Filter: {args.sgb or 'Alle'}")
    print(f"Limit: {args.limit}")
    
    # Check OpenAI
    if not args.mock and not check_openai_available():
        print("\n❌ OpenAI Package nicht installiert!")
        print("   Installiere: pip install openai tiktoken")
        return 1
    
    if not args.mock:
        has_azure = AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_API_KEY
        has_openai = OPENAI_API_KEY and OPENAI_API_KEY != "sk-your-openai-api-key-here"
        
        if not has_azure and not has_openai:
            print("\n⚠️  WARNUNG: Kein OpenAI API Key gefunden!")
            print("   Setze OPENAI_API_KEY oder AZURE_OPENAI_* in .env")
            print("   Verwende --mock für Test-Embeddings")
            return 1
        
        if has_azure:
            print(f"\n✅ Azure OpenAI konfiguriert: {AZURE_OPENAI_ENDPOINT}")
            print(f"   Deployment: {AZURE_OPENAI_EMBEDDING_DEPLOYMENT}")
        else:
            print(f"\n✅ OpenAI konfiguriert: {EMBEDDING_MODEL}")
    
    # Connect to Neo4j
    print(f"\nVerbinde zu Neo4j: {NEO4J_URI}")
    try:
        driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))
        driver.verify_connectivity()
        print("✅ Verbindung erfolgreich")
    except Exception as e:
        print(f"❌ Neo4j Verbindung fehlgeschlagen: {e}")
        return 1
    
    # Get chunks
    print(f"\n📊 Lade Chunks ohne Embeddings...")
    chunks = get_chunks_without_embeddings(driver, args.sgb)
    
    if not chunks:
        print("✅ Alle Chunks haben bereits Embeddings!")
        driver.close()
        return 0
    
    chunks = chunks[:args.limit]
    
    print(f"✅ {len(chunks)} Chunks gefunden")
    
    if not args.execute:
        print("\n" + "="*80)
        print("🔍 DRY-RUN Modus - Keine Änderungen")
        print("="*80)
        print("\nBeispiel Chunks:")
        for i, chunk in enumerate(chunks[:3], 1):
            print(f"\n{i}. Chunk: {chunk['chunk_id']}")
            print(f"   Text: {chunk['text'][:100]}...")
        
        print("\n" + "="*80)
        print("➡️  Führe mit --execute aus um Embeddings zu generieren")
        print("   Beispiel: python scripts/generate_embeddings.py --execute")
        if not args.mock:
            print(f"\n💰 Kosten-Schätzung (OpenAI {EMBEDDING_MODEL}):")
            print(f"   ~{len(chunks) * 0.00002:.4f} USD für {len(chunks)} Chunks")
        print("="*80)
        
        driver.close()
        return 0
    
    # Generate embeddings
    print("\n" + "="*80)
    print("🚀 Generiere Embeddings")
    print("="*80)
    
    success_count = 0
    error_count = 0
    
    for i, chunk in enumerate(chunks, 1):
        chunk_id = chunk['chunk_id']
        text = chunk['text']
        
        # Generate embedding
        if args.mock:
            embedding = get_mock_embedding(EMBEDDING_DIMENSIONS)
        else:
            embedding = get_openai_embedding(text)
        
        if embedding is None:
            print(f"❌ {i}/{len(chunks)}: Fehler bei {chunk_id}")
            error_count += 1
            continue
        
        # Update Neo4j
        try:
            update_chunk_embedding(driver, chunk_id, embedding)
            success_count += 1
            
            if i % 10 == 0 or i == len(chunks):
                print(f"✅ {i}/{len(chunks)}: {success_count} erfolgreich, {error_count} Fehler")
        
        except Exception as e:
            print(f"❌ {i}/{len(chunks)}: DB Fehler bei {chunk_id}: {e}")
            error_count += 1
    
    # Create vector index
    print("\n" + "="*80)
    print("📊 Erstelle Vector Index")
    print("="*80)
    
    create_vector_index(driver)
    
    # Summary
    print("\n" + "="*80)
    print("📈 ZUSAMMENFASSUNG")
    print("="*80)
    print(f"✅ Erfolgreich: {success_count}/{len(chunks)}")
    print(f"❌ Fehler: {error_count}/{len(chunks)}")
    
    if success_count > 0:
        print("\n🎉 Embeddings generiert!")
        print("\nNächste Schritte:")
        print("1. Vector Search testen:")
        print("   python scripts/test_vector_search.py 'Widerspruch einlegen'")
        print("\n2. RAG Query ausführen:")
        print("   python scripts/rag_query.py 'Wie funktioniert das Widerspruchsverfahren?'")
    
    print("="*80 + "\n")
    
    driver.close()
    return 0 if error_count == 0 else 1


if __name__ == "__main__":
    exit(main())
