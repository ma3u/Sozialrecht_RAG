#!/usr/bin/env python3
"""
GraphRAG Query System
Kombiniert Vector Search + Graph Traversal + LLM für intelligente Rechtsauskunft

Usage:
    python scripts/graphrag_query.py "Wie funktioniert das Widerspruchsverfahren?"
    python scripts/graphrag_query.py "Was besagt § 79 SGB X?" --sgb X
    python scripts/graphrag_query.py "Datenschutz Sozialdaten" --limit 10
"""

import os
import sys
import argparse
from typing import List, Dict, Optional
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
EMBEDDING_DIMENSIONS = int(os.getenv("EMBEDDING_DIMENSIONS", "1536"))


def get_query_embedding(query: str, use_mock: bool = False) -> Optional[List[float]]:
    """Generiert Embedding für Query"""
    
    if use_mock:
        import numpy as np
        vec = np.random.randn(EMBEDDING_DIMENSIONS)
        vec = vec / np.linalg.norm(vec)
        return vec.tolist()
    
    if not OPENAI_API_KEY or OPENAI_API_KEY == "sk-your-openai-api-key-here":
        print("⚠️  Kein OpenAI API Key - verwende Mock-Embedding")
        return get_query_embedding(query, use_mock=True)
    
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
        return get_query_embedding(query, use_mock=True)


def graphrag_search(driver, query_embedding: List[float], limit: int = 5, sgb_filter: Optional[str] = None):
    """
    GraphRAG: Vector Search + Graph Context
    
    1. Vector Search: Finde relevante Chunks
    2. Graph Traversal: Hole Kontext (Paragraph, Absätze, verwandte Normen)
    3. Return: Angereicherte Resultate mit Graph-Kontext
    """
    
    cypher_query = """
        // 1. Vector Search: Top K relevante Chunks
        CALL db.index.vector.queryNodes('chunk_embeddings', $limit, $query_embedding)
        YIELD node as chunk, score
        
        // 2. Graph Traversal: Hole Kontext
        MATCH (chunk)<-[:HAS_CHUNK]-(norm:LegalNorm)<-[:CONTAINS_NORM]-(doc:LegalDocument)
    """
    
    if sgb_filter:
        cypher_query += " WHERE doc.sgb_nummer = $sgb"
    
    cypher_query += """
        
        // 3. Sammle verwandte Chunks aus dem gleichen Paragraphen
        OPTIONAL MATCH (norm)-[:HAS_CHUNK]->(related_chunk:Chunk)
        WHERE related_chunk <> chunk
        
        // 4. Hole auch TextUnits (falls vorhanden)
        OPTIONAL MATCH (norm)-[:HAS_CONTENT]->(textunit:TextUnit)
        
        RETURN 
            // Haupt-Chunk
            chunk.chunk_id as chunk_id,
            chunk.text as chunk_text,
            score,
            
            // Norm-Context
            norm.paragraph_nummer as paragraph,
            norm.enbez as norm_titel,
            norm.titel as norm_beschreibung,
            
            // Document-Context
            doc.sgb_nummer as sgb,
            doc.title as doc_title,
            
            // Graph-Context: Verwandte Chunks
            collect(DISTINCT related_chunk.text)[0..3] as related_chunks,
            count(DISTINCT related_chunk) as total_related_chunks,
            
            // Graph-Context: TextUnits
            collect(DISTINCT textunit.text)[0..2] as absaetze
            
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


def generate_llm_response(query: str, graph_results: List[Dict], use_mock: bool = False):
    """Generiert LLM-Antwort basierend auf Graph-Kontext"""
    
    if use_mock or not OPENAI_API_KEY or OPENAI_API_KEY == "sk-your-openai-api-key-here":
        print("\n💡 Mock-Modus: Keine LLM-Generierung")
        return None
    
    try:
        import openai
        client = openai.OpenAI(api_key=OPENAI_API_KEY)
        
        # Baue Context aus Graph-Results
        context_parts = []
        for i, result in enumerate(graph_results[:3], 1):
            sgb = result['sgb']
            para = result['paragraph']
            titel = result['norm_titel']
            text = result['chunk_text']
            
            context_parts.append(f"\n[{i}] SGB {sgb} {para} ({titel}):\n{text[:300]}...")
        
        context = "\n".join(context_parts)
        
        prompt = f"""Du bist ein Experte für deutsches Sozialrecht. 
Beantworte die folgende Frage basierend AUSSCHLIESSLICH auf dem bereitgestellten Kontext.

KONTEXT:
{context}

FRAGE: {query}

ANTWORT (kurz und präzise, mit Quellenangaben):"""
        
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Du bist ein Sozialrechtsexperte."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=500
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        print(f"⚠️  LLM Generierung fehlgeschlagen: {e}")
        return None


def print_results(query: str, results: List[Dict], llm_response: Optional[str] = None):
    """Formatierte Ausgabe der Ergebnisse"""
    
    print("\n" + "="*80)
    print(f"📊 GRAPH RAG ERGEBNISSE")
    print("="*80)
    print(f"\n🔍 Query: \"{query}\"")
    print(f"✅ {len(results)} relevante Rechtsnormen gefunden\n")
    
    # LLM Antwort (falls vorhanden)
    if llm_response:
        print("="*80)
        print("🤖 KI-GENERIERTE ANTWORT")
        print("="*80)
        print(llm_response)
        print("\n" + "="*80)
        print("📚 QUELLEN & DETAILS")
        print("="*80)
    
    # Detaillierte Ergebnisse
    for i, result in enumerate(results, 1):
        score = result['score']
        sgb = result['sgb']
        para = result['paragraph']
        titel = result['norm_titel']
        text = result['chunk_text']
        related_count = result['total_related_chunks']
        
        print(f"\n{i}. Score: {score:.4f} | SGB {sgb} {para} ({titel})")
        print(f"   {'-' * 75}")
        
        # Haupt-Text
        display_text = text[:400] + "..." if len(text) > 400 else text
        print(f"   {display_text}")
        
        # Graph-Context
        if related_count > 0:
            print(f"\n   📊 Graph-Context: {related_count} verwandte Chunks im gleichen Paragraphen")
        
        # Absätze
        if result['absaetze'] and len(result['absaetze']) > 0:
            print(f"   📝 Absätze: {len(result['absaetze'])} weitere Absätze verfügbar")
    
    print("\n" + "="*80)


def main():
    parser = argparse.ArgumentParser(description="GraphRAG Query System")
    parser.add_argument("query", type=str, help="Rechts-Frage")
    parser.add_argument("--limit", type=int, default=5, help="Anzahl Ergebnisse (default: 5)")
    parser.add_argument("--sgb", type=str, help="Filter auf SGB (z.B. 'X')")
    parser.add_argument("--mock", action="store_true", help="Mock-Embedding verwenden (kein OpenAI)")
    parser.add_argument("--no-llm", action="store_true", help="Keine LLM-Generierung")
    
    args = parser.parse_args()
    
    print("\n" + "="*80)
    print("🤖 GRAPHRAG QUERY SYSTEM")
    print("="*80)
    print(f"\n🔍 Query: \"{args.query}\"")
    print(f"🎯 Top-K: {args.limit}")
    print(f"📚 SGB Filter: {args.sgb or 'Alle'}")
    print(f"🔧 Modus: {'Mock' if args.mock else 'OpenAI'}")
    
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
    
    # GraphRAG Search
    print(f"\n🔎 GraphRAG Suche (Vector + Graph Traversal)...")
    try:
        results = graphrag_search(driver, query_embedding, args.limit, args.sgb)
    except Exception as e:
        print(f"❌ GraphRAG Fehler: {e}")
        print("\nMögliche Ursachen:")
        print("  - Vector Index nicht verfügbar")
        print("  - Embeddings fehlen")
        driver.close()
        return 1
    
    if not results:
        print("⚠️  Keine Ergebnisse gefunden")
        driver.close()
        return 0
    
    print(f"✅ {len(results)} Ergebnisse gefunden")
    
    # Generate LLM Response (optional)
    llm_response = None
    if not args.no_llm and not args.mock:
        print(f"\n🤖 Generiere KI-Antwort mit GPT-4...")
        llm_response = generate_llm_response(args.query, results, use_mock=args.mock)
        if llm_response:
            print("✅ Antwort generiert")
    
    # Display results
    print_results(args.query, results, llm_response)
    
    print("\n💡 GraphRAG Features:")
    print("  ✅ Vector Search (semantische Ähnlichkeit)")
    print("  ✅ Graph Traversal (verwandte Chunks & Absätze)")
    print("  ✅ Context Enrichment (Paragraph-Kontext)")
    if llm_response:
        print("  ✅ LLM Generation (GPT-4 Antwort)")
    
    print("\n🔄 Weitere Queries:")
    print(f"  python scripts/graphrag_query.py 'Datenschutz DSGVO' --sgb X")
    print(f"  python scripts/graphrag_query.py 'Widerspruchsfrist' --limit 10")
    print()
    
    driver.close()
    return 0


if __name__ == "__main__":
    exit(main())
