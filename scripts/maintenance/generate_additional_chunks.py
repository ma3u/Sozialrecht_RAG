#!/usr/bin/env python3
"""
Generate Additional Chunks for Low-Coverage SGBs

Generates chunks for norms that have fewer than 2 chunks, improving
semantic search quality for low-coverage SGBs.
"""

import os
from neo4j import GraphDatabase
from sentence_transformers import SentenceTransformer
from langchain.text_splitter import RecursiveCharacterTextSplitter

class ChunkGenerator:
    def __init__(self):
        uri = os.environ.get('NEO4J_URI', 'bolt://localhost:7687')
        username = os.environ.get('NEO4J_USERNAME', 'neo4j')
        password = os.environ.get('NEO4J_PASSWORD', 'password')
        
        self.driver = GraphDatabase.driver(uri, auth=(username, password))
        
        # Load embedding model
        print("Loading embedding model...")
        self.embedding_model = SentenceTransformer('paraphrase-multilingual-mpnet-base-v2')
        
        # Text splitter for chunking
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=800,
            chunk_overlap=100,
            separators=["\n\n§", "\n\n", "\n", ". ", " ", ""]
        )
    
    def find_low_coverage_norms(self, target_sgbs=None):
        """Find norms with < 2 chunks"""
        print("\n" + "="*80)
        print("FINDING LOW-COVERAGE NORMS")
        print("="*80)
        
        with self.driver.session() as session:
            if target_sgbs:
                sgb_filter = f"AND doc.sgb_nummer IN {target_sgbs}"
            else:
                sgb_filter = ""
            
            result = session.run(f"""
                MATCH (doc:LegalDocument)-[:HAS_STRUCTURE|CONTAINS_NORM*1..3]->(norm:LegalNorm)
                WHERE norm.content_text IS NOT NULL 
                  {sgb_filter}
                OPTIONAL MATCH (norm)-[:HAS_CHUNK]->(c:Chunk)
                WITH norm, doc.sgb_nummer as sgb, count(c) as chunk_count
                WHERE chunk_count < 2
                RETURN sgb, 
                       count(norm) as low_coverage_norms,
                       sum(CASE WHEN chunk_count = 0 THEN 1 ELSE 0 END) as no_chunks,
                       sum(CASE WHEN chunk_count = 1 THEN 1 ELSE 0 END) as one_chunk
                ORDER BY sgb
            """)
            
            results = {}
            for record in result:
                sgb = record['sgb']
                results[sgb] = {
                    'total': record['low_coverage_norms'],
                    'no_chunks': record['no_chunks'],
                    'one_chunk': record['one_chunk']
                }
                print(f"SGB {sgb:>4}: {record['low_coverage_norms']:4} norms need chunks " +
                      f"({record['no_chunks']} with 0, {record['one_chunk']} with 1)")
            
            return results
    
    def generate_chunks_for_sgb(self, sgb):
        """Generate chunks for all low-coverage norms in an SGB"""
        print(f"\n{'='*80}")
        print(f"GENERATING CHUNKS FOR SGB {sgb}")
        print("="*80)
        
        with self.driver.session() as session:
            # Get norms that need chunks
            result = session.run("""
                MATCH (doc:LegalDocument {sgb_nummer: $sgb})
                      -[:HAS_STRUCTURE|CONTAINS_NORM*1..3]->(norm:LegalNorm)
                WHERE norm.content_text IS NOT NULL
                OPTIONAL MATCH (norm)-[:HAS_CHUNK]->(c:Chunk)
                WITH norm, count(c) as chunk_count
                WHERE chunk_count < 2
                RETURN norm.id as norm_id, 
                       norm.enbez as enbez,
                       norm.titel as titel,
                       norm.content_text as content,
                       chunk_count
                ORDER BY chunk_count, norm.enbez
            """, sgb=sgb)
            
            norms = list(result)
            print(f"Found {len(norms)} norms needing chunks\n")
            
            chunks_created = 0
            for i, record in enumerate(norms, 1):
                chunks_added = self._generate_chunks_for_norm(
                    session, 
                    record['norm_id'],
                    record['enbez'],
                    record['content'],
                    record['chunk_count'],
                    sgb
                )
                chunks_created += chunks_added
                
                if i % 10 == 0:
                    print(f"  Progress: {i}/{len(norms)} norms processed...")
            
            print(f"\n✅ Created {chunks_created} new chunks for SGB {sgb}")
            return chunks_created
    
    def _generate_chunks_for_norm(self, session, norm_id, enbez, content, existing_chunks, sgb):
        """Generate chunks for a single norm"""
        if not content or len(content) < 50:
            return 0
        
        # Split text into chunks
        chunks = self.text_splitter.split_text(content)
        
        # Calculate how many chunks to add (aim for at least 2 total)
        chunks_needed = max(2 - existing_chunks, 0)
        if chunks_needed == 0:
            return 0
        
        # Take the needed chunks
        chunks_to_add = chunks[:chunks_needed] if len(chunks) >= chunks_needed else chunks
        
        # Generate embeddings
        embeddings = self.embedding_model.encode(chunks_to_add, show_progress_bar=False)
        
        # Add chunks to Neo4j
        for idx, (chunk_text, embedding) in enumerate(zip(chunks_to_add, embeddings)):
            session.run("""
                MATCH (norm:LegalNorm {id: $norm_id})
                CREATE (c:Chunk {
                    text: $text,
                    embedding: $embedding,
                    chunk_index: $chunk_index,
                    paragraph_context: $context
                })
                CREATE (norm)-[:HAS_CHUNK]->(c)
            """, 
            norm_id=norm_id,
            text=chunk_text,
            embedding=embedding.tolist(),
            chunk_index=existing_chunks + idx,
            context=f"{sgb} {enbez}"
            )
        
        return len(chunks_to_add)
    
    def generate_for_all_low_coverage_sgbs(self):
        """Generate chunks for all SGBs with low coverage"""
        target_sgbs = ['I', 'III', 'VII', 'VIII', 'X', 'XII', 'XIV']
        
        # Find what needs to be done
        low_coverage = self.find_low_coverage_norms(target_sgbs)
        
        total_created = 0
        for sgb in target_sgbs:
            if sgb in low_coverage and low_coverage[sgb]['total'] > 0:
                created = self.generate_chunks_for_sgb(sgb)
                total_created += created
        
        print(f"\n{'='*80}")
        print(f"SUMMARY")
        print("="*80)
        print(f"Total chunks created: {total_created}")
        
        return total_created
    
    def close(self):
        self.driver.close()


def main():
    generator = ChunkGenerator()
    
    try:
        # Generate chunks for all low-coverage SGBs
        total = generator.generate_for_all_low_coverage_sgbs()
        
        print(f"\n🎉 Successfully generated {total} additional chunks!")
        print(f"\nRun verify_sgb_coverage.py to see the improvements.")
        
    finally:
        generator.close()


if __name__ == '__main__':
    main()
