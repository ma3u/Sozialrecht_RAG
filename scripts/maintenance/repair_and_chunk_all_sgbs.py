#!/usr/bin/env python3
"""
Repair and Chunk All SGBs
Checks if norms have content, regenerates from XML if needed, then creates chunks
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from neo4j import GraphDatabase
import os
import logging
from typing import List, Dict
from src.xml_legal_parser import LegalXMLParser

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Neo4j connection
NEO4J_URI = os.environ.get("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.environ.get("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.environ.get("NEO4J_PASSWORD", "password")

driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

XML_CACHE_DIR = Path(__file__).parent.parent / "xml_cache"

# Map SGB numbers to directory names
SGB_DIR_MAP = {
    "I": "sgb_1",
    "II": "sgb_2",
    "III": "sgb_3",
    "IV": "sgb_4",
    "V": "sgb_5",
    "VI": "sgb_6",
    "VII": "sgb_7",
    "VIII": "sgb_8",
    "IX": "sgb_9_2018",  # Using newer version
    "X": "sgb_10",
    "XI": "sgb_11",
    "XII": "sgb_12",
    "XIV": "sgb_14"
}


def get_sgb_stats(tx):
    """Get stats for all SGBs"""
    query = """
    MATCH (doc:LegalDocument)
    WHERE doc.sgb_nummer IS NOT NULL
    WITH doc
    MATCH (doc)-[:HAS_STRUCTURE|CONTAINS_NORM*1..3]->(norm:LegalNorm)
    OPTIONAL MATCH (norm)-[:HAS_CHUNK]->(chunk:Chunk)
    WITH doc.sgb_nummer as sgb, 
         count(DISTINCT norm) as total_norms,
         count(DISTINCT chunk) as total_chunks,
         collect(DISTINCT CASE WHEN norm.content_text = '' OR norm.content_text IS NULL THEN norm.id ELSE NULL END) as empty_norms
    RETURN sgb, total_norms, total_chunks, 
           size([n IN empty_norms WHERE n IS NOT NULL]) as norms_without_content
    ORDER BY sgb
    """
    result = tx.run(query)
    return [dict(record) for record in result]


def get_norms_without_content(tx, sgb_nummer: str) -> List[Dict]:
    """Get norms that have no content"""
    query = """
    MATCH (doc:LegalDocument {sgb_nummer: $sgb_nummer})-[:HAS_STRUCTURE|CONTAINS_NORM*1..3]->(norm:LegalNorm)
    WHERE norm.content_text = '' OR norm.content_text IS NULL
    RETURN norm.id as norm_id, 
           norm.norm_doknr as norm_doknr,
           norm.enbez as enbez
    LIMIT 50
    """
    result = tx.run(query, sgb_nummer=sgb_nummer)
    return [dict(record) for record in result]


def link_orphaned_norms_for_sgb(tx, sgb_nummer: str) -> int:
    """Link orphaned norms to their document by matching norm_doknr prefix"""
    query = """
    // Find the document
    MATCH (doc:LegalDocument {sgb_nummer: $sgb_nummer})
    
    // Find orphaned norms with matching doknr prefix
    MATCH (norm:LegalNorm)
    WHERE norm.norm_doknr STARTS WITH doc.doknr
      AND NOT EXISTS((doc)-[:HAS_STRUCTURE|CONTAINS_NORM*1..10]-(norm))
    
    // Create relationship
    MERGE (doc)-[:CONTAINS_NORM]->(norm)
    
    RETURN count(norm) as linked_count
    """
    result = tx.run(query, sgb_nummer=sgb_nummer)
    record = result.single()
    return record['linked_count'] if record else 0


def reimport_sgb_from_xml(sgb_nummer: str):
    """Reimport an SGB from XML to fix content"""
    # Find the XML file in the cache directory
    sgb_dir_name = SGB_DIR_MAP.get(sgb_nummer)
    if not sgb_dir_name:
        logger.error(f"❌ No directory mapping for SGB {sgb_nummer}")
        return False
    
    sgb_dir = XML_CACHE_DIR / sgb_dir_name
    if not sgb_dir.exists():
        logger.error(f"❌ Directory not found: {sgb_dir}")
        return False
    
    # Find the XML file (there should be one .xml file per directory)
    xml_files = list(sgb_dir.glob("*.xml"))
    if not xml_files:
        logger.error(f"❌ No XML file found in: {sgb_dir}")
        return False
    
    xml_file = xml_files[0]
    logger.info(f"📖 Re-parsing XML: {xml_file}")
    
    parser = LegalXMLParser()
    document = parser.parse_dokument(xml_file)
    
    # Update norms in database
    with driver.session() as session:
        for norm in document.norms:
            if norm.content_text.strip():
                session.execute_write(update_norm_content, norm)
    
    logger.info(f"✅ Updated {len(document.norms)} norms for SGB {sgb_nummer}")
    return True


def update_norm_content(tx, norm):
    """Update norm content in database"""
    query = """
    MATCH (norm:LegalNorm {norm_doknr: $norm_doknr})
    SET norm.content_text = $content_text
    RETURN norm.id as norm_id
    """
    result = tx.run(query, 
                   norm_doknr=norm.norm_doknr,
                   content_text=norm.content_text)
    return result.single()


def generate_chunks_for_sgb(tx, sgb_nummer: str) -> int:
    """Generate chunks for an SGB using RecursiveCharacterTextSplitter"""
    query = """
    MATCH (doc:LegalDocument {sgb_nummer: $sgb_nummer})-[:HAS_STRUCTURE|CONTAINS_NORM*1..3]->(norm:LegalNorm)
    WHERE norm.content_text IS NOT NULL 
      AND norm.content_text <> ''
      AND NOT EXISTS((norm)-[:HAS_CHUNK]->(:Chunk))
    WITH norm, norm.content_text as text
    WHERE size(text) > 50
    // Split into chunks (simple approach - 1000 chars per chunk with 200 char overlap)
    WITH norm, text,
         range(0, size(text), 800) as starts
    UNWIND starts as start
    WITH norm, 
         substring(text, start, 1000) as chunk_text,
         start,
         start / 800 as chunk_idx
    WHERE size(trim(chunk_text)) > 50
    CREATE (chunk:Chunk {
        id: randomUUID(),
        text: chunk_text,
        chunk_index: chunk_idx,
        start_char: start,
        end_char: start + size(chunk_text),
        source: 'norm_content'
    })
    CREATE (norm)-[:HAS_CHUNK]->(chunk)
    RETURN count(chunk) as chunks_created
    """
    result = tx.run(query, sgb_nummer=sgb_nummer)
    record = result.single()
    return record['chunks_created'] if record else 0


def main():
    logger.info("=" * 80)
    logger.info("SGB Content Repair and Chunking")
    logger.info("=" * 80)
    
    with driver.session() as session:
        stats = session.execute_read(get_sgb_stats)
    
    logger.info("\n📊 Current SGB Status:")
    for stat in stats:
        sgb = stat['sgb']
        norms = stat['total_norms']
        chunks = stat['total_chunks']
        empty = stat['norms_without_content']
        chunk_rate = (chunks / norms * 100) if norms > 0 else 0
        
        status = "✅" if empty == 0 and chunk_rate > 90 else "⚠️" if empty < 10 else "❌"
        logger.info(f"  {status} SGB {sgb:>3}: {norms:>4} norms, {chunks:>5} chunks ({chunk_rate:>5.1f}%), {empty:>3} empty")
    
    logger.info("\n" + "=" * 80)
    logger.info("Starting Repair Process")
    logger.info("=" * 80)
    
    for stat in stats:
        sgb = stat['sgb']
        empty_count = stat['norms_without_content']
        chunk_rate = (stat['total_chunks'] / stat['total_norms'] * 100) if stat['total_norms'] > 0 else 0
        
        if empty_count > 0 or chunk_rate < 90:
            logger.info(f"\n🔧 Processing SGB {sgb}...")
            
            # Link orphaned norms first
            logger.info(f"  🔗 Linking orphaned norms...")
            with driver.session() as session:
                linked_count = session.execute_write(link_orphaned_norms_for_sgb, sgb)
            logger.info(f"  ✅ Linked {linked_count} orphaned norms")
            
            # Re-import from XML if many norms are still empty after linking
            if empty_count > 5:
                logger.info(f"  📥 Re-importing from XML ({empty_count} empty norms)")
                success = reimport_sgb_from_xml(sgb)
                if not success:
                    logger.warning(f"  ⚠️  Could not reimport SGB {sgb}")
            
            # Generate chunks
            logger.info(f"  🔨 Generating chunks...")
            with driver.session() as session:
                chunks_created = session.execute_write(generate_chunks_for_sgb, sgb)
            
            logger.info(f"  ✅ Created {chunks_created} chunks for SGB {sgb}")
    
    # Final stats
    logger.info("\n" + "=" * 80)
    logger.info("Final SGB Status")
    logger.info("=" * 80)
    
    with driver.session() as session:
        final_stats = session.execute_read(get_sgb_stats)
    
    for stat in final_stats:
        sgb = stat['sgb']
        norms = stat['total_norms']
        chunks = stat['total_chunks']
        empty = stat['norms_without_content']
        chunk_rate = (chunks / norms * 100) if norms > 0 else 0
        
        status = "✅" if empty == 0 and chunk_rate > 90 else "⚠️" if empty < 10 else "❌"
        logger.info(f"  {status} SGB {sgb:>3}: {norms:>4} norms, {chunks:>5} chunks ({chunk_rate:>5.1f}%), {empty:>3} empty")
    
    driver.close()
    logger.info("\n✅ Repair process complete")


if __name__ == "__main__":
    main()
