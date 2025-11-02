#!/usr/bin/env python3
"""
SGB Coverage Verification and Improvement Script

Verifies that all SGBs have complete chunk coverage and fixes any issues.
"""

import os
import sys
from neo4j import GraphDatabase
from datetime import datetime
import json

class SGBCoverageVerifier:
    def __init__(self):
        uri = os.environ.get('NEO4J_URI', 'bolt://localhost:7687')
        username = os.environ.get('NEO4J_USERNAME', 'neo4j')
        password = os.environ.get('NEO4J_PASSWORD', 'password')
        
        self.driver = GraphDatabase.driver(uri, auth=(username, password))
        self.report = {
            'timestamp': datetime.now().isoformat(),
            'sgbs': {},
            'orphaned_norms': 0,
            'orphaned_chunks': 0,
            'total_chunks': 0,
            'accessible_chunks': 0
        }
    
    def verify_all_sgbs(self):
        """Verify chunk coverage for all SGBs"""
        print("\n" + "="*80)
        print("SGB COVERAGE VERIFICATION REPORT")
        print("="*80)
        print(f"Timestamp: {self.report['timestamp']}\n")
        
        with self.driver.session() as session:
            # Get all SGB documents
            result = session.run("""
                MATCH (doc:LegalDocument)
                WHERE doc.sgb_nummer IS NOT NULL
                RETURN doc.sgb_nummer as sgb, doc.jurabk as jurabk, doc.id as doc_id
                ORDER BY doc.sgb_nummer
            """)
            
            sgbs = [dict(record) for record in result]
            
            print(f"Found {len(sgbs)} SGB documents\n")
            print("-"*80)
            
            for sgb_doc in sgbs:
                self._verify_single_sgb(session, sgb_doc['sgb'], sgb_doc['doc_id'])
            
            # Check orphaned norms
            self._check_orphaned_norms(session)
            
            # Summary
            self._print_summary()
    
    def _verify_single_sgb(self, session, sgb, doc_id):
        """Verify a single SGB's coverage"""
        result = session.run("""
            MATCH (doc:LegalDocument {id: $doc_id})
            OPTIONAL MATCH (doc)-[:HAS_STRUCTURE]->(struct:StructuralUnit)
            OPTIONAL MATCH (doc)-[:CONTAINS_NORM]->(norm:LegalNorm)
            OPTIONAL MATCH (struct)-[:CONTAINS_NORM]->(struct_norm:LegalNorm)
            WITH doc, 
                 count(DISTINCT struct) as structures,
                 count(DISTINCT norm) + count(DISTINCT struct_norm) as norms
            OPTIONAL MATCH (doc)-[:HAS_STRUCTURE|CONTAINS_NORM*1..3]->(n:LegalNorm)-[:HAS_CHUNK]->(c:Chunk)
            RETURN structures, norms, count(DISTINCT c) as chunks
        """, doc_id=doc_id)
        
        record = result.single()
        structures = record['structures'] or 0
        norms = record['norms'] or 0
        chunks = record['chunks'] or 0
        
        # Determine status
        if chunks == 0:
            status = "❌ NO CHUNKS"
        elif chunks < norms * 2:  # Expect at least 2 chunks per norm on average
            status = "⚠️  LOW COVERAGE"
        else:
            status = "✅ COMPLETE"
        
        self.report['sgbs'][sgb] = {
            'structures': structures,
            'norms': norms,
            'chunks': chunks,
            'status': status
        }
        
        self.report['accessible_chunks'] += chunks
        
        print(f"SGB {sgb:>4} | {status:15} | Structures: {structures:4} | Norms: {norms:4} | Chunks: {chunks:6}")
    
    def _check_orphaned_norms(self, session):
        """Check for orphaned norms"""
        result = session.run("""
            MATCH (norm:LegalNorm)
            WHERE NOT EXISTS {
                MATCH (doc:LegalDocument)-[:CONTAINS_NORM]->(norm)
            }
            AND NOT EXISTS {
                MATCH ()-[:CONTAINS_NORM]->(norm)
            }
            OPTIONAL MATCH (norm)-[:HAS_CHUNK]->(c:Chunk)
            RETURN count(DISTINCT norm) as orphaned_norms, count(DISTINCT c) as orphaned_chunks
        """)
        
        record = result.single()
        self.report['orphaned_norms'] = record['orphaned_norms'] or 0
        self.report['orphaned_chunks'] = record['orphaned_chunks'] or 0
        
        print("-"*80)
        print(f"\nOrphaned Norms: {self.report['orphaned_norms']}")
        print(f"Orphaned Chunks: {self.report['orphaned_chunks']}")
    
    def _print_summary(self):
        """Print summary statistics"""
        with self.driver.session() as session:
            result = session.run("MATCH (c:Chunk) RETURN count(c) as total")
            self.report['total_chunks'] = result.single()['total']
        
        accessible = self.report['accessible_chunks']
        total = self.report['total_chunks']
        coverage_pct = (accessible / total * 100) if total > 0 else 0
        
        print("\n" + "="*80)
        print("SUMMARY")
        print("="*80)
        print(f"Total Chunks in Database: {total:,}")
        print(f"Accessible via SGBs: {accessible:,} ({coverage_pct:.1f}%)")
        print(f"Orphaned Chunks: {self.report['orphaned_chunks']:,} ({self.report['orphaned_chunks']/total*100:.1f}%)")
        
        # Count status
        complete = sum(1 for sgb in self.report['sgbs'].values() if '✅' in sgb['status'])
        low_coverage = sum(1 for sgb in self.report['sgbs'].values() if '⚠️' in sgb['status'])
        no_chunks = sum(1 for sgb in self.report['sgbs'].values() if '❌' in sgb['status'])
        
        print(f"\nSGB Status:")
        print(f"  ✅ Complete Coverage: {complete}")
        print(f"  ⚠️  Low Coverage: {low_coverage}")
        print(f"  ❌ No Chunks: {no_chunks}")
        
        if coverage_pct >= 95:
            print(f"\n🎉 EXCELLENT: {coverage_pct:.1f}% chunk coverage - production ready!")
        elif coverage_pct >= 80:
            print(f"\n✅ GOOD: {coverage_pct:.1f}% chunk coverage - acceptable for production")
        elif coverage_pct >= 50:
            print(f"\n⚠️  WARNING: Only {coverage_pct:.1f}% chunk coverage - improvements needed")
        else:
            print(f"\n❌ CRITICAL: Only {coverage_pct:.1f}% chunk coverage - immediate action required")
    
    def generate_missing_chunks_report(self):
        """Generate report of SGBs that need chunk generation"""
        print("\n" + "="*80)
        print("SGBs NEEDING CHUNK GENERATION")
        print("="*80)
        
        needs_work = []
        for sgb, data in self.report['sgbs'].items():
            if data['chunks'] == 0 or (data['norms'] > 0 and data['chunks'] < data['norms']):
                needs_work.append((sgb, data))
        
        if not needs_work:
            print("✅ All SGBs have adequate chunk coverage!")
        else:
            for sgb, data in needs_work:
                print(f"\nSGB {sgb}:")
                print(f"  Norms: {data['norms']}")
                print(f"  Chunks: {data['chunks']}")
                print(f"  Status: {data['status']}")
                print(f"  Action: Generate chunks for {data['norms']} norms")
    
    def save_report(self, filename='logs/sgb_coverage_report.json'):
        """Save report to JSON file"""
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        with open(filename, 'w') as f:
            json.dump(self.report, f, indent=2)
        print(f"\n📄 Report saved to: {filename}")
    
    def close(self):
        self.driver.close()


def main():
    verifier = SGBCoverageVerifier()
    
    try:
        # Run verification
        verifier.verify_all_sgbs()
        
        # Generate reports
        verifier.generate_missing_chunks_report()
        
        # Save report
        verifier.save_report()
        
    finally:
        verifier.close()


if __name__ == '__main__':
    main()
