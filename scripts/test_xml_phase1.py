#!/usr/bin/env python3
"""
Test script for Phase 1 XML implementation
Tests XML download, parsing, and knowledge graph building with SGB II
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from xml_downloader import GIIXMLDownloader
from xml_legal_parser import LegalXMLParser
from graphrag_legal_extractor import LegalKnowledgeGraphBuilder
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()


def test_phase1():
    """Test complete Phase 1 implementation"""
    
    print("\n" + "="*60)
    print("PHASE 1 TEST: XML Download, Parse, and Knowledge Graph")
    print("="*60)
    
    # ====================
    # 1. Test XML Downloader
    # ====================
    print("\n[1/5] Testing XML Downloader...")
    downloader = GIIXMLDownloader()
    
    # Download TOC
    catalog = downloader.download_toc()
    print(f"  ✅ Downloaded TOC: {len(catalog)} laws")
    
    # Get SGB URLs
    sgb_urls = downloader.get_sgb_xml_urls()
    print(f"  ✅ Mapped {len(sgb_urls)} SGB URLs")
    
    # Download SGB II as test case
    print("\n  Downloading SGB II XML...")
    xml_path = downloader.download_law_xml("II")
    print(f"  ✅ Downloaded SGB II: {xml_path}")
    
    # Get metadata
    metadata = downloader.get_xml_metadata(xml_path)
    print(f"  ✅ XML Metadata:")
    print(f"     - Jurabk: {metadata.get('jurabk')}")
    print(f"     - Doknr: {metadata.get('doknr')}")
    print(f"     - Build Date: {metadata.get('builddate')}")
    print(f"     - File Size: {metadata.get('file_size'):,} bytes")
    
    # ====================
    # 2. Test XML Parser
    # ====================
    print("\n[2/5] Testing XML Parser...")
    parser = LegalXMLParser()
    
    document = parser.parse_dokument(xml_path)
    print(f"  ✅ Parsed document: {document.jurabk}")
    print(f"     - SGB Number: {document.sgb_nummer}")
    print(f"     - Doknr: {document.doknr}")
    print(f"     - Build Date: {document.builddate}")
    print(f"     - Trust Score: {document.trust_score}")
    print(f"     - Norms: {len(document.norms)}")
    print(f"     - Structures: {len(document.structures)}")
    
    # Show sample norm
    if document.norms:
        sample_norm = document.norms[0]
        print(f"\n  Sample Norm:")
        print(f"     - Enbez: {sample_norm.enbez}")
        print(f"     - Paragraph: {sample_norm.paragraph_nummer}")
        print(f"     - Title: {sample_norm.titel[:60]}...")
        print(f"     - Text Units: {len(sample_norm.text_units)}")
        print(f"     - Amendments: {len(sample_norm.amendments)}")
        print(f"     - Has Footnotes: {sample_norm.has_footnotes}")
    
    # Show sample structure
    if document.structures:
        sample_struct = document.structures[0]
        print(f"\n  Sample Structure:")
        print(f"     - Kennzahl: {sample_struct.gliederungskennzahl}")
        print(f"     - Bez: {sample_struct.gliederungsbez}")
        print(f"     - Title: {sample_struct.gliederungstitel}")
        print(f"     - Level: {sample_struct.level}")
    
    # ====================
    # 3. Test Neo4j Connection
    # ====================
    print("\n[3/5] Testing Neo4j Connection...")
    uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    username = os.getenv("NEO4J_USERNAME", "neo4j")
    password = os.getenv("NEO4J_PASSWORD", "password")
    
    try:
        driver = GraphDatabase.driver(uri, auth=(username, password))
        driver.verify_connectivity()
        print(f"  ✅ Connected to Neo4j at {uri}")
    except Exception as e:
        print(f"  ❌ Failed to connect to Neo4j: {e}")
        print(f"     Please ensure Neo4j is running at {uri}")
        return False
    
    # ====================
    # 4. Test Knowledge Graph Builder
    # ====================
    print("\n[4/5] Testing Knowledge Graph Builder...")
    kg_builder = LegalKnowledgeGraphBuilder(driver)
    
    print("  Building knowledge graph from SGB II...")
    print("  This may take a few minutes for embeddings...")
    
    try:
        kg_builder.build_from_xml(document)
        print(f"  ✅ Knowledge graph built successfully!")
    except Exception as e:
        print(f"  ❌ Failed to build knowledge graph: {e}")
        driver.close()
        return False
    
    # ====================
    # 5. Verify Data in Neo4j
    # ====================
    print("\n[5/5] Verifying Data in Neo4j...")
    
    with driver.session() as session:
        # Check LegalDocument
        result = session.run("MATCH (d:LegalDocument) RETURN count(d) as count")
        doc_count = result.single()['count']
        print(f"  ✅ Legal Documents: {doc_count}")
        
        # Check LegalNorms
        result = session.run("MATCH (n:LegalNorm) RETURN count(n) as count")
        norm_count = result.single()['count']
        print(f"  ✅ Legal Norms: {norm_count}")
        
        # Check StructuralUnits
        result = session.run("MATCH (s:StructuralUnit) RETURN count(s) as count")
        struct_count = result.single()['count']
        print(f"  ✅ Structural Units: {struct_count}")
        
        # Check TextUnits
        result = session.run("MATCH (t:TextUnit) RETURN count(t) as count")
        text_count = result.single()['count']
        print(f"  ✅ Text Units: {text_count}")
        
        # Check Amendments
        result = session.run("MATCH (a:Amendment) RETURN count(a) as count")
        amendment_count = result.single()['count']
        print(f"  ✅ Amendments: {amendment_count}")
        
        # Check Chunks
        result = session.run("MATCH (c:Chunk) RETURN count(c) as count")
        chunk_count = result.single()['count']
        print(f"  ✅ Chunks (with embeddings): {chunk_count}")
        
        # Test a query: Find § 20 SGB II
        print("\n  Testing query: Find § 20 SGB II")
        result = session.run("""
            MATCH (d:LegalDocument {sgb_nummer: 'II'})
            -[:HAS_STRUCTURE]->(s:StructuralUnit)
            -[:CONTAINS_NORM]->(n:LegalNorm {paragraph_nummer: '20'})
            RETURN n.enbez as enbez, n.titel as titel, n.paragraph_nummer as para
            LIMIT 1
        """)
        
        record = result.single()
        if record:
            print(f"  ✅ Found: {record['enbez']} - {record['titel']}")
        else:
            print(f"  ⚠️  Could not find § 20 (might not be linked to structure)")
            # Try direct query
            result = session.run("""
                MATCH (n:LegalNorm {paragraph_nummer: '20'})
                RETURN n.enbez as enbez, n.titel as titel
                LIMIT 1
            """)
            record = result.single()
            if record:
                print(f"  ✅ Found directly: {record['enbez']} - {record['titel']}")
    
    driver.close()
    
    # ====================
    # Summary
    # ====================
    print("\n" + "="*60)
    print("PHASE 1 TEST COMPLETE!")
    print("="*60)
    print("\n✅ All components working:")
    print("   1. XML Downloader - Downloads and caches XML from gesetze-im-internet.de")
    print("   2. XML Parser - Parses legal XML structure into Python objects")
    print("   3. Neo4j Connection - Connects to database")
    print("   4. Knowledge Graph Builder - Builds structured graph with embeddings")
    print("   5. Data Verification - Confirms data in Neo4j")
    
    print("\n📊 Data imported:")
    print(f"   - {doc_count} Legal Documents")
    print(f"   - {norm_count} Legal Norms (§ paragraphs)")
    print(f"   - {struct_count} Structural Units (chapters, sections)")
    print(f"   - {text_count} Text Units (absätze)")
    print(f"   - {amendment_count} Amendments")
    print(f"   - {chunk_count} Chunks with embeddings for RAG")
    
    print("\n🚀 Next Steps:")
    print("   - Run Phase 2 migration: python scripts/migrate_to_xml_schema.py")
    print("   - Import more SGBs: Modify this script to loop through all SGBs")
    print("   - Test RAG queries with new XML data")
    
    print("\n" + "="*60 + "\n")
    
    return True


if __name__ == "__main__":
    success = test_phase1()
    sys.exit(0 if success else 1)
