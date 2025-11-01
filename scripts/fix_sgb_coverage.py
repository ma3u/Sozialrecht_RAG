#!/usr/bin/env python3
"""
Fix SGB Coverage - Repair Orphaned Legal Norms

This script addresses the critical issue where 2,246 LegalNorm nodes with 12,079 chunks
are not connected to any LegalDocument, making them inaccessible for case work queries.

Problem:
- Only SGB II has complete Document→Norm→Chunk paths
- 2,246 norms with chunks have no CONTAINS_NORM relationship from any document
- These orphaned norms contain ~12,079 chunks (29% of total)

Solution Strategy:
1. Analyze orphaned norm patterns (e.g., norm_doknr prefixes)
2. Match orphaned norms to existing LegalDocuments by identifier patterns
3. Create missing CONTAINS_NORM relationships
4. Verify chunk accessibility after repair

Usage:
    python scripts/fix_sgb_coverage.py --analyze  # Diagnostic mode (read-only)
    python scripts/fix_sgb_coverage.py --fix      # Execute repair (writes to DB)
    python scripts/fix_sgb_coverage.py --verify   # Post-repair verification
"""

import os
import argparse
from dotenv import load_dotenv
from neo4j import GraphDatabase
from collections import defaultdict

load_dotenv()


class SGBCoverageFixer:
    def __init__(self):
        self.uri = os.getenv('NEO4J_URI')
        self.password = os.getenv('NEO4J_PASSWORD')
        self.driver = GraphDatabase.driver(self.uri, auth=('neo4j', self.password))
    
    def close(self):
        self.driver.close()
    
    def analyze_orphaned_norms(self):
        """Analyze patterns in orphaned norms to determine repair strategy."""
        print("=" * 80)
        print("ANALYZING ORPHANED LEGAL NORMS")
        print("=" * 80)
        
        with self.driver.session() as session:
            # Find orphaned norms
            result = session.run('''
                MATCH (norm:LegalNorm)-[:HAS_CHUNK]->(c:Chunk)
                WHERE NOT ((:LegalDocument)-[:CONTAINS_NORM]->(norm))
                RETURN 
                    norm.norm_doknr as doknr,
                    norm.enbez as enbez,
                    norm.paragraph_nummer as para,
                    count(c) as chunks
                ORDER BY chunks DESC
                LIMIT 20
            ''')
            
            print("\n📊 Top 20 Orphaned Norms by Chunk Count:")
            print("-" * 80)
            orphans = []
            for r in result:
                doknr = r['doknr'] or 'N/A'
                enbez = r['enbez'] or 'N/A'
                para = r['para'] or 'N/A'
                chunks = r['chunks']
                print(f"  {doknr[:30]:<30} | {para[:20]:<20} | {chunks:>6,} chunks")
                orphans.append((doknr, enbez, para, chunks))
            
            # Extract SGB patterns from doknr
            print("\n🔍 Analyzing norm_doknr Patterns:")
            print("-" * 80)
            
            sgb_patterns = defaultdict(int)
            for doknr, _, _, chunks in orphans:
                if doknr and doknr != 'N/A':
                    # Example: BJNR295500003... → extract year/number to infer SGB
                    # SGB II: BJNR295500003 (2003, Law 2955)
                    # SGB XII: BJNR196300003 (2003, Law 1963)
                    prefix = doknr[:13] if len(doknr) >= 13 else doknr
                    sgb_patterns[prefix] += chunks
            
            for prefix, total_chunks in sorted(sgb_patterns.items(), key=lambda x: -x[1])[:10]:
                print(f"  {prefix}: {total_chunks:,} chunks")
            
            # Check if we can match by structural units
            print("\n🔗 Checking Alternative Connection Paths:")
            print("-" * 80)
            
            result = session.run('''
                MATCH (norm:LegalNorm)-[:HAS_CHUNK]->(c:Chunk)
                WHERE NOT ((:LegalDocument)-[:CONTAINS_NORM]->(norm))
                OPTIONAL MATCH (struct:StructuralUnit)-[:CONTAINS_NORM]->(norm)
                OPTIONAL MATCH (doc:LegalDocument)-[:HAS_STRUCTURE]->(struct)
                RETURN 
                    doc.sgb_nummer as sgb,
                    count(DISTINCT norm) as orphan_norms,
                    count(DISTINCT c) as chunks
                ORDER BY chunks DESC
            ''')
            
            print("  Via StructuralUnit:")
            for r in result:
                sgb = r['sgb'] if r['sgb'] else 'NOT_CONNECTED'
                print(f"    SGB {sgb}: {r['orphan_norms']:,} norms, {r['chunks']:,} chunks")
    
    def fix_via_structural_units(self, dry_run=True):
        """
        Repair Strategy: Connect orphaned norms through existing StructuralUnits.
        
        Path: LegalDocument → HAS_STRUCTURE → StructuralUnit → CONTAINS_NORM → LegalNorm
        
        We'll create direct CONTAINS_NORM relationships from LegalDocument to orphaned norms
        that are already connected via StructuralUnits.
        """
        print("\n" + "=" * 80)
        print("REPAIR STRATEGY: Link via Structural Units")
        print("=" * 80)
        
        mode = "DRY RUN" if dry_run else "EXECUTING"
        print(f"\n🔧 Mode: {mode}\n")
        
        with self.driver.session() as session:
            # First, check how many can be fixed
            result = session.run('''
                MATCH (doc:LegalDocument)-[:HAS_STRUCTURE]->(struct:StructuralUnit)
                      -[:CONTAINS_NORM]->(norm:LegalNorm)
                WHERE NOT ((doc)-[:CONTAINS_NORM]->(norm))
                  AND EXISTS((norm)-[:HAS_CHUNK]->(:Chunk))
                RETURN 
                    doc.sgb_nummer as sgb,
                    count(DISTINCT norm) as norms_to_link,
                    count(DISTINCT struct) as via_structures
                ORDER BY sgb
            ''')
            
            print("📋 Norms that can be linked to Documents via StructuralUnits:")
            print("-" * 80)
            total_fixable = 0
            for r in result:
                sgb = r['sgb']
                norms = r['norms_to_link']
                structs = r['via_structures']
                total_fixable += norms
                print(f"  SGB {sgb}: {norms:,} norms (via {structs:,} structures)")
            
            print(f"\n✅ Total fixable: {total_fixable:,} norms")
            
            if not dry_run:
                print("\n🔨 Creating CONTAINS_NORM relationships...")
                result = session.run('''
                    MATCH (doc:LegalDocument)-[:HAS_STRUCTURE]->(struct:StructuralUnit)
                          -[:CONTAINS_NORM]->(norm:LegalNorm)
                    WHERE NOT ((doc)-[:CONTAINS_NORM]->(norm))
                      AND EXISTS((norm)-[:HAS_CHUNK]->(:Chunk))
                    WITH doc, norm
                    CREATE (doc)-[:CONTAINS_NORM]->(norm)
                    RETURN count(*) as created
                ''')
                
                created = result.single()['created']
                print(f"✅ Created {created:,} new CONTAINS_NORM relationships")
                
                return created
            else:
                print("\n⚠️  No changes made (dry run mode)")
                return 0
    
    def verify_coverage(self):
        """Verify SGB coverage after repair."""
        print("\n" + "=" * 80)
        print("VERIFICATION: SGB Coverage Status")
        print("=" * 80)
        
        with self.driver.session() as session:
            # Check coverage for all SGBs
            result = session.run('''
                MATCH (doc:LegalDocument)
                OPTIONAL MATCH (doc)-[:CONTAINS_NORM]->(norm:LegalNorm)
                OPTIONAL MATCH (norm)-[:HAS_CHUNK]->(c:Chunk)
                RETURN 
                    doc.sgb_nummer as sgb,
                    count(DISTINCT norm) as total_norms,
                    count(DISTINCT c) as total_chunks,
                    CASE 
                        WHEN count(DISTINCT c) > 0 THEN '✅'
                        ELSE '❌'
                    END as status
                ORDER BY sgb
            ''')
            
            print("\n📊 Complete Path Status (Document → Norm → Chunk):")
            print("-" * 80)
            print(f"{'SGB':<8} | {'Norms':>8} | {'Chunks':>10} | Status")
            print("-" * 80)
            
            for r in result:
                sgb = r['sgb']
                norms = r['total_norms']
                chunks = r['total_chunks']
                status = r['status']
                print(f"{'SGB ' + sgb:<8} | {norms:>8,} | {chunks:>10,} | {status}")
            
            # Check remaining orphans
            print("\n")
            result = session.run('''
                MATCH (norm:LegalNorm)-[:HAS_CHUNK]->(c:Chunk)
                WHERE NOT ((:LegalDocument)-[:CONTAINS_NORM]->(norm))
                RETURN count(DISTINCT norm) as orphan_norms, count(c) as orphan_chunks
            ''')
            
            r = result.single()
            orphan_norms = r['orphan_norms']
            orphan_chunks = r['orphan_chunks']
            
            if orphan_norms == 0:
                print("✅ No orphaned norms remaining!")
            else:
                print(f"⚠️  {orphan_norms:,} norms with {orphan_chunks:,} chunks still orphaned")
                print("   → These may require manual SGB attribution or additional import data")


def main():
    parser = argparse.ArgumentParser(description='Fix SGB Coverage in Neo4j Knowledge Graph')
    parser.add_argument('--analyze', action='store_true', help='Analyze orphaned norms (read-only)')
    parser.add_argument('--fix', action='store_true', help='Execute repair (writes to database)')
    parser.add_argument('--verify', action='store_true', help='Verify coverage after fix')
    
    args = parser.parse_args()
    
    if not any([args.analyze, args.fix, args.verify]):
        parser.print_help()
        print("\n⚠️  Please specify at least one action: --analyze, --fix, or --verify")
        return
    
    fixer = SGBCoverageFixer()
    
    try:
        if args.analyze:
            fixer.analyze_orphaned_norms()
        
        if args.fix:
            print("\n" + "="*80)
            print("⚠️  WARNING: This will modify the Neo4j database!")
            print("="*80)
            confirm = input("\nType 'yes' to proceed: ")
            if confirm.lower() == 'yes':
                fixer.fix_via_structural_units(dry_run=False)
            else:
                print("❌ Aborted by user")
                return
        elif args.analyze:
            # Show what would be fixed
            fixer.fix_via_structural_units(dry_run=True)
        
        if args.verify:
            fixer.verify_coverage()
    
    finally:
        fixer.close()
    
    print("\n✅ Done!")


if __name__ == '__main__':
    main()
