"""
Sozialrecht Neo4j RAG System
Spezialisiertes RAG-System für deutsche Sozialgesetzbücher mit Quellenvalidierung

Basiert auf: ms-agentf-neo4j/neo4j-rag-demo/src/neo4j_rag.py
Angepasst für: Rechts-spezifische Anforderungen, Quellenvertrauenswürdigkeit, Hybrid-Strategie
"""

import os
import logging
from typing import List, Dict, Optional, Tuple
from neo4j import GraphDatabase
from sentence_transformers import SentenceTransformer
import numpy as np
from langchain.text_splitter import RecursiveCharacterTextSplitter
import time
from concurrent.futures import ThreadPoolExecutor
import threading
from datetime import datetime
import hashlib

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SozialrechtNeo4jRAG:
    """
    Neo4j RAG-System spezialisiert für Sozialrecht-Dokumente

    Features:
    - Paragraph-basierte Chunking-Strategie
    - Quellen-Vertrauenswürdigkeits-Tracking
    - Hybrid-Strategie für Gesetze + Weisungen
    - Metadata-Tracking (SGB, Paragraph, Stand-Datum, Quelle)
    """

    # Quellen-Vertrauenswürdigkeits-Scores
    SOURCE_TRUST_SCORES = {
        'gesetze-im-internet.de': 100,
        'arbeitsagentur.de': 95,
        'bmas.de': 95,
        'harald-thome.de': 85,
        'dguv.de': 85,
        'bih.de': 80,
        'tacheles-sozialhilfe.de': 85
    }

    # Dokument-Typ-Hierarchie (für Konfliktauflösung)
    DOC_TYPE_PRIORITY = {
        'Gesetz': 1,
        'BA_Weisung': 2,
        'BMAS_Rundschreiben': 3,
        'Harald_Thome': 4,
        'Fachverband': 5
    }

    def __init__(self, uri: str = None, username: str = None, password: str = None):
        """Initialize Sozialrecht Neo4j RAG System

        Args:
            uri: Neo4j connection URI
            username: Neo4j username
            password: Neo4j password
        """
        # Default to local Neo4j
        uri = uri or os.getenv("NEO4J_URI", "bolt://localhost:7687")
        username = username or os.getenv("NEO4J_USERNAME", "neo4j")
        password = password or os.getenv("NEO4J_PASSWORD", "password")

        self.driver = GraphDatabase.driver(
            uri,
            auth=(username, password),
            max_connection_pool_size=10,
            connection_timeout=30.0
        )

        # German embedding model for better legal text understanding
        logger.info("Loading German embedding model...")
        self.embedding_model = SentenceTransformer('paraphrase-multilingual-mpnet-base-v2')
        self._embedding_lock = threading.Lock()

        # Paragraph-specific text splitter (larger chunks for legal context)
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=800,  # Larger for legal paragraphs
            chunk_overlap=100,  # More overlap for context preservation
            separators=["\n\n§", "\n\n", "\n", ". ", " ", ""]  # Paragraph-aware
        )

        # Query cache
        self._query_cache = {}
        self._cache_lock = threading.Lock()

        # Initialize schema
        self._initialize_sozialrecht_schema()

        logger.info(f"✅ Sozialrecht RAG System initialized with URI: {uri}")

    def _initialize_sozialrecht_schema(self):
        """Create Sozialrecht-specific Neo4j schema"""
        with self.driver.session() as session:
            # Create constraints
            session.run("""
                CREATE CONSTRAINT IF NOT EXISTS FOR (d:Document) REQUIRE d.id IS UNIQUE
            """)

            session.run("""
                CREATE CONSTRAINT IF NOT EXISTS FOR (p:Paragraph) REQUIRE p.id IS UNIQUE
            """)

            # Create indexes for Sozialrecht-specific queries
            try:
                # SGB-specific index
                session.run("""
                    CREATE INDEX IF NOT EXISTS FOR (d:Document) ON (d.sgb_nummer)
                """)

                # Paragraph number index
                session.run("""
                    CREATE INDEX IF NOT EXISTS FOR (p:Paragraph) ON (p.paragraph_nummer)
                """)

                # Source trust score index
                session.run("""
                    CREATE INDEX IF NOT EXISTS FOR (d:Document) ON (d.trust_score)
                """)

                # Document type index (for hybrid strategy)
                session.run("""
                    CREATE INDEX IF NOT EXISTS FOR (d:Document) ON (d.document_type)
                """)

                # Full-text search index for chunks
                try:
                    session.run("""
                        CREATE FULLTEXT INDEX sozialrecht_fulltext IF NOT EXISTS
                        FOR (c:Chunk) ON EACH [c.text, c.paragraph_context]
                    """)
                except Exception:
                    logger.warning("Fulltext index might already exist")

            except Exception as e:
                logger.warning(f"Some indexes might already exist: {e}")

            logger.info("✅ Sozialrecht-specific Neo4j schema initialized")

    def add_sgb_document(self,
                        content: str,
                        sgb_nummer: str,
                        document_type: str,
                        source_url: str,
                        metadata: Optional[Dict] = None) -> str:
        """Add a Sozialrecht document with specific metadata

        Args:
            content: Full document text
            sgb_nummer: SGB number (I, II, III, etc.)
            document_type: 'Gesetz', 'BA_Weisung', 'BMAS_Rundschreiben', etc.
            source_url: Original download URL
            metadata: Additional metadata (stand_datum, paragraph_nummer, etc.)

        Returns:
            Document ID
        """
        # Generate document ID
        doc_id = hashlib.sha256(f"{sgb_nummer}_{document_type}_{content[:100]}".encode()).hexdigest()[:16]

        # Determine source domain and trust score
        trust_score = self._calculate_trust_score(source_url)

        # Build complete metadata
        doc_metadata = {
            'sgb_nummer': sgb_nummer,
            'document_type': document_type,
            'source_url': source_url,
            'trust_score': trust_score,
            'source_domain': self._extract_domain(source_url),
            'type_priority': self.DOC_TYPE_PRIORITY.get(document_type, 99),
            'extracted_date': datetime.now().isoformat()
        }

        if metadata:
            doc_metadata.update(metadata)

        # Add to Neo4j
        with self.driver.session() as session:
            with session.begin_transaction() as tx:
                self._add_document_with_paragraphs(
                    tx, doc_id, content, doc_metadata
                )
                tx.commit()

        logger.info(f"✅ Added: {sgb_nummer} {document_type} (ID: {doc_id}, Trust: {trust_score}%)")
        return doc_id

    def _calculate_trust_score(self, source_url: str) -> int:
        """Calculate trust score based on source domain"""
        for domain, score in self.SOURCE_TRUST_SCORES.items():
            if domain in source_url:
                return score
        return 70  # Default for unknown sources

    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL"""
        import re
        match = re.search(r'https?://([^/]+)', url)
        return match.group(1) if match else 'unknown'

    def _add_document_with_paragraphs(self, tx, doc_id: str, content: str, metadata: Dict):
        """Add document with paragraph-aware chunking"""

        # Split into chunks (paragraph-aware)
        chunks = self.text_splitter.split_text(content)

        # Generate embeddings in batch
        with self._embedding_lock:
            embeddings = self.embedding_model.encode(chunks)

        # Create Document node
        cypher_create_doc = """
            MERGE (d:Document {id: $doc_id})
            SET d.content = $content,
                d.created = datetime(),
                d.chunk_count = $chunk_count,
                d.sgb_nummer = $sgb_nummer,
                d.document_type = $document_type,
                d.source_url = $source_url,
                d.source_domain = $source_domain,
                d.trust_score = $trust_score,
                d.type_priority = $type_priority
        """

        doc_params = {
            'doc_id': doc_id,
            'content': content[:5000],  # Limit content length in node
            'chunk_count': len(chunks),
            'sgb_nummer': metadata.get('sgb_nummer', 'Unknown'),
            'document_type': metadata.get('document_type', 'Unknown'),
            'source_url': metadata.get('source_url', ''),
            'source_domain': metadata.get('source_domain', ''),
            'trust_score': metadata.get('trust_score', 70),
            'type_priority': metadata.get('type_priority', 99)
        }

        # Add optional metadata
        optional_fields = ['stand_datum', 'paragraph_nummer', 'filename', 'file_size_mb']
        for field in optional_fields:
            if field in metadata:
                cypher_create_doc += f", d.{field} = ${field}"
                doc_params[field] = metadata[field]

        tx.run(cypher_create_doc, **doc_params)

        # Create Chunk nodes with paragraph context
        chunk_data = []
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            # Extract paragraph number if present in chunk
            paragraph_nummer = self._extract_paragraph_number(chunk)

            chunk_data.append({
                'doc_id': doc_id,
                'text': chunk,
                'embedding': embedding.tolist(),
                'index': i,
                'paragraph_nummer': paragraph_nummer,
                'paragraph_context': chunk[:200]  # First 200 chars for context
            })

        # Batch insert chunks
        tx.run("""
            UNWIND $chunk_data as chunk
            MATCH (d:Document {id: chunk.doc_id})
            CREATE (c:Chunk {
                text: chunk.text,
                embedding: chunk.embedding,
                chunk_index: chunk.index,
                paragraph_nummer: chunk.paragraph_nummer,
                paragraph_context: chunk.paragraph_context
            })
            CREATE (d)-[:HAS_CHUNK]->(c)
        """, chunk_data=chunk_data)

        # Create Paragraph nodes if paragraph numbers found
        paragraphs_found = set(c['paragraph_nummer'] for c in chunk_data if c['paragraph_nummer'])

        if paragraphs_found:
            for para_num in paragraphs_found:
                para_chunks = [c for c in chunk_data if c['paragraph_nummer'] == para_num]
                para_text = "\n\n".join([c['text'] for c in para_chunks])

                tx.run("""
                    MERGE (p:Paragraph {id: $para_id})
                    SET p.paragraph_nummer = $paragraph_nummer,
                        p.sgb_nummer = $sgb_nummer,
                        p.content = $content,
                        p.chunk_count = $chunk_count
                    WITH p
                    MATCH (d:Document {id: $doc_id})
                    MERGE (d)-[:CONTAINS_PARAGRAPH]->(p)
                """, {
                    'para_id': f"{metadata['sgb_nummer']}_{para_num}",
                    'paragraph_nummer': para_num,
                    'sgb_nummer': metadata['sgb_nummer'],
                    'content': para_text[:5000],
                    'chunk_count': len(para_chunks),
                    'doc_id': doc_id
                })

    def _extract_paragraph_number(self, text: str) -> Optional[str]:
        """Extract paragraph number from text (§ X, § XX, etc.)"""
        import re
        match = re.search(r'§\s*(\d+[a-z]?(?:\s*Abs\.?\s*\d+)?)', text)
        return match.group(1) if match else None

    def hybrid_search_with_source_ranking(self,
                                         query: str,
                                         k: int = 5,
                                         prefer_gesetz: bool = True) -> List[Dict]:
        """
        Hybrid search mit Quellen-Hierarchie

        Args:
            query: Suchanfrage
            k: Anzahl Ergebnisse
            prefer_gesetz: Bevorzuge Gesetz vor Weisungen (für Beträge/Fristen)

        Returns:
            List of results mit Trust-Score und Source-Priority
        """
        # Generate query embedding
        with self._embedding_lock:
            query_embedding = self.embedding_model.encode([query])[0]

        with self.driver.session() as session:
            # Vector search mit Source-Ranking
            result = session.run("""
                MATCH (d:Document)-[:HAS_CHUNK]->(c:Chunk)
                WITH d, c,
                     gds.similarity.cosine(c.embedding, $query_embedding) as similarity
                ORDER BY similarity DESC
                LIMIT $limit
                RETURN c.text as text,
                       c.paragraph_nummer as paragraph_nummer,
                       similarity as score,
                       d.id as doc_id,
                       d.sgb_nummer as sgb_nummer,
                       d.document_type as document_type,
                       d.trust_score as trust_score,
                       d.type_priority as type_priority,
                       d.source_url as source_url,
                       d.stand_datum as stand_datum,
                       d.filename as filename
            """, query_embedding=query_embedding.tolist(), limit=k*3)

            chunks = []
            for record in result:
                # Calculate combined score (similarity + trust + type priority)
                similarity_score = float(record['score'])
                trust_score = int(record.get('trust_score', 70))
                type_priority = int(record.get('type_priority', 99))

                # Weighted scoring
                combined_score = (
                    similarity_score * 0.6 +  # Semantic similarity (60%)
                    (trust_score / 100) * 0.25 +  # Source trust (25%)
                    (1 - type_priority / 100) * 0.15  # Type priority (15%)
                )

                # Boost Gesetz if prefer_gesetz=True
                if prefer_gesetz and record.get('document_type') == 'Gesetz':
                    combined_score *= 1.2

                chunks.append({
                    'text': record['text'],
                    'paragraph': record.get('paragraph_nummer'),
                    'score': combined_score,
                    'similarity': similarity_score,
                    'doc_id': record['doc_id'],
                    'sgb': record.get('sgb_nummer', 'Unknown'),
                    'type': record.get('document_type', 'Unknown'),
                    'trust_score': trust_score,
                    'source_url': record.get('source_url', ''),
                    'stand_datum': record.get('stand_datum'),
                    'filename': record.get('filename', '')
                })

            # Sort by combined score
            chunks.sort(key=lambda x: x['score'], reverse=True)
            return chunks[:k]

    def search_by_sgb_and_paragraph(self,
                                    sgb_nummer: str,
                                    paragraph_nummer: str) -> List[Dict]:
        """
        Suche spezifisch nach SGB und Paragraph

        Args:
            sgb_nummer: z.B. "II", "III", "VI"
            paragraph_nummer: z.B. "20", "11a", "136"

        Returns:
            Alle Dokumente zu diesem Paragraph (Gesetz + Weisungen)
        """
        with self.driver.session() as session:
            result = session.run("""
                MATCH (d:Document)-[:CONTAINS_PARAGRAPH]->(p:Paragraph)
                WHERE d.sgb_nummer = $sgb AND p.paragraph_nummer = $paragraph
                RETURN d.document_type as type,
                       d.trust_score as trust,
                       d.filename as filename,
                       d.stand_datum as stand_datum,
                       p.content as content
                ORDER BY d.type_priority ASC, d.trust_score DESC
            """, sgb=sgb_nummer, paragraph=paragraph_nummer)

            return [{
                'type': record['type'],
                'trust': record['trust'],
                'filename': record['filename'],
                'stand_datum': record['stand_datum'],
                'content': record['content']
            } for record in result]

    def get_hybrid_answer(self,
                         query: str,
                         detect_betrag_anfrage: bool = True) -> Dict:
        """
        Hybrid-Strategie: Gesetz für Beträge, Weisung für Verfahren

        Args:
            query: Benutzeranfrage
            detect_betrag_anfrage: Automatisch erkennen ob Betrag/Frist gefragt ist

        Returns:
            Antwort mit Gesetz- und Weisungs-Quellen
        """
        # Detect if this is a query about amounts/dates
        is_betrag_query = detect_betrag_anfrage and any(word in query.lower() for word in [
            'regelbedarf', 'betrag', 'höhe', 'euro', '€', 'frist', 'datum',
            'wie viel', 'wieviel', 'berechnung', 'satz'
        ])

        # Search Gesetz with high priority
        gesetz_results = self.hybrid_search_with_source_ranking(
            query, k=3, prefer_gesetz=True
        )

        # Search Weisungen
        weisungen_results = self.hybrid_search_with_source_ranking(
            query, k=3, prefer_gesetz=False
        )

        # Build answer
        answer_parts = []

        if is_betrag_query and gesetz_results:
            # For amounts: Prioritize Gesetz
            gesetz_text = gesetz_results[0]['text']
            answer_parts.append(f"**Rechtliche Grundlage (Gesetz):**\n{gesetz_text}\n")
            answer_parts.append(f"📚 Quelle: {gesetz_results[0]['filename']} (SGB {gesetz_results[0]['sgb']})")
            answer_parts.append(f"   Vertrauenswürdigkeit: {gesetz_results[0]['trust_score']}% ⭐⭐⭐⭐⭐\n")

            if weisungen_results:
                weisung_text = weisungen_results[0]['text']
                answer_parts.append(f"**Anwendungshinweise (Fachliche Weisung):**\n{weisung_text}\n")
                answer_parts.append(f"📚 Quelle: {weisungen_results[0]['filename']}")
                if weisungen_results[0]['stand_datum']:
                    answer_parts.append(f"   Stand: {weisungen_results[0]['stand_datum']}")
                answer_parts.append(f"   Vertrauenswürdigkeit: {weisungen_results[0]['trust_score']}%\n")
        else:
            # For procedural questions: Combine both
            all_results = gesetz_results + weisungen_results
            all_results.sort(key=lambda x: x['score'], reverse=True)

            for i, result in enumerate(all_results[:3]):
                answer_parts.append(f"**Quelle {i+1} ({result['type']}):**\n{result['text']}\n")
                answer_parts.append(f"📚 {result['filename']} (SGB {result['sgb']})")
                if result['stand_datum']:
                    answer_parts.append(f"   Stand: {result['stand_datum']}")
                answer_parts.append(f"   Vertrauenswürdigkeit: {result['trust_score']}%")
                answer_parts.append(f"   Relevanz: {result['similarity']:.2%}\n")

        # Add disclaimer
        answer_parts.append("\n⚠️ **Disclaimer**: Keine Rechtsberatung. Bei Rechtsfragen Behörde konsultieren!")

        return {
            'answer': "\n".join(answer_parts),
            'gesetz_sources': gesetz_results,
            'weisung_sources': weisungen_results,
            'is_betrag_query': is_betrag_query
        }

    def get_stats(self) -> Dict:
        """Get Sozialrecht-specific statistics"""
        with self.driver.session() as session:
            result = session.run("""
                MATCH (d:Document)
                OPTIONAL MATCH (d)-[:HAS_CHUNK]->(c:Chunk)
                OPTIONAL MATCH (d)-[:CONTAINS_PARAGRAPH]->(p:Paragraph)
                WITH COUNT(DISTINCT d) as doc_count,
                     COUNT(DISTINCT c) as chunk_count,
                     COUNT(DISTINCT p) as paragraph_count,
                     d.sgb_nummer as sgb,
                     d.document_type as type
                RETURN doc_count, chunk_count, paragraph_count,
                       COLLECT(DISTINCT sgb) as sgbs,
                       COLLECT(DISTINCT type) as types
            """)

            record = result.single()

            return {
                'documents': record['doc_count'],
                'chunks': record['chunk_count'],
                'paragraphs': record['paragraph_count'],
                'sgbs_covered': record['sgbs'],
                'document_types': record['types'],
                'cache_size': len(self._query_cache)
            }

    def close(self):
        """Close Neo4j connection"""
        self.driver.close()
        logger.info("✅ Neo4j connection closed")


if __name__ == "__main__":
    # Demo usage
    rag = SozialrechtNeo4jRAG()

    # Example: Add SGB II § 20 Gesetz
    example_content = """
    § 20 Regelbedarf zur Sicherung des Lebensunterhalts

    (1) Der Regelbedarf zur Sicherung des Lebensunterhalts umfasst insbesondere
    Ernährung, Kleidung, Körperpflege, Hausrat, Haushaltsenergie ohne die auf die
    Heizung entfallenden Anteile sowie persönliche Bedürfnisse des täglichen Lebens.

    (2) Als Regelbedarf wird monatlich für Personen, die alleinstehend oder
    alleinerziehend sind, ein Betrag von 563 Euro anerkannt (Regelbedarfsstufe 1).
    """

    doc_id = rag.add_sgb_document(
        content=example_content,
        sgb_nummer="II",
        document_type="Gesetz",
        source_url="https://www.gesetze-im-internet.de/sgb_2/__20.html",
        metadata={
            'paragraph_nummer': '20',
            'stand_datum': '2025-01-01',
            'filename': 'SGB_02_Buergergeld.pdf'
        }
    )

    print(f"\n✅ Document added with ID: {doc_id}")

    # Test hybrid search
    response = rag.get_hybrid_answer("Was ist der Regelbedarf für Alleinstehende?")
    print(f"\n📝 Hybrid Answer:\n{response['answer']}")

    # Print stats
    stats = rag.get_stats()
    print(f"\n📊 Database Stats: {stats}")

    rag.close()
