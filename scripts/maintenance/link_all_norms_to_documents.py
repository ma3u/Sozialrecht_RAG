#!/usr/bin/env python3
"""
Link All Norms to Documents Script

Ensures all LegalNorm nodes with chunks are properly connected to their
parent LegalDocument nodes, making all chunks accessible for queries.
"""

import os
from neo4j import GraphDatabase
from datetime import datetime

class NormLinker:
    def __init__(self):
        uri = os.environ.get('NEO4J_URI', 'bolt://localhost:7687')
        username = os.environ.get('NEO4J_USERNAME', 'neo4j')
        password = os.environ.get('NEO4J_PASSWORD', 'password')
        
        self.driver = GraphDatabase.driver(uri, auth=(username, password))
    
    def analyze_situation(self):
        """Analyze current linking situation"""
        print("\n" + "="*80)
        print("ANALYZING NORM-TO-DOCUMENT LINKAGE")
        print("="*80)
        
        with self.driver.session() as session:
            # Count norms with chunks
            result = session.run("""
                MATCH (norm:LegalNorm)-[:HAS_CHUNK]->(c:Chunk)
                WITH norm, count(c) as chunks
                OPTIONAL MATCH (doc:LegalDocument)-[:HAS_STRUCTURE|CONTAINS_NORM*1..3]->(norm)
                RETURN 
                    count(DISTINCT CASE WHEN doc IS NOT NULL THEN norm END) as linked_norms,
                    count(DISTINCT CASE WHEN doc IS NULL THEN norm END) as unlinked_norms,
                    sum(CASE WHEN doc IS NOT NULL THEN chunks ELSE 0 END) as linked_chunks,
                    sum(CASE WHEN doc IS NULL THEN chunks ELSE 0 END) as unlinked_chunks
            """)
            
            record = result.single()
            linked_norms = record['linked_norms']
            unlinked_norms = record['unlinked_norms']
            linked_chunks = record['linked_chunks']
            unlinked_chunks = record['unlinked_chunks']
            
            print(f"\nNorms with chunks:")
            print(f"  ✅ Linked to documents: {linked_norms:,} norms ({linked_chunks:,} chunks)")
            print(f"  ❌ Not linked: {unlinked_norms:,} norms ({unlinked_chunks:,} chunks)")
            
            if unlinked_norms == 0:
                print(f"\n🎉 All norms are properly linked!")
                return False
            else:
                print(f"\n⚠️  {unlinked_norms:,} norms need linking")
                return True
    
    def link_norms_via_doknr(self):
        """Link norms to documents by matching doknr"""
        print("\n" + "="*80)
        print("LINKING NORMS VIA DOKNR MATCHING")
        print("="*80)
        
        with self.driver.session() as session:
            result = session.run("""
                MATCH (norm:LegalNorm)-[:HAS_CHUNK]->(c:Chunk)
                WHERE NOT EXISTS {
                    MATCH (doc:LegalDocument)-[:HAS_STRUCTURE|CONTAINS_NORM*1..3]->(norm)
                }
                AND norm.norm_doknr IS NOT NULL
                WITH norm, substring(norm.norm_doknr, 0, 13) as doc_doknr
                MATCH (doc:LegalDocument)
                WHERE doc.doknr = doc_doknr
                MERGE (doc)-[:CONTAINS_NORM]->(norm)
                RETURN count(*) as linked
            """)
            
            linked = result.single()['linked']
            print(f"✅ Linked {linked:,} norms to documents via doknr matching")
            return linked
    
    def link_norms_via_id_pattern(self):
        """Link norms to documents by parsing norm ID"""
        print("\n" + "="*80)
        print("LINKING NORMS VIA ID PATTERN MATCHING")
        print("="*80)
        
        with self.driver.session() as session:
            # Try to extract SGB number from norm ID
            result = session.run("""
                MATCH (norm:LegalNorm)-[:HAS_CHUNK]->(c:Chunk)
                WHERE NOT EXISTS {
                    MATCH (doc:LegalDocument)-[:HAS_STRUCTURE|CONTAINS_NORM*1..3]->(norm)
                }
                AND norm.id CONTAINS 'SGB_'
                WITH norm, split(norm.id, '_')[1] as sgb_nr
                MATCH (doc:LegalDocument)
                WHERE doc.sgb_nummer = sgb_nr
                MERGE (doc)-[:CONTAINS_NORM]->(norm)
                RETURN count(*) as linked
            """)
            
            linked = result.single()['linked']
            print(f"✅ Linked {linked:,} norms to documents via ID pattern")
            return linked
    
    def verify_results(self):
        """Verify the linking worked"""
        print("\n" + "="*80)
        print("VERIFICATION")
        print("="*80)
        
        with self.driver.session() as session:
            # Check final stats
            result = session.run("""
                MATCH (c:Chunk)
                OPTIONAL MATCH (norm:LegalNorm)-[:HAS_CHUNK]->(c)
                OPTIONAL MATCH (doc:LegalDocument)-[:HAS_STRUCTURE|CONTAINS_NORM*1..3]->(norm)
                WITH 
                    count(DISTINCT c) as total_chunks,
                    count(DISTINCT CASE WHEN doc IS NOT NULL THEN c END) as accessible_chunks
                RETURN total_chunks, accessible_chunks, 
                       (accessible_chunks * 100.0 / total_chunks) as coverage_pct
            """)
            
            record = result.single()
            total = record['total_chunks']
            accessible = record['accessible_chunks']
            coverage = record['coverage_pct']
            
            print(f"\nFinal Statistics:")
            print(f"  Total chunks: {total:,}")
            print(f"  Accessible chunks: {accessible:,}")
            print(f"  Coverage: {coverage:.1f}%")
            
            if coverage >= 99:
                print(f"\n🎉 EXCELLENT: {coverage:.1f}% chunk coverage!")
            elif coverage >= 90:
                print(f"\n✅ GOOD: {coverage:.1f}% chunk coverage")
            else:
                print(f"\n⚠️  WARNING: Only {coverage:.1f}% chunk coverage")
            
            # Show per-SGB breakdown
            result = session.run("""
                MATCH (doc:LegalDocument)-[:HAS_STRUCTURE|CONTAINS_NORM*1..3]->(norm:LegalNorm)-[:HAS_CHUNK]->(c:Chunk)
                RETURN doc.sgb_nummer as sgb, count(DISTINCT c) as chunks
                ORDER BY sgb
            """)
            
            print(f"\nChunks per SGB:")
            for record in result:
                print(f"  SGB {record['sgb']:>4}: {record['chunks']:>6,} chunks")
    
    def close(self):
        self.driver.close()


def main():
    linker = NormLinker()
    
    try:
        # Analyze
        needs_linking = linker.analyze_situation()
        
        if needs_linking:
            # Link via doknr
            linked_doknr = linker.link_norms_via_doknr()
            
            # Link via ID pattern
            linked_id = linker.link_norms_via_id_pattern()
            
            print(f"\n📊 Total norms linked: {linked_doknr + linked_id:,}")
        
        # Verify
        linker.verify_results()
        
    finally:
        linker.close()


if __name__ == '__main__':
    main()
