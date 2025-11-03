#!/usr/bin/env python3
"""
Complete Re-import of XML and PDF Data with neo4j-graphrag-python
Creates all relationships and chunks properly to visualize the graph
"""

import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from neo4j import GraphDatabase
from xml_legal_parser import LegalXMLParser
from graphrag_legal_extractor import LegalKnowledgeGraphBuilder
from dotenv import load_dotenv
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

load_dotenv()


class GraphRAGReimporter:
    """Re-import all data with proper GraphRAG structure"""
    
    def __init__(self):
        self.uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        self.username = os.getenv("NEO4J_USERNAME", "neo4j")
        self.password = os.getenv("NEO4J_PASSWORD")
        
        if not self.password:
            raise ValueError("❌ NEO4J_PASSWORD not set in .env")
        
        self.driver = GraphDatabase.driver(self.uri, auth=(self.username, self.password))
        logger.info(f"✅ Connected to Neo4j: {self.uri}")
    
    def close(self):
        self.driver.close()
    
    def clean_duplicates(self):
        """Remove duplicate LegalDocuments"""
        logger.info("\n🧹 Cleaning duplicate LegalDocuments...")
        
        with self.driver.session() as session:
            # Find duplicates
            result = session.run("""
                MATCH (doc:LegalDocument)
                WITH doc.sgb_nummer as sgb, collect(doc) as docs
                WHERE size(docs) > 1
                RETURN sgb, docs
            """)
            
            for record in result:
                sgb = record['sgb']
                docs = record['docs']
                logger.info(f"  Found {len(docs)} copies of SGB {sgb}")
                
                # Keep the most recent one, delete others
                docs_sorted = sorted(docs, key=lambda d: d.get('builddate', ''), reverse=True)
                to_delete = docs_sorted[1:]
                
                for doc in to_delete:
                    session.run("""
                        MATCH (doc:LegalDocument)
                        WHERE elementId(doc) = $id
                        DETACH DELETE doc
                    """, id=doc.element_id)
                    logger.info(f"  ✅ Deleted duplicate: {doc.get('jurabk')}")
    
    def reimport_xml_with_chunks(self, sgb_name="II"):
        """Re-import XML with proper chunk generation"""
        logger.info(f"\n📥 Re-importing SGB {sgb_name} XML with chunks...")
        
        # Find XML file
        xml_dir = Path(f"xml_cache/sgb_{sgb_name.lower()}")
        if not xml_dir.exists():
            logger.error(f"❌ XML directory not found: {xml_dir}")
            return False
        
        xml_files = list(xml_dir.glob("*.xml"))
        if not xml_files:
            logger.error(f"❌ No XML files found in {xml_dir}")
            return False
        
        xml_file = xml_files[0]
        logger.info(f"  Found XML: {xml_file}")
        
        # Parse XML
        parser = LegalXMLParser()
        document = parser.parse_dokument(xml_file)
        logger.info(f"  ✅ Parsed: {document.jurabk} ({len(document.norms)} norms)")
        
        # Delete existing data for this SGB
        with self.driver.session() as session:
            result = session.run("""
                MATCH (doc:LegalDocument {sgb_nummer: $sgb})
                OPTIONAL MATCH (doc)-[:HAS_STRUCTURE]->(struct:StructuralUnit)
                                    -[:CONTAINS_NORM]->(norm:LegalNorm)
                OPTIONAL MATCH (norm)-[:HAS_CONTENT]->(text:TextUnit)
                OPTIONAL MATCH (norm)-[:HAS_CHUNK]->(chunk:Chunk)
                DETACH DELETE doc, struct, norm, text, chunk
                RETURN count(*) as deleted
            """, sgb=sgb_name)
            deleted = result.single()['deleted']
            logger.info(f"  🗑️  Deleted {deleted} existing nodes for SGB {sgb_name}")
        
        # Build knowledge graph with chunks
        logger.info("  🔨 Building knowledge graph with embeddings...")
        kg_builder = LegalKnowledgeGraphBuilder(self.driver)
        kg_builder.build_from_xml(document)
        
        logger.info(f"  ✅ SGB {sgb_name} imported successfully!")
        return True
    
    def reimport_all_sgbs(self):
        """Re-import all available SGB XML files"""
        logger.info("\n🔄 Re-importing all SGB XMLs...")
        
        xml_cache = Path("xml_cache")
        if not xml_cache.exists():
            logger.warning("❌ xml_cache directory not found!")
            return
        
        sgb_dirs = [d for d in xml_cache.iterdir() if d.is_dir() and d.name.startswith('sgb_')]
        logger.info(f"  Found {len(sgb_dirs)} SGB directories")
        
        success_count = 0
        for sgb_dir in sorted(sgb_dirs):
            sgb_name = sgb_dir.name.replace('sgb_', '').upper()
            try:
                if self.reimport_xml_with_chunks(sgb_name):
                    success_count += 1
            except Exception as e:
                logger.error(f"  ❌ Failed to import SGB {sgb_name}: {e}")
        
        logger.info(f"\n✅ Successfully re-imported {success_count}/{len(sgb_dirs)} SGBs")
    
    def verify_pdf_chunks(self):
        """Verify that PDF documents have chunks"""
        logger.info("\n🔍 Verifying PDF document chunks...")
        
        with self.driver.session() as session:
            result = session.run("""
                MATCH (d:Document)
                OPTIONAL MATCH (d)-[:HAS_CHUNK]->(c:Chunk)
                WITH d, count(c) as chunk_count
                WHERE chunk_count = 0
                RETURN d.filename as filename, chunk_count
                LIMIT 5
            """)
            
            missing = list(result)
            if missing:
                logger.warning(f"  ⚠️  {len(missing)} PDF documents missing chunks:")
                for r in missing:
                    logger.warning(f"    - {r['filename']}")
            else:
                logger.info("  ✅ All PDF documents have chunks")
    
    def create_summary_report(self):
        """Generate summary of database state"""
        logger.info("\n" + "="*70)
        logger.info("📊 DATABASE SUMMARY AFTER RE-IMPORT")
        logger.info("="*70)
        
        with self.driver.session() as session:
            # Node counts
            result = session.run("""
                MATCH (n)
                RETURN labels(n)[0] as type, count(*) as count
                ORDER BY count DESC
            """)
            
            logger.info("\n📦 Node Types:")
            for r in result:
                logger.info(f"  {r['type']:<20} {r['count']:>10,}")
            
            # Relationship counts
            result = session.run("""
                MATCH ()-[r]->()
                RETURN type(r) as rel_type, count(*) as count
                ORDER BY count DESC
            """)
            
            logger.info("\n🔗 Relationship Types:")
            for r in result:
                logger.info(f"  {r['rel_type']:<30} {r['count']:>10,}")
            
            # LegalNorm chunk coverage
            result = session.run("""
                MATCH (norm:LegalNorm)
                OPTIONAL MATCH (norm)-[:HAS_CHUNK]->(chunk:Chunk)
                WITH count(DISTINCT norm) as total_norms,
                     count(DISTINCT chunk) as total_chunks,
                     sum(CASE WHEN chunk IS NOT NULL THEN 1 ELSE 0 END) as norms_with_chunks
                RETURN total_norms, total_chunks, norms_with_chunks
            """)
            
            stats = result.single()
            coverage = (stats['norms_with_chunks'] / stats['total_norms'] * 100) if stats['total_norms'] > 0 else 0
            
            logger.info(f"\n📈 LegalNorm Chunk Coverage:")
            logger.info(f"  Total norms: {stats['total_norms']:,}")
            logger.info(f"  Norms with chunks: {stats['norms_with_chunks']:,}")
            logger.info(f"  Coverage: {coverage:.1f}%")
            
            # Sample query for visualization
            logger.info("\n✅ Ready for Neo4j Browser visualization!")
            logger.info("\n📋 Try this query in Neo4j Browser:")
            logger.info("""
MATCH path = (doc:LegalDocument {sgb_nummer: "II"})
             -[:CONTAINS_NORM]->(norm:LegalNorm)
             -[:HAS_CHUNK]->(chunk:Chunk)
RETURN path
LIMIT 50
            """)


def main():
    print("\n" + "="*70)
    print("🔄 COMPLETE RE-IMPORT WITH NEO4J-GRAPHRAG-PYTHON")
    print("="*70)
    print("\nThis will:")
    print("  1. Clean duplicate LegalDocuments")
    print("  2. Re-import all SGB XMLs with proper chunks")
    print("  3. Verify PDF document chunks")
    print("  4. Generate summary report")
    print("\n" + "="*70)
    
    answer = input("\n⚠️  Proceed with re-import? This will delete existing XML data. (yes/no): ")
    if answer.lower() not in ['yes', 'y']:
        print("❌ Re-import cancelled")
        return 1
    
    reimporter = GraphRAGReimporter()
    
    try:
        # Step 1: Clean duplicates
        reimporter.clean_duplicates()
        
        # Step 2: Re-import all SGBs
        reimporter.reimport_all_sgbs()
        
        # Step 3: Verify PDFs
        reimporter.verify_pdf_chunks()
        
        # Step 4: Summary
        reimporter.create_summary_report()
        
        print("\n" + "="*70)
        print("✅ RE-IMPORT COMPLETE!")
        print("="*70)
        print("\nNext steps:")
        print("  1. Open Neo4j Browser")
        print("  2. Run the sample query shown above")
        print("  3. Enjoy the beautiful graph visualization!")
        
    except Exception as e:
        logger.error(f"\n❌ Re-import failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        reimporter.close()
    
    return 0


if __name__ == "__main__":
    exit(main())
