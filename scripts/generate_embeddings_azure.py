#!/usr/bin/env python3
"""
Generate Embeddings using Azure OpenAI
Erstellt Embeddings für alle Chunks in Neo4j mit Azure OpenAI API

Usage:
    # Dry-Run (keine Änderungen)
    python scripts/generate_embeddings_azure.py --dry-run
    
    # Embeddings generieren
    python scripts/generate_embeddings_azure.py --execute
    
    # Nur bestimmte SGB
    python scripts/generate_embeddings_azure.py --execute --sgb X
"""

import os
import sys
import argparse
import time
from typing import List, Dict, Optional
from neo4j import GraphDatabase
from dotenv import load_dotenv
from openai import AzureOpenAI
import tiktoken

# Load environment
load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")

AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_OPENAI_EMBEDDING_DEPLOYMENT = os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT", "text-embedding-ada-002")
AZURE_OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION", "2024-08-01-preview")
EMBEDDING_DIMENSIONS = int(os.getenv("AZURE_OPENAI_EMBEDDING_DIMENSIONS", "1536"))
MAX_TOKENS = 8191  # Azure OpenAI embedding model limit (leave 1 token buffer)


def count_tokens(text: str, encoding_name: str = "cl100k_base") -> int:
    """Zählt die Anzahl der Tokens in einem Text"""
    try:
        encoding = tiktoken.get_encoding(encoding_name)
        return len(encoding.encode(text))
    except Exception:
        # Fallback: approximate 4 chars per token
        return len(text) // 4


def truncate_text(text: str, max_tokens: int = MAX_TOKENS, encoding_name: str = "cl100k_base") -> str:
    """Kürzt Text auf maximale Token-Anzahl"""
    try:
        encoding = tiktoken.get_encoding(encoding_name)
        tokens = encoding.encode(text)
        if len(tokens) <= max_tokens:
            return text
        # Truncate and decode back
        truncated_tokens = tokens[:max_tokens]
        return encoding.decode(truncated_tokens)
    except Exception:
        # Fallback: truncate by characters
        max_chars = max_tokens * 4
        return text[:max_chars] if len(text) > max_chars else text


def get_azure_openai_embedding(client: AzureOpenAI, text: str) -> Optional[List[float]]:
    """Generiert Embedding mit Azure OpenAI"""
    try:
        # Truncate if necessary
        truncated_text = truncate_text(text, MAX_TOKENS)
        if len(truncated_text) < len(text):
            print(f"⚠️  Text gekürzt: {len(text)} -> {len(truncated_text)} Zeichen ({count_tokens(text)} -> {count_tokens(truncated_text)} tokens)")
        
        response = client.embeddings.create(
            model=AZURE_OPENAI_EMBEDDING_DEPLOYMENT,
            input=truncated_text,
            dimensions=EMBEDDING_DIMENSIONS
        )
        return response.data[0].embedding
        
    except Exception as e:
        print(f"⚠️  Azure OpenAI API Fehler: {e}")
        return None


def get_azure_openai_embeddings_batch(client: AzureOpenAI, texts: List[str]) -> List[Optional[List[float]]]:
    """Generiert mehrere Embeddings auf einmal (bis zu 16 auf einmal)"""
    try:
        # Truncate texts if necessary
        truncated_texts = []
        for idx, text in enumerate(texts):
            truncated = truncate_text(text, MAX_TOKENS)
            if len(truncated) < len(text):
                token_count = count_tokens(text)
                truncated_count = count_tokens(truncated)
                print(f"⚠️  Text {idx+1} gekürzt: {token_count} -> {truncated_count} tokens")
            truncated_texts.append(truncated)
        
        # Azure OpenAI allows up to 16 inputs at once
        batch_size = 16
        all_embeddings = []
        
        for i in range(0, len(truncated_texts), batch_size):
            batch = truncated_texts[i:i+batch_size]
            response = client.embeddings.create(
                model=AZURE_OPENAI_EMBEDDING_DEPLOYMENT,
                input=batch,
                dimensions=EMBEDDING_DIMENSIONS
            )
            batch_embeddings = [data.embedding for data in response.data]
            all_embeddings.extend(batch_embeddings)
            
            # Small delay to avoid rate limits
            if i + batch_size < len(truncated_texts):
                time.sleep(0.1)
        
        return all_embeddings
        
    except Exception as e:
        print(f"⚠️  Azure OpenAI Batch API Fehler: {e}")
        return [None] * len(texts)


def get_chunks_without_embeddings(driver, sgb_filter: Optional[str] = None, limit: int = 1000):
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
            elementId(chunk) as chunk_id,
            chunk.text as text
        LIMIT $limit
    """
    
    with driver.session() as session:
        result = session.run(query, sgb=sgb_filter, limit=limit)
        return [dict(record) for record in result]


def update_chunk_embedding(driver, chunk_id: str, embedding: List[float]):
    """Speichert Embedding in Neo4j"""
    
    query = """
        MATCH (chunk:Chunk)
        WHERE elementId(chunk) = $chunk_id
        SET chunk.embedding = $embedding,
            chunk.embedding_model = $model,
            chunk.embedding_generated_at = datetime()
        RETURN elementId(chunk) as updated_id
    """
    
    with driver.session() as session:
        result = session.run(
            query, 
            chunk_id=chunk_id, 
            embedding=embedding,
            model=AZURE_OPENAI_EMBEDDING_DEPLOYMENT
        )
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
    parser = argparse.ArgumentParser(description="Generiere Embeddings mit Azure OpenAI")
    parser.add_argument("--execute", action="store_true", help="Embeddings generieren (ohne: Dry-Run)")
    parser.add_argument("--sgb", type=str, help="Nur bestimmte SGB (z.B. 'X')")
    parser.add_argument("--limit", type=int, default=1000, help="Max. Anzahl Chunks (default: 1000)")
    parser.add_argument("--batch", action="store_true", help="Batch-Modus (16 auf einmal, schneller)")
    
    args = parser.parse_args()
    
    print("\n" + "="*80)
    print("🤖 RAG System - Azure OpenAI Embedding Generator")
    print("="*80)
    print(f"\nModus: {'EXECUTE' if args.execute else 'DRY-RUN'}")
    print(f"SGB Filter: {args.sgb or 'Alle'}")
    print(f"Limit: {args.limit}")
    print(f"Batch-Modus: {'Ja (16 auf einmal)' if args.batch else 'Nein (einzeln)'}")
    
    # Check Azure OpenAI credentials
    if not AZURE_OPENAI_ENDPOINT or not AZURE_OPENAI_API_KEY:
        print("\n❌ Azure OpenAI Konfiguration fehlt!")
        print("   Setze AZURE_OPENAI_ENDPOINT und AZURE_OPENAI_API_KEY")
        print("   Führe aus: source setup_azure_openai.sh")
        return 1
    
    print(f"\n✅ Azure OpenAI Endpoint: {AZURE_OPENAI_ENDPOINT}")
    print(f"✅ Embedding Deployment: {AZURE_OPENAI_EMBEDDING_DEPLOYMENT}")
    
    # Initialize Azure OpenAI client
    try:
        client = AzureOpenAI(
            api_key=AZURE_OPENAI_API_KEY,
            api_version=AZURE_OPENAI_API_VERSION,
            azure_endpoint=AZURE_OPENAI_ENDPOINT
        )
        print("✅ Azure OpenAI Client initialisiert")
    except Exception as e:
        print(f"❌ Azure OpenAI Client Fehler: {e}")
        return 1
    
    # Connect to Neo4j
    print(f"\nVerbinde zu Neo4j: {NEO4J_URI}")
    try:
        driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))
        driver.verify_connectivity()
        print("✅ Neo4j Verbindung erfolgreich")
    except Exception as e:
        print(f"❌ Neo4j Verbindung fehlgeschlagen: {e}")
        return 1
    
    # Get chunks
    print(f"\n📊 Lade Chunks ohne Embeddings...")
    chunks = get_chunks_without_embeddings(driver, args.sgb, args.limit)
    
    if not chunks:
        print("✅ Alle Chunks haben bereits Embeddings!")
        driver.close()
        return 0
    
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
        print("   Beispiel: python scripts/generate_embeddings_azure.py --execute --batch")
        
        # Cost estimation
        tokens_per_chunk = 150  # Approximation
        total_tokens = len(chunks) * tokens_per_chunk
        cost = total_tokens / 1_000_000 * 0.10  # $0.10 per 1M tokens
        
        print(f"\n💰 Kosten-Schätzung (Azure OpenAI {AZURE_OPENAI_EMBEDDING_DEPLOYMENT}):")
        print(f"   ~{cost:.4f} USD für {len(chunks):,} Chunks (~{total_tokens:,} tokens)")
        print(f"   Rate Limit: 10 requests/10 seconds")
        print(f"   Geschätzte Dauer: ~{len(chunks) / 6:.1f} Minuten (einzeln)")
        if args.batch:
            print(f"   Geschätzte Dauer (Batch): ~{len(chunks) / 96:.1f} Minuten (16er Batches)")
        print("="*80)
        
        driver.close()
        return 0
    
    # Generate embeddings
    print("\n" + "="*80)
    print("🚀 Generiere Embeddings mit Azure OpenAI")
    print("="*80)
    
    success_count = 0
    error_count = 0
    start_time = time.time()
    
    if args.batch:
        # Batch mode: process 16 at a time
        batch_size = 16
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i:i+batch_size]
            texts = [chunk['text'] for chunk in batch]
            chunk_ids = [chunk['chunk_id'] for chunk in batch]
            
            # Generate embeddings
            embeddings = get_azure_openai_embeddings_batch(client, texts)
            
            # Update Neo4j
            for chunk_id, embedding in zip(chunk_ids, embeddings):
                if embedding is None:
                    error_count += 1
                    continue
                
                try:
                    update_chunk_embedding(driver, chunk_id, embedding)
                    success_count += 1
                except Exception as e:
                    print(f"❌ DB Fehler bei {chunk_id}: {e}")
                    error_count += 1
            
            processed = min(i + batch_size, len(chunks))
            elapsed = time.time() - start_time
            rate = success_count / elapsed if elapsed > 0 else 0
            eta = (len(chunks) - processed) / rate if rate > 0 else 0
            
            print(f"✅ {processed}/{len(chunks)}: {success_count} erfolgreich, {error_count} Fehler "
                  f"({rate:.1f}/s, ETA: {eta/60:.1f} min)")
    
    else:
        # Single mode
        for i, chunk in enumerate(chunks, 1):
            chunk_id = chunk['chunk_id']
            text = chunk['text']
            
            # Generate embedding
            embedding = get_azure_openai_embedding(client, text)
            
            if embedding is None:
                error_count += 1
                continue
            
            # Update Neo4j
            try:
                update_chunk_embedding(driver, chunk_id, embedding)
                success_count += 1
                
                if i % 10 == 0 or i == len(chunks):
                    elapsed = time.time() - start_time
                    rate = success_count / elapsed if elapsed > 0 else 0
                    eta = (len(chunks) - i) / rate if rate > 0 else 0
                    print(f"✅ {i}/{len(chunks)}: {success_count} erfolgreich, {error_count} Fehler "
                          f"({rate:.1f}/s, ETA: {eta/60:.1f} min)")
            
            except Exception as e:
                print(f"❌ {i}/{len(chunks)}: DB Fehler bei {chunk_id}: {e}")
                error_count += 1
            
            # Rate limiting
            time.sleep(1)  # 1 second between requests to stay within limits
    
    # Create vector index
    print("\n" + "="*80)
    print("📊 Erstelle Vector Index")
    print("="*80)
    
    create_vector_index(driver)
    
    # Summary
    elapsed_total = time.time() - start_time
    print("\n" + "="*80)
    print("📈 ZUSAMMENFASSUNG")
    print("="*80)
    print(f"✅ Erfolgreich: {success_count}/{len(chunks)}")
    print(f"❌ Fehler: {error_count}/{len(chunks)}")
    print(f"⏱️  Gesamtdauer: {elapsed_total/60:.2f} Minuten")
    print(f"📊 Durchschnitt: {success_count/elapsed_total:.1f} embeddings/second")
    
    if success_count > 0:
        print("\n🎉 Embeddings generiert!")
        print("\nNächste Schritte:")
        print("1. Vector Search testen:")
        print("   python scripts/test_vector_search.py 'Widerspruch einlegen'")
    
    print("="*80 + "\n")
    
    driver.close()
    return 0 if error_count == 0 else 1


if __name__ == "__main__":
    exit(main())
