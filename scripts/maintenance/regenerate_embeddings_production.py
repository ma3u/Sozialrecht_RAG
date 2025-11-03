#!/usr/bin/env python3
"""
Regenerate Embeddings for Production
Clears old embeddings and regenerates with Azure OpenAI text-embedding-3-large

This ensures all embeddings use the high-quality 3072-dimensional model
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from neo4j import GraphDatabase

sys.path.append(str(Path(__file__).parent.parent))
load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")


def clear_old_embeddings(driver):
    """Clear all existing embeddings from chunks"""
    print("\n" + "="*80)
    print("Clearing Old Embeddings")
    print("="*80)
    
    with driver.session() as session:
        # Count current embeddings
        result = session.run("MATCH (c:Chunk) WHERE c.embedding IS NOT NULL RETURN count(c) as count")
        old_count = result.single()['count']
        
        print(f"\n📊 Found {old_count:,} chunks with existing embeddings")
        print("These will be cleared to ensure consistent production quality.\n")
        
        if old_count == 0:
            print("✅ No embeddings to clear")
            return 0
        
        # Confirm
        response = input(f"Clear {old_count:,} existing embeddings? [yes/no]: ")
        if response.lower() not in ['yes', 'y']:
            print("❌ Operation cancelled")
            return None
        
        # Clear embeddings
        print("\n🗑️  Clearing embeddings...")
        result = session.run("""
            MATCH (c:Chunk)
            WHERE c.embedding IS NOT NULL
            REMOVE c.embedding
            REMOVE c.embedding_model
            REMOVE c.embedding_generated_at
            RETURN count(c) as cleared
        """)
        
        cleared = result.single()['cleared']
        print(f"✅ Cleared {cleared:,} embeddings")
        
        return cleared


def main():
    print("\n" + "="*80)
    print("PRODUCTION EMBEDDING REGENERATION")
    print("Azure OpenAI text-embedding-3-large (3072 dimensions)")
    print("="*80)
    
    # Check Azure credentials
    if not os.getenv("AZURE_OPENAI_API_KEY"):
        print("\n❌ AZURE_OPENAI_API_KEY not set!")
        print("Run: source setup_azure_openai.sh")
        return 1
    
    print(f"\n✅ Azure OpenAI configured")
    print(f"   Endpoint: {os.getenv('AZURE_OPENAI_ENDPOINT')}")
    print(f"   Deployment: {os.getenv('AZURE_OPENAI_EMBEDDING_DEPLOYMENT')}")
    
    # Connect to Neo4j
    print(f"\n📊 Connecting to Neo4j: {NEO4J_URI}")
    try:
        driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))
        driver.verify_connectivity()
        print("✅ Connected to Neo4j")
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return 1
    
    # Get stats
    with driver.session() as session:
        result = session.run("MATCH (c:Chunk) RETURN count(c) as total")
        total_chunks = result.single()['total']
    
    print(f"\n📈 Database Statistics:")
    print(f"   Total chunks: {total_chunks:,}")
    
    # Estimate
    print(f"\n💰 Cost Estimate:")
    tokens_per_chunk = 150
    total_tokens = total_chunks * tokens_per_chunk
    cost = total_tokens / 1_000_000 * 0.13  # $0.13 per 1M tokens for text-embedding-3-large
    print(f"   Estimated tokens: {total_tokens:,}")
    print(f"   Estimated cost: ${cost:.2f}")
    
    print(f"\n⏱️  Time Estimate:")
    print(f"   With batch mode (16 at a time): ~17 minutes")
    print(f"   With single mode: ~2 hours")
    
    print("\n" + "="*80)
    print("STEP 1: Clear Old Embeddings")
    print("="*80)
    
    cleared = clear_old_embeddings(driver)
    if cleared is None:
        driver.close()
        return 1
    
    print("\n" + "="*80)
    print("STEP 2: Generate New Embeddings")
    print("="*80)
    
    print("\nNow run the Azure embedding generator:")
    print("\n  python scripts/generate_embeddings_azure.py --execute --batch")
    print("\nThis will generate high-quality 3072-dimensional embeddings for all chunks.")
    print("\n" + "="*80)
    
    driver.close()
    return 0


if __name__ == "__main__":
    exit(main())
