"""
Legal Knowledge Graph Builder using neo4j-graphrag-python
Builds structured legal knowledge graph from parsed XML documents
"""

import logging
from typing import List, Dict, Optional
from neo4j import GraphDatabase
from sentence_transformers import SentenceTransformer
import numpy as np
from xml_legal_parser import LegalDocument, LegalNorm, StructuralUnit, TextUnit, ListItem, Amendment
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LegalKnowledgeGraphBuilder:
    """Use neo4j-graphrag-python to build legal KG"""
    
    def __init__(self, neo4j_driver, embedding_model: Optional[SentenceTransformer] = None):
        """Initialize Knowledge Graph Builder
        
        Args:
            neo4j_driver: Neo4j driver instance
            embedding_model: SentenceTransformer model for embeddings (optional)
        """
        self.driver = neo4j_driver
        
        # Use provided embedding model or load default
        if embedding_model:
            self.embedding_model = embedding_model
        else:
            logger.info("Loading German embedding model...")
            self.embedding_model = SentenceTransformer('paraphrase-multilingual-mpnet-base-v2')
        
        logger.info("✅ Legal Knowledge Graph Builder initialized")
    
    def build_from_xml(self, legal_document: LegalDocument):
        """Convert parsed XML to Neo4j graph
        
        Args:
            legal_document: Parsed LegalDocument object
        """
        with self.driver.session() as session:
            with session.begin_transaction() as tx:
                # 1. Create Legal Document node
                doc_node_id = self._create_legal_document(tx, legal_document)
                
                # 2. Create Structural Units
                struct_node_ids = self._create_structural_units(tx, legal_document, doc_node_id)
                
                # 3. Create Legal Norms with relationships
                self._create_legal_norms(tx, legal_document, doc_node_id, struct_node_ids)
                
                tx.commit()
        
        logger.info(f"✅ Built knowledge graph for {legal_document.jurabk}")
    
    def _create_legal_document(self, tx, doc: LegalDocument) -> str:
        """Create LegalDocument node"""
        query = """
        MERGE (d:LegalDocument {id: $id})
        SET d.doknr = $doknr,
            d.builddate = datetime($builddate),
            d.jurabk = $jurabk,
            d.lange_titel = $lange_titel,
            d.sgb_nummer = $sgb_nummer,
            d.ausfertigung_datum = date($ausfertigung_datum),
            d.fundstelle = $fundstelle,
            d.trust_score = $trust_score,
            d.source_type = $source_type,
            d.xml_source_url = $xml_source_url,
            d.last_updated = datetime($last_updated)
        RETURN d.id as id
        """
        
        result = tx.run(query,
            id=doc.id,
            doknr=doc.doknr,
            builddate=doc.builddate.isoformat(),
            jurabk=doc.jurabk,
            lange_titel=doc.lange_titel,
            sgb_nummer=doc.sgb_nummer,
            ausfertigung_datum=doc.ausfertigung_datum.isoformat() if doc.ausfertigung_datum else None,
            fundstelle=doc.fundstelle,
            trust_score=doc.trust_score,
            source_type=doc.source_type,
            xml_source_url=doc.xml_source_url,
            last_updated=datetime.now().isoformat()
        )
        
        return result.single()['id']
    
    def _create_structural_units(self, tx, doc: LegalDocument, doc_node_id: str) -> Dict[str, str]:
        """Create StructuralUnit nodes and link to document"""
        struct_node_ids = {}
        
        for struct in doc.structures:
            query = """
            MERGE (s:StructuralUnit {id: $id})
            SET s.gliederungskennzahl = $kennzahl,
                s.gliederungsbez = $bez,
                s.gliederungstitel = $titel,
                s.level = $level,
                s.order_index = $order_index
            WITH s
            MATCH (d:LegalDocument {id: $doc_id})
            MERGE (d)-[:HAS_STRUCTURE]->(s)
            RETURN s.id as id
            """
            
            result = tx.run(query,
                id=struct.id,
                kennzahl=struct.gliederungskennzahl,
                bez=struct.gliederungsbez,
                titel=struct.gliederungstitel,
                level=struct.level,
                order_index=struct.order_index,
                doc_id=doc_node_id
            )
            
            struct_node_ids[struct.gliederungskennzahl] = struct.id
        
        logger.info(f"Created {len(struct_node_ids)} structural units")
        return struct_node_ids
    
    def _create_legal_norms(self, tx, doc: LegalDocument, doc_node_id: str, struct_node_ids: Dict[str, str]):
        """Create LegalNorm nodes with all relationships"""
        for norm in doc.norms:
            # Create norm node
            norm_query = """
            MERGE (n:LegalNorm {id: $id})
            SET n.norm_doknr = $norm_doknr,
                n.enbez = $enbez,
                n.paragraph_nummer = $paragraph_nummer,
                n.titel = $titel,
                n.content_text = $content_text,
                n.has_footnotes = $has_footnotes,
                n.order_index = $order_index
            RETURN n.id as id
            """
            
            tx.run(norm_query,
                id=norm.id,
                norm_doknr=norm.norm_doknr,
                enbez=norm.enbez,
                paragraph_nummer=norm.paragraph_nummer,
                titel=norm.titel,
                content_text=norm.content_text,
                has_footnotes=norm.has_footnotes,
                order_index=norm.order_index
            )
            
            # Link to structural unit if applicable
            if norm.gliederung and norm.gliederung['kennzahl']:
                struct_id = struct_node_ids.get(norm.gliederung['kennzahl'])
                if struct_id:
                    link_query = """
                    MATCH (s:StructuralUnit {id: $struct_id})
                    MATCH (n:LegalNorm {id: $norm_id})
                    MERGE (s)-[:CONTAINS_NORM]->(n)
                    """
                    tx.run(link_query, struct_id=struct_id, norm_id=norm.id)
            
            # Create text units
            self._create_text_units(tx, norm)
            
            # Create amendments
            self._create_amendments(tx, norm)
            
            # Generate chunks with embeddings
            self._create_chunks_with_embeddings(tx, norm, doc.sgb_nummer)
        
        logger.info(f"Created {len(doc.norms)} legal norms with content")
    
    def _create_text_units(self, tx, norm: LegalNorm):
        """Create TextUnit nodes and link to norm"""
        for text_unit in norm.text_units:
            query = """
            MERGE (t:TextUnit {id: $id})
            SET t.type = $type,
                t.text = $text,
                t.absatz_nummer = $absatz_nummer,
                t.order_index = $order_index
            WITH t
            MATCH (n:LegalNorm {id: $norm_id})
            MERGE (n)-[:HAS_CONTENT]->(t)
            RETURN t.id as id
            """
            
            tx.run(query,
                id=text_unit.id,
                type=text_unit.type,
                text=text_unit.text,
                absatz_nummer=text_unit.absatz_nummer,
                order_index=text_unit.order_index,
                norm_id=norm.id
            )
            
            # Create list items if applicable
            if text_unit.list_items:
                self._create_list_items(tx, text_unit)
    
    def _create_list_items(self, tx, text_unit: TextUnit):
        """Create ListItem nodes and link to text unit"""
        for list_item in text_unit.list_items:
            query = """
            MERGE (l:ListItem {id: $id})
            SET l.list_type = $list_type,
                l.term = $term,
                l.definition = $definition,
                l.order_index = $order_index
            WITH l
            MATCH (t:TextUnit {id: $text_unit_id})
            MERGE (t)-[:HAS_LIST_ITEM]->(l)
            """
            
            tx.run(query,
                id=list_item.id,
                list_type=list_item.list_type,
                term=list_item.term,
                definition=list_item.definition,
                order_index=list_item.order_index,
                text_unit_id=text_unit.id
            )
    
    def _create_amendments(self, tx, norm: LegalNorm):
        """Create Amendment nodes and link to norm"""
        for amendment in norm.amendments:
            query = """
            MERGE (a:Amendment {id: $id})
            SET a.standtyp = $standtyp,
                a.standkommentar = $standkommentar,
                a.amendment_date = date($amendment_date),
                a.bgbl_reference = $bgbl_reference
            WITH a
            MATCH (n:LegalNorm {id: $norm_id})
            MERGE (n)-[:HAS_AMENDMENT]->(a)
            """
            
            tx.run(query,
                id=amendment.id,
                standtyp=amendment.standtyp,
                standkommentar=amendment.standkommentar,
                amendment_date=amendment.amendment_date.isoformat() if amendment.amendment_date else None,
                bgbl_reference=amendment.bgbl_reference,
                norm_id=norm.id
            )
    
    def _create_chunks_with_embeddings(self, tx, norm: LegalNorm, sgb_nummer: Optional[str]):
        """Create Chunk nodes with embeddings for RAG"""
        # Combine text units into chunks (respect 800 char limit from existing system)
        chunks = []
        current_chunk = ""
        chunk_index = 0
        
        for text_unit in norm.text_units:
            if len(current_chunk) + len(text_unit.text) > 800:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                    current_chunk = text_unit.text
                else:
                    chunks.append(text_unit.text[:800])
            else:
                current_chunk += " " + text_unit.text
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        # If no chunks, use full content
        if not chunks and norm.content_text:
            chunks = [norm.content_text[:800]]
        
        # Generate embeddings and create chunk nodes
        if chunks:
            embeddings = self.embedding_model.encode(chunks, show_progress_bar=False)
            
            for idx, (chunk_text, embedding) in enumerate(zip(chunks, embeddings)):
                chunk_query = """
                CREATE (c:Chunk)
                SET c.text = $text,
                    c.embedding = $embedding,
                    c.chunk_index = $chunk_index,
                    c.paragraph_context = $paragraph_context
                WITH c
                MATCH (n:LegalNorm {id: $norm_id})
                MERGE (n)-[:HAS_CHUNK]->(c)
                """
                
                paragraph_context = f"{sgb_nummer or ''} {norm.enbez} - {norm.titel}"
                
                tx.run(chunk_query,
                    text=chunk_text,
                    embedding=embedding.tolist(),
                    chunk_index=idx,
                    paragraph_context=paragraph_context,
                    norm_id=norm.id
                )
            
            logger.debug(f"Created {len(chunks)} chunks for {norm.enbez}")


if __name__ == "__main__":
    # Test the knowledge graph builder
    from xml_downloader import GIIXMLDownloader
    from xml_legal_parser import LegalXMLParser
    from neo4j import GraphDatabase
    import os
    
    print("\n=== Testing Legal Knowledge Graph Builder ===")
    
    # Download and parse SGB II
    downloader = GIIXMLDownloader()
    xml_path = downloader.download_law_xml("II")
    
    parser = LegalXMLParser()
    document = parser.parse_dokument(xml_path)
    
    print(f"\nParsed: {document.jurabk}")
    print(f"Norms: {len(document.norms)}")
    
    # Connect to Neo4j
    uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    username = os.getenv("NEO4J_USERNAME", "neo4j")
    password = os.getenv("NEO4J_PASSWORD", "password")
    
    driver = GraphDatabase.driver(uri, auth=(username, password))
    
    # Build knowledge graph
    print("\n=== Building Knowledge Graph ===")
    kg_builder = LegalKnowledgeGraphBuilder(driver)
    kg_builder.build_from_xml(document)
    
    print("\n✅ Knowledge graph built successfully!")
    
    driver.close()
