#!/usr/bin/env python3
"""
Enhanced XML to Neo4j Importer with Amendment Tracking
Integrates AmendmentParser for comprehensive amendment coverage
"""

import logging
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime
from lxml import etree
import hashlib

# Import existing parser and new amendment parser
from src.xml_legal_parser import LegalXMLParser, LegalDocument, LegalNorm
from src.amendment_parser import AmendmentParser, ParsedAmendment, ParsedBGBl, ParsedFussnote

try:
    from neo4j import GraphDatabase
    NEO4J_AVAILABLE = True
except ImportError:
    NEO4J_AVAILABLE = False
    logging.warning("neo4j package not available - will not connect to database")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EnhancedXMLtoNeo4jImporter:
    """Enhanced importer with comprehensive amendment tracking"""
    
    def __init__(self, neo4j_uri: str, neo4j_user: str, neo4j_password: str):
        """Initialize importer with Neo4j connection"""
        self.xml_parser = LegalXMLParser()
        self.amendment_parser = AmendmentParser()
        
        if NEO4J_AVAILABLE:
            self.driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))
            logger.info("✅ Connected to Neo4j")
        else:
            self.driver = None
            logger.warning("⚠️ Neo4j not available - running in dry-run mode")
    
    def close(self):
        """Close Neo4j connection"""
        if self.driver:
            self.driver.close()
    
    def import_xml_with_amendments(self, xml_path: Path) -> Dict:
        """
        Import XML file with comprehensive amendment tracking
        
        Args:
            xml_path: Path to XML file
            
        Returns:
            Dictionary with import statistics
        """
        logger.info(f"📄 Importing: {xml_path.name}")
        
        # Parse XML
        document = self.xml_parser.parse_dokument(xml_path)
        
        # Extract enhanced amendment data
        stats = {
            'document': document.jurabk,
            'norms': len(document.norms),
            'amendments': 0,
            'bgbl_refs': 0,
            'fussnoten': 0
        }
        
        with self.driver.session() as session:
            # Import document
            self._create_document_node(session, document)
            
            # Import norms with enhanced amendments
            for norm in document.norms:
                self._create_norm_node(session, document, norm)
                
                # Process amendments with enhanced parser
                amendment_count = self._process_norm_amendments(session, norm)
                stats['amendments'] += amendment_count
                
                # Process fussnoten
                fussnote_count = self._process_norm_fussnoten(session, norm, xml_path)
                stats['fussnoten'] += fussnote_count
            
            # Extract and create BGBl references
            bgbl_count = self._process_document_bgbl(session, document)
            stats['bgbl_refs'] = bgbl_count
        
        logger.info(f"✅ Imported {stats['document']}: {stats['norms']} norms, "
                   f"{stats['amendments']} amendments, {stats['bgbl_refs']} BGBl refs")
        
        return stats
    
    def _create_document_node(self, session, document: LegalDocument):
        """Create or update LegalDocument node"""
        query = """
        MERGE (doc:LegalDocument {doknr: $doknr})
        SET doc.jurabk = $jurabk,
            doc.sgb_nummer = $sgb_nummer,
            doc.lange_titel = $lange_titel,
            doc.ausfertigung_datum = date($ausfertigung_datum),
            doc.fundstelle = $fundstelle,
            doc.builddate = datetime($builddate),
            doc.xml_source_url = $xml_source_url,
            doc.trust_score = $trust_score,
            doc.source_type = $source_type
        RETURN doc.doknr as doknr
        """
        
        result = session.run(query, 
            doknr=document.doknr,
            jurabk=document.jurabk,
            sgb_nummer=document.sgb_nummer,
            lange_titel=document.lange_titel,
            ausfertigung_datum=document.ausfertigung_datum.isoformat() if document.ausfertigung_datum else None,
            fundstelle=document.fundstelle,
            builddate=document.builddate.isoformat(),
            xml_source_url=document.xml_source_url,
            trust_score=document.trust_score,
            source_type=document.source_type
        )
        
        return result.single()
    
    def _create_norm_node(self, session, document: LegalDocument, norm: LegalNorm):
        """Create or update LegalNorm node"""
        query = """
        MATCH (doc:LegalDocument {doknr: $doc_doknr})
        MERGE (norm:Norm {norm_doknr: $norm_doknr})
        SET norm.enbez = $enbez,
            norm.paragraph_nummer = $paragraph_nummer,
            norm.titel = $titel,
            norm.content_text = $content_text,
            norm.has_footnotes = $has_footnotes,
            norm.order_index = $order_index
        MERGE (doc)-[:CONTAINS_NORM]->(norm)
        RETURN norm.norm_doknr as norm_doknr
        """
        
        result = session.run(query,
            doc_doknr=document.doknr,
            norm_doknr=norm.norm_doknr,
            enbez=norm.enbez,
            paragraph_nummer=norm.paragraph_nummer,
            titel=norm.titel,
            content_text=norm.content_text[:5000],  # Limit length
            has_footnotes=norm.has_footnotes,
            order_index=norm.order_index
        )
        
        return result.single()
    
    def _process_norm_amendments(self, session, norm: LegalNorm) -> int:
        """
        Process amendments for a norm using enhanced parser
        
        Returns:
            Number of amendments created
        """
        count = 0
        
        for old_amendment in norm.amendments:
            # Use enhanced parser
            parsed = self.amendment_parser.parse_standkommentar(old_amendment.standkommentar)
            
            if parsed:
                self._create_amendment_node(session, norm.norm_doknr, parsed)
                count += 1
        
        return count
    
    def _create_amendment_node(self, session, norm_doknr: str, amendment: ParsedAmendment):
        """Create Amendment node and link to norm"""
        # Generate unique ID
        amendment_id = hashlib.sha256(
            f"{norm_doknr}_{amendment.raw_text}".encode()
        ).hexdigest()[:16]
        
        query = """
        MATCH (norm:Norm {norm_doknr: $norm_doknr})
        MERGE (amendment:Amendment {id: $amendment_id})
        SET amendment.raw_text = $raw_text,
            amendment.amendment_type = $amendment_type,
            amendment.amendment_date = date($amendment_date),
            amendment.artikel = $artikel,
            amendment.gesetz_ref = $gesetz_ref,
            amendment.bgbl_issue = $bgbl_issue,
            amendment.bgbl_year = $bgbl_year,
            amendment.bgbl_full_ref = $bgbl_full_ref,
            amendment.created_at = datetime()
        MERGE (norm)-[:HAS_AMENDMENT]->(amendment)
        RETURN amendment.id as id
        """
        
        amendment_dict = amendment.to_dict()
        
        result = session.run(query,
            norm_doknr=norm_doknr,
            amendment_id=amendment_id,
            **amendment_dict
        )
        
        return result.single()
    
    def _process_norm_fussnoten(self, session, norm: LegalNorm, xml_path: Path) -> int:
        """
        Extract and process fussnoten (footnotes) for version tracking
        
        Returns:
            Number of fussnoten created
        """
        count = 0
        
        # Re-parse XML to get fussnoten
        with open(xml_path, 'rb') as f:
            xml_content = f.read()
        root = etree.fromstring(xml_content)
        
        # Find this norm's element
        for norm_elem in root.findall('.//norm'):
            if norm_elem.get('doknr') == norm.norm_doknr:
                textdaten = norm_elem.find('textdaten')
                if textdaten is not None:
                    fussnoten_elem = textdaten.find('fussnoten')
                    if fussnoten_elem is not None:
                        # Extract text from fussnoten
                        fussnote_text = self._extract_text_recursive(fussnoten_elem)
                        
                        # Parse with enhanced parser
                        parsed_fussnote = self.amendment_parser.parse_fussnote(fussnote_text)
                        
                        if parsed_fussnote:
                            self._create_fussnote_node(session, norm.norm_doknr, parsed_fussnote)
                            count += 1
                break
        
        return count
    
    def _create_fussnote_node(self, session, norm_doknr: str, fussnote: ParsedFussnote):
        """Create Fussnote node and link to norm"""
        fussnote_id = hashlib.sha256(
            f"{norm_doknr}_{fussnote.context[:100]}".encode()
        ).hexdigest()[:16]
        
        query = """
        MATCH (norm:Norm {norm_doknr: $norm_doknr})
        MERGE (fussnote:Fussnote {id: $fussnote_id})
        SET fussnote.valid_from = date($valid_from),
            fussnote.in_kraft = date($in_kraft),
            fussnote.context = $context,
            fussnote.created_at = datetime()
        MERGE (norm)-[:HAS_FUSSNOTE]->(fussnote)
        RETURN fussnote.id as id
        """
        
        fussnote_dict = fussnote.to_dict()
        
        result = session.run(query,
            norm_doknr=norm_doknr,
            fussnote_id=fussnote_id,
            **fussnote_dict
        )
        
        return result.single()
    
    def _process_document_bgbl(self, session, document: LegalDocument) -> int:
        """
        Extract BGBl references from document fundstelle
        
        Returns:
            Number of BGBl references created
        """
        if not document.fundstelle:
            return 0
        
        # Try to parse BGBl from fundstelle
        # Format: "BGBl I 1996, 1254"
        parts = document.fundstelle.split()
        if len(parts) >= 3 and parts[0] == 'BGBl':
            periodikum = f"{parts[0]} {parts[1]}"  # "BGBl I"
            zitstelle = " ".join(parts[2:])  # "1996, 1254"
            
            parsed_bgbl = self.amendment_parser.parse_bgbl_reference(periodikum, zitstelle)
            
            if parsed_bgbl:
                self._create_bgbl_node(session, document.doknr, parsed_bgbl)
                return 1
        
        return 0
    
    def _create_bgbl_node(self, session, doc_doknr: str, bgbl: ParsedBGBl):
        """Create BGBl node and link to document"""
        query = """
        MATCH (doc:LegalDocument {doknr: $doc_doknr})
        MERGE (bgbl:BGBl {id: $id})
        SET bgbl.periodikum = $periodikum,
            bgbl.year = $year,
            bgbl.page = $page,
            bgbl.full_reference = $full_reference,
            bgbl.created_at = datetime()
        MERGE (doc)-[:PUBLISHED_IN]->(bgbl)
        RETURN bgbl.id as id
        """
        
        bgbl_dict = bgbl.to_dict()
        
        result = session.run(query,
            doc_doknr=doc_doknr,
            **bgbl_dict
        )
        
        return result.single()
    
    def create_amendment_superseded_relationships(self, session):
        """
        Create SUPERSEDED_BY relationships between amendments
        Links amendments chronologically for the same norm
        """
        query = """
        MATCH (norm:Norm)-[:HAS_AMENDMENT]->(a1:Amendment)
        MATCH (norm)-[:HAS_AMENDMENT]->(a2:Amendment)
        WHERE a1.amendment_date < a2.amendment_date
          AND NOT (a1)-[:SUPERSEDED_BY]->(a2)
        WITH norm, a1, a2
        ORDER BY a1.amendment_date, a2.amendment_date
        WITH norm, a1, collect(a2)[0] as next_amendment
        WHERE next_amendment IS NOT NULL
        MERGE (a1)-[:SUPERSEDED_BY]->(next_amendment)
        RETURN count(*) as relationships_created
        """
        
        result = session.run(query)
        count = result.single()['relationships_created']
        logger.info(f"✅ Created {count} SUPERSEDED_BY relationships")
        return count
    
    def _extract_text_recursive(self, elem) -> str:
        """Recursively extract all text from XML element"""
        texts = []
        if elem.text:
            texts.append(elem.text)
        for child in elem:
            texts.append(self._extract_text_recursive(child))
            if child.tail:
                texts.append(child.tail)
        return " ".join(texts).strip()
    
    def create_indexes(self):
        """Create Neo4j indexes for amendment queries"""
        indexes = [
            "CREATE INDEX amendment_date IF NOT EXISTS FOR (a:Amendment) ON (a.amendment_date)",
            "CREATE INDEX amendment_gesetz IF NOT EXISTS FOR (a:Amendment) ON (a.gesetz_ref)",
            "CREATE INDEX amendment_artikel IF NOT EXISTS FOR (a:Amendment) ON (a.artikel)",
            "CREATE INDEX amendment_bgbl_year IF NOT EXISTS FOR (a:Amendment) ON (a.bgbl_year)",
            "CREATE INDEX bgbl_year IF NOT EXISTS FOR (b:BGBl) ON (b.year)",
            "CREATE INDEX bgbl_full_ref IF NOT EXISTS FOR (b:BGBl) ON (b.full_reference)",
            "CREATE INDEX fussnote_valid_from IF NOT EXISTS FOR (f:Fussnote) ON (f.valid_from)",
        ]
        
        with self.driver.session() as session:
            for index_query in indexes:
                session.run(index_query)
                logger.info(f"✅ Created index: {index_query.split('FOR')[1].split('ON')[0].strip()}")


def import_single_sgb(sgb_path: Path, neo4j_uri: str, neo4j_user: str, neo4j_password: str) -> Dict:
    """
    Import a single SGB XML file with amendments
    
    Args:
        sgb_path: Path to SGB XML file
        neo4j_uri: Neo4j connection URI
        neo4j_user: Neo4j username
        neo4j_password: Neo4j password
        
    Returns:
        Import statistics dictionary
    """
    importer = EnhancedXMLtoNeo4jImporter(neo4j_uri, neo4j_user, neo4j_password)
    
    try:
        # Create indexes first
        importer.create_indexes()
        
        # Import document
        stats = importer.import_xml_with_amendments(sgb_path)
        
        # Create superseded relationships
        with importer.driver.session() as session:
            stats['superseded_rels'] = importer.create_amendment_superseded_relationships(session)
        
        return stats
        
    finally:
        importer.close()


# Example usage and testing
if __name__ == '__main__':
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    # Configuration
    NEO4J_URI = os.getenv('NEO4J_URI', 'bolt://localhost:7687')
    NEO4J_USER = os.getenv('NEO4J_USER', 'neo4j')
    NEO4J_PASSWORD = os.getenv('NEO4J_PASSWORD', 'password')
    
    print("=== Enhanced XML to Neo4j Importer ===\n")
    
    # Find SGB VII XML for testing
    xml_cache_dir = Path('/Users/ma3u/projects/sozialgesetze/Sozialrecht_RAG/xml_cache')
    sgb7_xml = xml_cache_dir / 'sgb_7' / 'BJNR125410996.xml'
    
    if sgb7_xml.exists():
        print(f"📄 Testing with: {sgb7_xml.name}\n")
        
        stats = import_single_sgb(sgb7_xml, NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)
        
        print("\n" + "="*60)
        print("Import Statistics:")
        print("="*60)
        for key, value in stats.items():
            print(f"  {key}: {value}")
        print("\n✅ Import test complete!")
    else:
        print(f"❌ Test file not found: {sgb7_xml}")
        print("   Please ensure SGB VII XML is available in xml_cache/sgb_7/")
