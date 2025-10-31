#!/usr/bin/env python3
"""
GraphRAG Status Summary - Complete overview of the system
"""

import sys
import os
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()


def print_status():
    uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    username = os.getenv("NEO4J_USERNAME", "neo4j")
    password = os.getenv("NEO4J_PASSWORD")
    
    driver = GraphDatabase.driver(uri, auth=(username, password))
    
    print("\n" + "="*70)
    print("📊 GRAPHRAG STATUS SUMMARY")
    print("="*70)
    
    with driver.session() as session:
        # XML Graph stats
        result = session.run("""
            MATCH (doc:LegalDocument)
            OPTIONAL MATCH (doc)-[:HAS_STRUCTURE]->(struct:StructuralUnit)
            OPTIONAL MATCH (struct)-[:CONTAINS_NORM]->(norm:LegalNorm)
            OPTIONAL MATCH (norm)-[:HAS_CHUNK]->(chunk:Chunk)
            RETURN
              COUNT(DISTINCT doc) as docs,
              COUNT(DISTINCT struct) as structures,
              COUNT(DISTINCT norm) as norms,
              COUNT(DISTINCT chunk) as chunks
        """)
        
        xml_stats = result.single()
        
        # PDF Graph stats
        result = session.run("""
            MATCH (d:Document)
            OPTIONAL MATCH (d)-[:HAS_CHUNK]->(c:Chunk)
            OPTIONAL MATCH (d)-[:CONTAINS_PARAGRAPH]->(p:Paragraph)
            RETURN
              COUNT(DISTINCT d) as docs,
              COUNT(DISTINCT c) as chunks,
              COUNT(DISTINCT p) as paragraphs
        """)
        
        pdf_stats = result.single()
        
        # Check vector index
        result = session.run("""
            SHOW INDEXES
            YIELD name, type, state
            WHERE name = 'chunk_embeddings' AND type = 'VECTOR'
            RETURN state
        """)
        
        vector_index = result.single()
        vector_status = vector_index['state'] if vector_index else "NOT CREATED"
        
        # Count indexed chunks
        result = session.run("""
            MATCH (c:Chunk)
            WHERE c.embedding IS NOT NULL
            RETURN COUNT(c) as count
        """)
        
        indexed_chunks = result.single()['count']
    
    print("\n📚 XML GRAPH (Gesetze from gesetze-im-internet.de)")
    print("-" * 70)
    print(f"  Legal Documents:      {xml_stats['docs']:>6}")
    print(f"  Structural Units:     {xml_stats['structures']:>6}")
    print(f"  Legal Norms:          {xml_stats['norms']:>6}")
    print(f"  Chunks (with embed):  {xml_stats['chunks']:>6}")
    
    if xml_stats['norms'] > 0:
        coverage = (xml_stats['chunks'] / xml_stats['norms']) * 100
        print(f"  Coverage:             {coverage:>5.1f}%")
        if coverage < 100:
            missing = xml_stats['norms'] - xml_stats['chunks']
            print(f"  ⚠️  Missing chunks:    {missing:>6}")
    
    print("\n📄 PDF GRAPH (Handlungsanweisungen)")
    print("-" * 70)
    print(f"  Documents:            {pdf_stats['docs']:>6}")
    print(f"  Chunks (with embed):  {pdf_stats['chunks']:>6}")
    print(f"  Paragraphs:           {pdf_stats['paragraphs']:>6}")
    
    print("\n🔍 VECTOR INDEX (Semantic Search)")
    print("-" * 70)
    print(f"  Status:               {vector_status}")
    print(f"  Indexed Chunks:       {indexed_chunks:>6}")
    print(f"  Total Chunks:         {xml_stats['chunks'] + pdf_stats['chunks']:>6}")
    
    if vector_status == "ONLINE":
        print(f"  ✅ Ready for semantic search!")
    else:
        print(f"  ⚠️  Vector index not ready")
    
    print("\n💡 CAPABILITIES")
    print("-" * 70)
    print("  ✅ Structured XML queries (LegalNorm hierarchy)")
    print("  ✅ PDF document search (Handlungsanweisungen)")
    if vector_status == "ONLINE":
        print("  ✅ Semantic search across all documents")
    else:
        print("  ❌ Semantic search (vector index not ready)")
    print("  ✅ Cross-SGB queries")
    print("  ✅ Graph relationships and workflows")
    
    print("\n📈 PERFORMANCE")
    print("-" * 70)
    
    if Path("logs/graphrag_efficiency_test.json").exists():
        import json
        with open("logs/graphrag_efficiency_test.json") as f:
            data = json.load(f)
        
        fast = sum(1 for t in data['tests'] if t['status'] == '✅')
        total = len(data['tests'])
        avg_time = sum(t['time_ms'] for t in data['tests']) / total
        
        print(f"  Last test run:        {data['timestamp']}")
        print(f"  Tests passed:         {fast}/{total}")
        print(f"  Average query time:   {avg_time:.2f}ms")
    else:
        print("  No test results available")
        print("  Run: python scripts/test_graphrag_efficiency.py")
    
    print("\n" + "="*70)
    
    driver.close()


if __name__ == "__main__":
    print_status()
