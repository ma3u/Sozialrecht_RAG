#!/usr/bin/env python3
"""Quick import script for SGB II"""

import sys
sys.path.insert(0, 'src')

from pathlib import Path
from xml_legal_parser import LegalXMLParser
from graphrag_legal_extractor import LegalKnowledgeGraphBuilder
from neo4j import GraphDatabase
import os
from dotenv import load_dotenv

load_dotenv()

# Check if XML file exists
xml_file = Path("xml_cache/sgb_2/BJNR295500003.xml")

if not xml_file.exists():
    print(f"❌ XML file not found: {xml_file}")
    print("\nPlease download SGB II XML first:")
    print("  mkdir -p xml_cache/sgb_2")
    print("  cd xml_cache/sgb_2")
    print("  wget https://www.gesetze-im-internet.de/sgb_2/xml.zip")
    print("  unzip xml.zip")
    sys.exit(1)

print(f"✅ Found XML: {xml_file}")

# Parse XML
print("\n📖 Parsing XML...")
parser = LegalXMLParser()
document = parser.parse_dokument(xml_file)

print(f"✅ Parsed: {document.jurabk}")
print(f"   - {len(document.norms)} norms")
print(f"   - {len(document.structures)} structures")

# Connect to Neo4j
uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
username = os.getenv("NEO4J_USERNAME", "neo4j")
password = os.getenv("NEO4J_PASSWORD")

if not password:
    print("❌ NEO4J_PASSWORD not set in .env")
    sys.exit(1)

print(f"\n🔌 Connecting to Neo4j: {uri}")
driver = GraphDatabase.driver(uri, auth=(username, password))

# Test connection
try:
    driver.verify_connectivity()
    print("✅ Connected!")
except Exception as e:
    print(f"❌ Connection failed: {e}")
    sys.exit(1)

# Build knowledge graph
print("\n📊 Building knowledge graph...")
kg_builder = LegalKnowledgeGraphBuilder(driver)
kg_builder.build_from_xml(document)

print("\n✅ Import complete!")
print("\nNow try your Cypher query again in Neo4j Browser!")

driver.close()
