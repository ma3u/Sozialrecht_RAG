#!/usr/bin/env python3
"""
Link Orphaned Legal Norms to their Correct SGB Documents

This script repairs the critical data integrity issue where 2,227 LegalNorm nodes
with 9,604 chunks are orphaned (not connected to any LegalDocument).

Strategy:
- Match orphaned norms to LegalDocuments using norm_doknr prefix
- Create missing CONTAINS_NORM relationships
- Verify complete Document→Norm→Chunk paths after repair

Usage:
    python scripts/link_orphaned_norms.py --analyze  # Show what will be fixed
    python scripts/link_orphaned_norms.py --fix      # Execute the repair
    python scripts/link_orphaned_norms.py --verify   # Verify after fix
"""

import os
import argparse
from dotenv import load_dotenv
from neo4j import GraphDatabase

load_dotenv()

# Mapping of norm_doknr prefixes to SGB numbers
SGB_DOKNR_MAP = {
    'BJNR295500003': 'II',     # Grundsicherung für Arbeitsuchende
    'BJNR059500997': 'III',    # Arbeitsförderung
    'BJNR138450976': 'IV',     # Gemeinsame Vorschriften
    'BJNR024820988': 'V',      # Gesetzliche Krankenversicherung
    'BJNR122610989': 'VI',     # Gesetzliche Rentenversicherung
    'BJNR111630990': 'VIII',   # Kinder- und Jugendhilfe
    'BJNR101500994': 'XI',     # Soziale Pflegeversicherung
}


class OrphanedNormLinker:
    def __init__(self):
        self.uri = os.getenv('NEO4J_URI')
        self.password = os.getenv('NEO4J_PASSWORD')
        self.driver = GraphDatabase.driver(self.uri, auth=('neo4j', self.password))
    
    def close(self):
        self.driver.close()
    
    def analyze(self):
        """Analyze orphaned norms that can be linked."""
        print("=" * 90)
        print("ANALYSIS: Orphaned LegalNorm Nodes with Chunks")
        print("=" * 90)
        
        with self.driver.session() as session:
            print("\n📋 Orphaned Norms by SGB (matchable via norm_doknr):\n")
            print(f"{'SGB':<8} | {'Norms':>8} | {'Chunks':>10} | {'Document ID':<25}")
            print("-" * 90)
            
            total_norms = 0
            total_chunks = 0
            
            for doknr_prefix, sgb_num in sorted(SGB_DOKNR_MAP.items(), key=lambda x: x[1]):
                result = session.run('''
                    MATCH (norm:LegalNorm)
                    WHERE norm.norm_doknr STARTS WITH $prefix
                    OPTIONAL MATCH (doc_connected:LegalDocument)-[:CONTAINS_NORM]->(norm)
                    WITH norm, doc_connected
                    WHERE doc_connected IS NULL
                    OPTIONAL MATCH (norm)-[:HAS_CHUNK]->(c:Chunk)
                    RETURN count(DISTINCT norm) as norms, count(c) as chunks
                ''', prefix=doknr_prefix)
                
                r = result.single()
                if r and r['norms'] > 0:
                    norms = r['norms']
                    chunks = r['chunks']
                    total_norms += norms
                    total_chunks += chunks
                    print(f"SGB {sgb_num:<4} | {norms:>8,} | {chunks:>10,} | {doknr_prefix}")
            
            print("-" * 90)
            print(f"{'TOTAL':<8} | {total_norms:>8,} | {total_chunks:>10,} |")
            print()
            
            # Check if target documents exist
            print("\n🔍 Verifying target LegalDocument nodes exist:\n")
            for doknr_prefix, sgb_num in sorted(SGB_DOKNR_MAP.items(), key=lambda x: x[1]):
                result = session.run('''
                    MATCH (doc:LegalDocument)
                    WHERE doc.doknr = $doknr AND doc.sgb_nummer = $sgb
                    RETURN count(*) as exists
                ''', doknr=doknr_prefix, sgb=sgb_num)
                
                exists = result.single()['exists']
                status = "✅" if exists > 0 else "❌ MISSING"
                print(f"  SGB {sgb_num:<4}: {status}")
    
    def fix(self, dry_run=True):
        """Create CONTAINS_NORM relationships for orphaned norms."""
        mode = "DRY RUN" if dry_run else "EXECUTING"
        print("\n" + "=" * 90)
        print(f"REPAIR: Linking Orphaned Norms to Documents [{mode}]")
        print("=" * 90)
        
        total_created = 0
        
        with self.driver.session() as session:
            print()
            for doknr_prefix, sgb_num in sorted(SGB_DOKNR_MAP.items(), key=lambda x: x[1]):
                if not dry_run:
                    result = session.run('''
                        // Find the target document
                        MATCH (doc:LegalDocument {doknr: $doknr, sgb_nummer: $sgb})
                        // Find orphaned norms matching this doknr prefix
                        MATCH (norm:LegalNorm)
                        WHERE norm.norm_doknr STARTS WITH $doknr
                          AND NOT EXISTS {
                              MATCH (doc2:LegalDocument)-[:CONTAINS_NORM]->(norm)
                          }
                        // Create the relationship
                        CREATE (doc)-[:CONTAINS_NORM]->(norm)
                        RETURN count(*) as created
                    ''', doknr=doknr_prefix, sgb=sgb_num)
                    
                    created = result.single()['created']
                    total_created += created
                    print(f"  SGB {sgb_num:<4}: Created {created:>5,} CONTAINS_NORM relationships")
                else:
                    # Just count what would be created
                    result = session.run('''
                        MATCH (doc:LegalDocument {doknr: $doknr, sgb_nummer: $sgb})
                        MATCH (norm:LegalNorm)
                        WHERE norm.norm_doknr STARTS WITH $doknr
                        OPTIONAL MATCH (doc_check:LegalDocument)-[:CONTAINS_NORM]->(norm)
                        WITH norm, doc, doc_check
                        WHERE doc_check IS NULL
                        RETURN count(*) as would_create
                    ''', doknr=doknr_prefix, sgb=sgb_num)
                    
                    would_create = result.single()['would_create']
                    total_created += would_create
                    print(f"  SGB {sgb_num:<4}: Would create {would_create:>5,} CONTAINS_NORM relationships")
            
            print("-" * 90)
            if dry_run:
                print(f"  TOTAL: Would create {total_created:,} relationships")
                print("\n⚠️  Run with --fix to apply changes")
            else:
                print(f"  TOTAL: Created {total_created:,} relationships")
                print("\n✅ Repair complete!")
    
    def verify(self):
        """Verify SGB coverage after linking."""
        print("\n" + "=" * 90)
        print("VERIFICATION: SGB Coverage After Repair")
        print("=" * 90)
        
        with self.driver.session() as session:
            print("\n📊 Complete Path Status (Document → Norm → Chunk):\n")
            print(f"{'SGB':<8} | {'Total Norms':>12} | {'Norms w/Chunks':>15} | {'Total Chunks':>12} | Status")
            print("-" * 90)
            
            result = session.run('''
                MATCH (doc:LegalDocument)
                OPTIONAL MATCH (doc)-[:CONTAINS_NORM]->(norm:LegalNorm)
                OPTIONAL MATCH (norm)-[:HAS_CHUNK]->(c:Chunk)
                RETURN 
                    doc.sgb_nummer as sgb,
                    count(DISTINCT norm) as total_norms,
                    count(DISTINCT CASE WHEN c IS NOT NULL THEN norm END) as norms_with_chunks,
                    count(DISTINCT c) as total_chunks,
                    CASE 
                        WHEN count(DISTINCT c) > 0 THEN '✅'
                        ELSE '❌'
                    END as status
                ORDER BY sgb
            ''')
            
            for r in result:
                sgb = r['sgb']
                total_norms = r['total_norms']
                norms_with_chunks = r['norms_with_chunks']
                total_chunks = r['total_chunks']
                status = r['status']
                print(f"SGB {sgb:<4} | {total_norms:>12,} | {norms_with_chunks:>15,} | {total_chunks:>12,} | {status}")
            
            # Check remaining orphans
            print("\n")
            result = session.run('''
                MATCH (norm:LegalNorm)-[:HAS_CHUNK]->(c:Chunk)
                WHERE NOT EXISTS {
                    MATCH (doc:LegalDocument)-[:CONTAINS_NORM]->(norm)
                }
                RETURN count(DISTINCT norm) as orphan_norms, count(DISTINCT c) as orphan_chunks
            ''')
            
            r = result.single()
            orphan_norms = r['orphan_norms']
            orphan_chunks = r['orphan_chunks']
            
            if orphan_norms == 0:
                print("✅ SUCCESS: All norms with chunks are now connected to documents!")
            else:
                print(f"⚠️  {orphan_norms:,} norms with {orphan_chunks:,} chunks still orphaned")
                print("   → May require additional doknr mappings or manual investigation")
            
            # Show total chunk distribution
            print("\n📈 Total Chunk Distribution:\n")
            result = session.run('''
                MATCH (c:Chunk)
                RETURN count(c) as total_chunks
            ''')
            total = result.single()['total_chunks']
            
            result = session.run('''
                MATCH (doc:LegalDocument)-[:CONTAINS_NORM]->(norm:LegalNorm)-[:HAS_CHUNK]->(c:Chunk)
                RETURN count(DISTINCT c) as connected_chunks
            ''')
            connected = result.single()['connected_chunks']
            
            pct = (connected / total * 100) if total > 0 else 0
            print(f"  Total chunks: {total:,}")
            print(f"  Connected via documents: {connected:,} ({pct:.1f}%)")
            print(f"  Orphaned: {total - connected:,} ({100-pct:.1f}%)")


def main():
    parser = argparse.ArgumentParser(
        description='Link orphaned LegalNorm nodes to their correct SGB LegalDocuments'
    )
    parser.add_argument('--analyze', action='store_true', help='Analyze orphaned norms')
    parser.add_argument('--fix', action='store_true', help='Execute repair (creates relationships)')
    parser.add_argument('--verify', action='store_true', help='Verify coverage after repair')
    
    args = parser.parse_args()
    
    if not any([args.analyze, args.fix, args.verify]):
        parser.print_help()
        print("\n⚠️  Please specify at least one action: --analyze, --fix, or --verify")
        return
    
    linker = OrphanedNormLinker()
    
    try:
        if args.analyze:
            linker.analyze()
            # Show dry run
            linker.fix(dry_run=True)
        
        if args.fix:
            print("\n" + "=" * 90)
            print("⚠️  WARNING: This will modify the Neo4j database!")
            print("   It will create CONTAINS_NORM relationships for orphaned norms.")
            print("=" * 90)
            confirm = input("\nType 'yes' to proceed: ")
            if confirm.lower() == 'yes':
                linker.fix(dry_run=False)
            else:
                print("\n❌ Aborted by user")
                return
        
        if args.verify:
            linker.verify()
    
    finally:
        linker.close()
    
    print("\n✅ Done!\n")


if __name__ == '__main__':
    main()
