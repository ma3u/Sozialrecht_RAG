#!/usr/bin/env python3
"""
Test GraphRAG Import Efficiency with Real-World Use Cases
Tests both XML-based and PDF-based RAG queries with performance metrics
"""

import sys
import os
from pathlib import Path
import time
from typing import Dict, List, Tuple
import json

# Add src to path
sys.path.append(str(Path(__file__).parent.parent))

from neo4j import GraphDatabase
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

load_dotenv()


class GraphRAGEfficiencyTester:
    """Test GraphRAG efficiency with realistic use cases"""
    
    def __init__(self):
        self.uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        self.username = os.getenv("NEO4J_USERNAME", "neo4j")
        self.password = os.getenv("NEO4J_PASSWORD")
        
        if not self.password:
            raise ValueError("❌ NEO4J_PASSWORD not set in .env")
        
        self.driver = GraphDatabase.driver(self.uri, auth=(self.username, self.password))
        
        # Load embedding model for semantic search
        logger.info("Loading embedding model...")
        self.embedding_model = SentenceTransformer('paraphrase-multilingual-mpnet-base-v2')
        logger.info("✅ Embedding model loaded")
        
        self.results = []
    
    def close(self):
        self.driver.close()
    
    def run_timed_query(self, name: str, query: str, params: Dict = None) -> Tuple[float, List]:
        """Execute query and measure time"""
        start = time.time()
        
        with self.driver.session() as session:
            result = session.run(query, params or {})
            records = list(result)
        
        elapsed = time.time() - start
        
        self.results.append({
            'test': name,
            'time_ms': round(elapsed * 1000, 2),
            'records': len(records),
            'status': '✅' if elapsed < 1.0 else '⚠️' if elapsed < 3.0 else '❌'
        })
        
        return elapsed, records
    
    def test_graph_statistics(self):
        """Test 1: Basic Graph Statistics"""
        logger.info("\n" + "="*60)
        logger.info("TEST 1: Graph Statistics (Overall Health Check)")
        logger.info("="*60)
        
        query = """
        MATCH (d:Document)
        OPTIONAL MATCH (d)-[:HAS_CHUNK]->(c:Chunk)
        OPTIONAL MATCH (d)-[:CONTAINS_PARAGRAPH]->(p:Paragraph)
        RETURN
          COUNT(DISTINCT d) as documents,
          COUNT(DISTINCT c) as chunks,
          COUNT(DISTINCT p) as paragraphs,
          CASE WHEN COUNT(c) > 0 THEN AVG(SIZE(c.embedding)) ELSE 0 END as avg_embedding_dim
        """
        
        elapsed, records = self.run_timed_query("Graph Statistics", query)
        
        if records:
            r = records[0]
            logger.info(f"  Documents: {r['documents']}")
            logger.info(f"  Chunks: {r['chunks']}")
            logger.info(f"  Paragraphs: {r['paragraphs']}")
            logger.info(f"  Embedding Dimension: {r['avg_embedding_dim']}")
            logger.info(f"  ⏱️  Time: {elapsed*1000:.2f}ms")
    
    def test_xml_graph_statistics(self):
        """Test 1b: XML Graph Statistics (LegalNorm based)"""
        logger.info("\n" + "="*60)
        logger.info("TEST 1b: XML Legal Graph Statistics")
        logger.info("="*60)
        
        query = """
        MATCH (doc:LegalDocument)
        OPTIONAL MATCH (doc)-[:HAS_STRUCTURE]->(struct:StructuralUnit)
        OPTIONAL MATCH (struct)-[:CONTAINS_NORM]->(norm:LegalNorm)
        OPTIONAL MATCH (norm)-[:HAS_CHUNK]->(chunk:Chunk)
        RETURN
          COUNT(DISTINCT doc) as legal_documents,
          COUNT(DISTINCT struct) as structures,
          COUNT(DISTINCT norm) as legal_norms,
          COUNT(DISTINCT chunk) as chunks,
          CASE WHEN COUNT(chunk) > 0 THEN AVG(SIZE(chunk.embedding)) ELSE 0 END as avg_embedding_dim
        """
        
        elapsed, records = self.run_timed_query("XML Graph Statistics", query)
        
        if records:
            r = records[0]
            logger.info(f"  Legal Documents: {r['legal_documents']}")
            logger.info(f"  Structures: {r['structures']}")
            logger.info(f"  Legal Norms: {r['legal_norms']}")
            logger.info(f"  Chunks: {r['chunks']}")
            logger.info(f"  Embedding Dimension: {r['avg_embedding_dim']}")
            logger.info(f"  ⏱️  Time: {elapsed*1000:.2f}ms")
    
    def test_use_case_regelbedarf(self):
        """Test 2: Use Case - Regelbedarf § 20 SGB II (Most common query)"""
        logger.info("\n" + "="*60)
        logger.info("TEST 2: Use Case - Regelbedarf § 20 SGB II")
        logger.info("="*60)
        
        # Test with XML schema
        query = """
        MATCH (doc:LegalDocument {sgb_nummer: "II"})
        -[:HAS_STRUCTURE]->(struct:StructuralUnit)
        -[:CONTAINS_NORM]->(norm:LegalNorm)
        WHERE norm.paragraph_nummer = "20"
        
        MATCH (norm)-[:HAS_CONTENT]->(text:TextUnit)
        OPTIONAL MATCH (norm)-[:HAS_CHUNK]->(chunk:Chunk)
        
        RETURN 
          doc.jurabk as gesetz,
          struct.gliederungsbez as kapitel,
          norm.enbez as paragraph,
          norm.titel as titel,
          COLLECT(DISTINCT text.text)[0..3] as first_texts,
          COUNT(DISTINCT chunk) as chunk_count
        """
        
        elapsed, records = self.run_timed_query("§20 SGB II Direct Lookup", query)
        
        if records:
            r = records[0]
            logger.info(f"  Found: {r['paragraph']} - {r['titel']}")
            logger.info(f"  Kapitel: {r['kapitel']}")
            logger.info(f"  Chunks: {r['chunk_count']}")
            logger.info(f"  ⏱️  Time: {elapsed*1000:.2f}ms")
            
            # Show sample text
            if r['first_texts']:
                logger.info(f"  📄 Sample: {r['first_texts'][0][:100]}...")
    
    def test_use_case_leistungsberechtigung(self):
        """Test 3: Use Case - Leistungsberechtigung §§ 7-9 SGB II"""
        logger.info("\n" + "="*60)
        logger.info("TEST 3: Use Case - Leistungsberechtigung §§ 7-9 SGB II")
        logger.info("="*60)
        
        query = """
        MATCH (doc:LegalDocument {sgb_nummer: "II"})
        -[:HAS_STRUCTURE]->(struct:StructuralUnit)
        -[:CONTAINS_NORM]->(norm:LegalNorm)
        WHERE norm.paragraph_nummer IN ["7", "8", "9"]
        
        MATCH (norm)-[:HAS_CONTENT]->(text:TextUnit)
        
        RETURN 
          norm.paragraph_nummer as paragraph_nr,
          norm.enbez as paragraph,
          norm.titel as titel,
          COUNT(text) as text_units
        ORDER BY norm.paragraph_nummer
        """
        
        elapsed, records = self.run_timed_query("§§7-9 SGB II Batch Lookup", query)
        
        logger.info(f"  Found {len(records)} paragraphs")
        for r in records:
            logger.info(f"    {r['paragraph']}: {r['titel']} ({r['text_units']} units)")
        logger.info(f"  ⏱️  Time: {elapsed*1000:.2f}ms")
    
    def test_use_case_semantic_search(self):
        """Test 4: Semantic Search - "Regelbedarfe" across all documents"""
        logger.info("\n" + "="*60)
        logger.info("TEST 4: Semantic Search - 'Regelbedarfe'")
        logger.info("="*60)
        
        # Generate embedding
        query_text = "Regelbedarfe für Alleinstehende"
        logger.info(f"  Query: '{query_text}'")
        
        start_embed = time.time()
        embedding = self.embedding_model.encode(query_text).tolist()
        embed_time = time.time() - start_embed
        logger.info(f"  ⏱️  Embedding generation: {embed_time*1000:.2f}ms")
        
        # Check if vector index exists
        check_index_query = """
        SHOW INDEXES
        YIELD name, type, labelsOrTypes, properties
        WHERE type = 'VECTOR'
        RETURN name, labelsOrTypes, properties
        """
        
        with self.driver.session() as session:
            indexes = list(session.run(check_index_query))
        
        if not indexes:
            logger.warning("  ⚠️  No vector index found! Semantic search will be slow.")
            logger.info("  To create index, run:")
            logger.info("    CREATE VECTOR INDEX chunk_embeddings IF NOT EXISTS")
            logger.info("    FOR (c:Chunk) ON (c.embedding)")
            logger.info("    OPTIONS {indexConfig: {`vector.dimensions`: 768, `vector.similarity_function`: 'cosine'}}")
            return
        
        logger.info(f"  ✅ Vector index found: {indexes[0]['name']}")
        
        # Semantic search
        query = """
        CALL db.index.vector.queryNodes('chunk_embeddings', 5, $embedding)
        YIELD node as chunk, score
        
        MATCH (norm:LegalNorm)-[:HAS_CHUNK]->(chunk)
        MATCH (doc:LegalDocument)-[:HAS_STRUCTURE]->()-[:CONTAINS_NORM]->(norm)
        
        RETURN 
          score as relevance,
          doc.sgb_nummer as sgb,
          norm.enbez as paragraph,
          norm.titel as titel,
          SUBSTRING(chunk.text, 0, 150) as text_preview
        ORDER BY score DESC
        """
        
        elapsed, records = self.run_timed_query("Semantic Search 'Regelbedarfe'", query, {'embedding': embedding})
        
        logger.info(f"  Found {len(records)} relevant chunks")
        for i, r in enumerate(records[:3], 1):
            logger.info(f"    {i}. [{r['sgb']}] {r['paragraph']}: {r['titel']}")
            logger.info(f"       Relevance: {r['relevance']:.4f}")
            logger.info(f"       Preview: {r['text_preview']}...")
        logger.info(f"  ⏱️  Total time: {elapsed*1000:.2f}ms")
    
    def test_use_case_antragspruefung(self):
        """Test 5: Complete Application Check Workflow"""
        logger.info("\n" + "="*60)
        logger.info("TEST 5: Complete Antragsprüfung Workflow")
        logger.info("="*60)
        
        query = """
        MATCH (doc:LegalDocument {sgb_nummer: "II"})
        -[:HAS_STRUCTURE]->()-[:CONTAINS_NORM]->(norm:LegalNorm)
        WHERE norm.paragraph_nummer IN [
          "7",   // Leistungsberechtigte
          "8",   // Erwerbsfähigkeit
          "9",   // Hilfebedürftigkeit
          "11",  // Einkommen
          "12",  // Vermögen
          "20",  // Regelbedarf
          "21",  // Mehrbedarf
          "22"   // Kosten der Unterkunft
        ]
        
        RETURN 
          norm.paragraph_nummer as step,
          norm.enbez as paragraph,
          norm.titel as check_point
        ORDER BY step
        """
        
        elapsed, records = self.run_timed_query("Antragsprüfung Workflow", query)
        
        logger.info(f"  Workflow has {len(records)} check points:")
        for i, r in enumerate(records, 1):
            logger.info(f"    {i}. {r['paragraph']}: {r['check_point']}")
        logger.info(f"  ⏱️  Time: {elapsed*1000:.2f}ms")
    
    def test_use_case_cross_sgb(self):
        """Test 6: Cross-SGB Query - Find related norms"""
        logger.info("\n" + "="*60)
        logger.info("TEST 6: Cross-SGB Analysis - Income regulations")
        logger.info("="*60)
        
        query = """
        MATCH (norm:LegalNorm)
        WHERE norm.paragraph_nummer = "11" 
          AND EXISTS {
            MATCH (norm)<-[:CONTAINS_NORM]-()<-[:HAS_STRUCTURE]-
                  (doc:LegalDocument {sgb_nummer: "II"})
          }
        
        MATCH (norm)-[:HAS_CHUNK]->(chunk:Chunk)
        WITH chunk.embedding as query_embedding
        LIMIT 1
        
        CALL db.index.vector.queryNodes('chunk_embeddings', 5, query_embedding)
        YIELD node as similar_chunk, score
        
        MATCH (related_norm:LegalNorm)-[:HAS_CHUNK]->(similar_chunk)
        MATCH (related_doc:LegalDocument)-[:HAS_STRUCTURE]->()
              -[:CONTAINS_NORM]->(related_norm)
        WHERE related_doc.sgb_nummer <> "II"
        
        RETURN 
          score as similarity,
          related_doc.sgb_nummer as other_sgb,
          related_norm.enbez as paragraph,
          related_norm.titel as titel
        ORDER BY score DESC
        """
        
        try:
            elapsed, records = self.run_timed_query("Cross-SGB Income Analysis", query)
            
            logger.info(f"  Found {len(records)} related norms in other SGBs:")
            for r in records[:3]:
                logger.info(f"    [{r['other_sgb']}] {r['paragraph']}: {r['titel']}")
                logger.info(f"       Similarity: {r['similarity']:.4f}")
            logger.info(f"  ⏱️  Time: {elapsed*1000:.2f}ms")
        except Exception as e:
            logger.warning(f"  ⚠️  Cross-SGB query failed (requires vector index): {e}")
    
    def test_use_case_pdf_search(self):
        """Test 7: PDF-based Document Search (Handlungsanweisungen)"""
        logger.info("\n" + "="*60)
        logger.info("TEST 7: PDF Document Search - Handlungsanweisungen")
        logger.info("="*60)
        
        query = """
        MATCH (d:Document)
        WHERE d.document_type = "Fachliche Weisung"
        OPTIONAL MATCH (d)-[:HAS_CHUNK]->(c:Chunk)
        RETURN 
          d.filename as filename,
          d.sgb_nummer as sgb,
          d.trust_score as trust,
          COUNT(c) as chunk_count
        ORDER BY d.trust_score DESC
        LIMIT 10
        """
        
        elapsed, records = self.run_timed_query("PDF Handlungsanweisungen Query", query)
        
        logger.info(f"  Found {len(records)} Handlungsanweisungen:")
        for i, r in enumerate(records[:5], 1):
            logger.info(f"    {i}. [{r['sgb']}] {r['filename']}")
            logger.info(f"       Trust: {r['trust']:.2f}, Chunks: {r['chunk_count']}")
        logger.info(f"  ⏱️  Time: {elapsed*1000:.2f}ms")
    
    def test_quality_check(self):
        """Test 8: Quality Check - Data Completeness"""
        logger.info("\n" + "="*60)
        logger.info("TEST 8: Quality Check - Data Completeness")
        logger.info("="*60)
        
        # Check norms without chunks
        query = """
        MATCH (norm:LegalNorm)
        WHERE NOT EXISTS {
          MATCH (norm)-[:HAS_CHUNK]->(:Chunk)
        }
        
        MATCH (doc:LegalDocument)-[:HAS_STRUCTURE]->()-[:CONTAINS_NORM]->(norm)
        
        RETURN 
          doc.sgb_nummer as sgb,
          COUNT(norm) as norms_without_chunks
        ORDER BY norms_without_chunks DESC
        """
        
        elapsed, records = self.run_timed_query("Quality Check - Missing Chunks", query)
        
        if records:
            total_missing = sum(r['norms_without_chunks'] for r in records)
            logger.info(f"  Total norms without chunks: {total_missing}")
            for r in records:
                logger.info(f"    SGB {r['sgb']}: {r['norms_without_chunks']} norms")
        else:
            logger.info("  ✅ All norms have chunks!")
        logger.info(f"  ⏱️  Time: {elapsed*1000:.2f}ms")
    
    def print_summary(self):
        """Print test summary"""
        logger.info("\n" + "="*70)
        logger.info("TEST SUMMARY - GraphRAG Efficiency")
        logger.info("="*70)
        
        print(f"\n{'Test':<40} {'Time (ms)':<12} {'Records':<10} {'Status'}")
        print("-" * 70)
        
        for r in self.results:
            print(f"{r['test']:<40} {r['time_ms']:<12} {r['records']:<10} {r['status']}")
        
        print("-" * 70)
        
        total_time = sum(r['time_ms'] for r in self.results)
        avg_time = total_time / len(self.results)
        
        fast = sum(1 for r in self.results if r['status'] == '✅')
        medium = sum(1 for r in self.results if r['status'] == '⚠️')
        slow = sum(1 for r in self.results if r['status'] == '❌')
        
        print(f"\nTotal Tests: {len(self.results)}")
        print(f"Fast (< 1s): {fast} ✅")
        print(f"Medium (1-3s): {medium} ⚠️")
        print(f"Slow (> 3s): {slow} ❌")
        print(f"\nTotal Time: {total_time:.2f}ms")
        print(f"Average Time: {avg_time:.2f}ms")
        
        logger.info("\n" + "="*70)


def main():
    print("\n🧪 GraphRAG Efficiency Test Suite")
    print("="*70)
    print("Testing both XML-based and PDF-based RAG queries")
    print("="*70)
    
    tester = GraphRAGEfficiencyTester()
    
    try:
        # Run all tests
        tester.test_graph_statistics()
        tester.test_xml_graph_statistics()
        tester.test_use_case_regelbedarf()
        tester.test_use_case_leistungsberechtigung()
        tester.test_use_case_semantic_search()
        tester.test_use_case_antragspruefung()
        tester.test_use_case_cross_sgb()
        tester.test_use_case_pdf_search()
        tester.test_quality_check()
        
        # Print summary
        tester.print_summary()
        
        # Save results
        output_file = Path(__file__).parent.parent / "logs" / "graphrag_efficiency_test.json"
        output_file.parent.mkdir(exist_ok=True)
        
        with open(output_file, 'w') as f:
            json.dump({
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
                'tests': tester.results
            }, f, indent=2)
        
        print(f"\n📊 Results saved to: {output_file}")
        
    finally:
        tester.close()
    
    print("\n✅ Test suite completed!")


if __name__ == "__main__":
    main()
