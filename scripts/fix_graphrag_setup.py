#!/usr/bin/env python3
"""
Fix GraphRAG Setup - Create indexes and fix missing chunks
"""

import sys
import os
from pathlib import Path
import time

sys.path.append(str(Path(__file__).parent.parent))

from neo4j import GraphDatabase
from dotenv import load_dotenv
import logging

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

load_dotenv()


def create_vector_index(driver):
    """Create vector index for semantic search"""
    logger.info("\n" + "="*60)
    logger.info("Creating Vector Index for Semantic Search")
    logger.info("="*60)
    
    with driver.session() as session:
        # Check if index exists
        result = session.run("""
            SHOW INDEXES
            YIELD name, type
            WHERE type = 'VECTOR'
            RETURN name
        """)
        
        existing = [r['name'] for r in result]
        
        if 'chunk_embeddings' in existing:
            logger.info("✅ Vector index 'chunk_embeddings' already exists")
            return
        
        # Create vector index
        logger.info("Creating vector index 'chunk_embeddings'...")
        session.run("""
            CREATE VECTOR INDEX chunk_embeddings IF NOT EXISTS
            FOR (c:Chunk) ON (c.embedding)
            OPTIONS {
                indexConfig: {
                    `vector.dimensions`: 768,
                    `vector.similarity_function`: 'cosine'
                }
            }
        """)
        
        logger.info("✅ Vector index created!")
        logger.info("   Note: Index will populate in background")


def create_property_indexes(driver):
    """Create property indexes for fast lookups"""
    logger.info("\n" + "="*60)
    logger.info("Creating Property Indexes")
    logger.info("="*60)
    
    indexes = [
        ("INDEX idx_legal_doc_sgb IF NOT EXISTS FOR (d:LegalDocument) ON (d.sgb_nummer)", "LegalDocument.sgb_nummer"),
        ("INDEX idx_legal_norm_para IF NOT EXISTS FOR (n:LegalNorm) ON (n.paragraph_nummer)", "LegalNorm.paragraph_nummer"),
        ("INDEX idx_document_type IF NOT EXISTS FOR (d:Document) ON (d.document_type)", "Document.document_type"),
        ("INDEX idx_document_sgb IF NOT EXISTS FOR (d:Document) ON (d.sgb_nummer)", "Document.sgb_nummer"),
    ]
    
    with driver.session() as session:
        for idx_query, name in indexes:
            try:
                session.run(f"CREATE {idx_query}")
                logger.info(f"✅ Created index: {name}")
            except Exception as e:
                if "already exists" in str(e).lower() or "equivalent" in str(e).lower():
                    logger.info(f"⏭️  Index exists: {name}")
                else:
                    logger.warning(f"⚠️  Failed to create {name}: {e}")


def analyze_missing_chunks(driver):
    """Analyze which norms are missing chunks"""
    logger.info("\n" + "="*60)
    logger.info("Analyzing Missing Chunks")
    logger.info("="*60)
    
    with driver.session() as session:
        # Count by SGB
        result = session.run("""
            MATCH (norm:LegalNorm)
            WHERE NOT EXISTS {
              MATCH (norm)-[:HAS_CHUNK]->(:Chunk)
            }
            
            MATCH (doc:LegalDocument)-[:HAS_STRUCTURE]->()-[:CONTAINS_NORM]->(norm)
            
            RETURN 
              doc.sgb_nummer as sgb,
              COUNT(norm) as missing_count
            ORDER BY missing_count DESC
        """)
        
        records = list(result)
        
        if not records:
            logger.info("✅ All norms have chunks!")
            return
        
        total = sum(r['missing_count'] for r in records)
        logger.info(f"⚠️  Total norms without chunks: {total}")
        logger.info("\nBreakdown by SGB:")
        for r in records:
            logger.info(f"  SGB {r['sgb']}: {r['missing_count']} norms")
        
        # Sample missing norms
        result = session.run("""
            MATCH (norm:LegalNorm)
            WHERE NOT EXISTS {
              MATCH (norm)-[:HAS_CHUNK]->(:Chunk)
            }
            
            MATCH (doc:LegalDocument)-[:HAS_STRUCTURE]->()-[:CONTAINS_NORM]->(norm)
            
            RETURN 
              doc.sgb_nummer as sgb,
              norm.enbez as paragraph,
              norm.titel as title,
              size(norm.content_text) as text_length
            LIMIT 5
        """)
        
        logger.info("\nSample norms without chunks:")
        for r in result:
            logger.info(f"  [{r['sgb']}] {r['paragraph']}: {r['title']}")
            logger.info(f"       Text length: {r['text_length']} chars")


def check_graph_health(driver):
    """Check overall graph health"""
    logger.info("\n" + "="*60)
    logger.info("Graph Health Check")
    logger.info("="*60)
    
    with driver.session() as session:
        # XML Graph
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
        
        r = result.single()
        logger.info("XML Graph (from gesetze-im-internet.de):")
        logger.info(f"  Documents: {r['docs']}")
        logger.info(f"  Structures: {r['structures']}")
        logger.info(f"  Norms: {r['norms']}")
        logger.info(f"  Chunks: {r['chunks']}")
        
        if r['norms'] > 0:
            coverage = (r['chunks'] / r['norms']) * 100 if r['norms'] > 0 else 0
            logger.info(f"  Chunk coverage: {coverage:.1f}%")
        
        # PDF Graph
        result = session.run("""
            MATCH (d:Document)
            OPTIONAL MATCH (d)-[:HAS_CHUNK]->(c:Chunk)
            OPTIONAL MATCH (d)-[:CONTAINS_PARAGRAPH]->(p:Paragraph)
            RETURN
              COUNT(DISTINCT d) as docs,
              COUNT(DISTINCT c) as chunks,
              COUNT(DISTINCT p) as paragraphs
        """)
        
        r = result.single()
        logger.info("\nPDF Graph (from Handlungsanweisungen):")
        logger.info(f"  Documents: {r['docs']}")
        logger.info(f"  Chunks: {r['chunks']}")
        logger.info(f"  Paragraphs: {r['paragraphs']}")


def verify_vector_index(driver):
    """Verify vector index is working"""
    logger.info("\n" + "="*60)
    logger.info("Verifying Vector Index")
    logger.info("="*60)
    
    with driver.session() as session:
        # Wait for index to be online
        max_wait = 30
        for i in range(max_wait):
            result = session.run("""
                SHOW INDEXES
                YIELD name, type, state
                WHERE name = 'chunk_embeddings' AND type = 'VECTOR'
                RETURN state
            """)
            
            record = result.single()
            if record and record['state'] == 'ONLINE':
                logger.info("✅ Vector index is ONLINE")
                
                # Test query
                result = session.run("""
                    MATCH (c:Chunk)
                    WHERE c.embedding IS NOT NULL
                    RETURN COUNT(c) as indexed_chunks
                """)
                
                count = result.single()['indexed_chunks']
                logger.info(f"✅ Indexed chunks: {count}")
                return True
            
            if i < max_wait - 1:
                time.sleep(1)
        
        logger.warning("⚠️  Vector index still populating (this is normal)")
        logger.info("   Check status with: SHOW INDEXES WHERE name = 'chunk_embeddings'")
        return False


def main():
    print("\n🔧 GraphRAG Setup & Optimization")
    print("="*60)
    
    uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    username = os.getenv("NEO4J_USERNAME", "neo4j")
    password = os.getenv("NEO4J_PASSWORD")
    
    if not password:
        logger.error("❌ NEO4J_PASSWORD not set in .env")
        return 1
    
    driver = GraphDatabase.driver(uri, auth=(username, password))
    
    try:
        # Check graph health
        check_graph_health(driver)
        
        # Create indexes
        create_vector_index(driver)
        create_property_indexes(driver)
        
        # Verify vector index
        verify_vector_index(driver)
        
        # Analyze issues
        analyze_missing_chunks(driver)
        
        logger.info("\n" + "="*60)
        logger.info("✅ GraphRAG setup complete!")
        logger.info("="*60)
        logger.info("\nNext steps:")
        logger.info("1. Wait ~30s for vector index to populate")
        logger.info("2. Re-run efficiency tests: python scripts/test_graphrag_efficiency.py")
        logger.info("3. If chunks are still missing, re-import SGB II: python quick_import_sgb2.py")
        
    finally:
        driver.close()
    
    return 0


if __name__ == "__main__":
    exit(main())
