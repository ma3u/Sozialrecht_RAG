#!/usr/bin/env python3
"""
Find DOKNR Patterns and Create SGB Mappings

Identifiziert doknr-Muster der verbleibenden orphaned Norms und
erstellt Mappings zu den korrekten SGBs.

Usage:
    python scripts/find_doknr_patterns.py --unmapped-only
    python scripts/find_doknr_patterns.py --create-links  # Execute repair
"""

import os
import argparse
from dotenv import load_dotenv
from neo4j import GraphDatabase

load_dotenv()

# Bekannte SGB-DOKNR-Mappings (erweitert)
SGB_DOKNR_MAP = {
    # Bereits gemappt (aus link_orphaned_norms.py)
    'BJNR295500003': 'II',     # Grundsicherung für Arbeitsuchende
    'BJNR059500997': 'III',    # Arbeitsförderung
    'BJNR138450976': 'IV',     # Gemeinsame Vorschriften
    'BJNR024820988': 'V',      # Gesetzliche Krankenversicherung
    'BJNR122610989': 'VI',     # Gesetzliche Rentenversicherung
    'BJNR111630990': 'VIII',   # Kinder- und Jugendhilfe
    'BJNR101500994': 'XI',     # Soziale Pflegeversicherung
    
    # Neu identifizierte Mappings (aus Analyse)
    'BJNR323410016': 'IX',     # Rehabilitation und Teilhabe (2016)
    'BJNR125410996': 'VII',    # Gesetzliche Unfallversicherung
    'BJNR302300003': 'XII',    # Sozialhilfe
    'BJNR265210019': 'XIV',    # Soziale Entschädigung (2019)
    'BJNR114690980': 'X',      # Sozialverwaltungsverfahren und Sozialdatenschutz
    'BJNR030150975': 'I',      # Allgemeiner Teil
    'BJNR104600001': 'XIII',   # (historisch, ggf. nicht mehr gültig)
}


class DoknrMapper:
    """Mapped doknr patterns to SGBs and creates relationships."""
    
    def __init__(self):
        self.uri = os.getenv('NEO4J_URI')
        self.password = os.getenv('NEO4J_PASSWORD')
        self.driver = GraphDatabase.driver(self.uri, auth=('neo4j', self.password))
    
    def close(self):
        self.driver.close()
    
    def analyze_unmapped(self):
        """Zeigt unmapped doknr patterns."""
        print("=" * 80)
        print("UNMAPPED DOKNR PATTERNS")
        print("=" * 80)
        
        with self.driver.session() as session:
            result = session.run('''
                MATCH (norm:LegalNorm)-[:HAS_CHUNK]->(c:Chunk)
                WHERE NOT EXISTS {
                    MATCH (doc:LegalDocument)-[:CONTAINS_NORM]->(norm)
                }
                AND norm.norm_doknr IS NOT NULL
                WITH substring(norm.norm_doknr, 0, 13) as doknr_prefix,
                     count(DISTINCT norm) as norms,
                     count(c) as chunks
                RETURN doknr_prefix, norms, chunks
                ORDER BY chunks DESC
            ''')
            
            print(f"\n{'DOKNR Prefix':<20} | {'SGB':<8} | {'Norms':>8} | {'Chunks':>8} | Status")
            print("-" * 80)
            
            total_mapped = 0
            total_unmapped = 0
            
            for r in result:
                prefix = r['doknr_prefix']
                norms = r['norms']
                chunks = r['chunks']
                
                if prefix in SGB_DOKNR_MAP:
                    sgb = SGB_DOKNR_MAP[prefix]
                    status = "✅ Mapped"
                    total_mapped += chunks
                else:
                    sgb = "?"
                    status = "❌ Unknown"
                    total_unmapped += chunks
                
                print(f"{prefix:<20} | {sgb:<8} | {norms:>8,} | {chunks:>8,} | {status}")
            
            print("-" * 80)
            print(f"Total mapped chunks: {total_mapped:,}")
            print(f"Total unmapped chunks: {total_unmapped:,}")
            print(f"Mapping coverage: {total_mapped/(total_mapped+total_unmapped)*100:.1f}%")
    
    def create_links(self, dry_run=True):
        """Erstellt CONTAINS_NORM Links für gemappte doknr patterns."""
        mode = "DRY RUN" if dry_run else "EXECUTING"
        print(f"\n{'='*80}")
        print(f"CREATE LINKS FROM DOKNR MAPPINGS [{mode}]")
        print("=" * 80)
        
        total_created = 0
        
        with self.driver.session() as session:
            for doknr_prefix, sgb_num in sorted(SGB_DOKNR_MAP.items(), key=lambda x: x[1]):
                # Check if target document exists
                doc_check = session.run('''
                    MATCH (doc:LegalDocument {sgb_nummer: $sgb, doknr: $doknr})
                    RETURN count(*) as exists
                ''', sgb=sgb_num, doknr=doknr_prefix)
                
                doc_exists = doc_check.single()['exists'] > 0
                
                if not doc_exists:
                    print(f"\n⚠️  SGB {sgb_num} (doknr: {doknr_prefix}): No matching LegalDocument found")
                    continue
                
                if dry_run:
                    # Count what would be created
                    result = session.run('''
                        MATCH (doc:LegalDocument {sgb_nummer: $sgb, doknr: $doknr})
                        MATCH (norm:LegalNorm)
                        WHERE norm.norm_doknr STARTS WITH $doknr
                          AND NOT EXISTS {
                              MATCH (any_doc:LegalDocument)-[:CONTAINS_NORM]->(norm)
                          }
                        RETURN count(*) as would_create
                    ''', sgb=sgb_num, doknr=doknr_prefix)
                    
                    count = result.single()['would_create']
                    if count > 0:
                        print(f"  SGB {sgb_num:<4}: Would create {count:>5,} links")
                    total_created += count
                else:
                    # Actually create links
                    result = session.run('''
                        MATCH (doc:LegalDocument {sgb_nummer: $sgb, doknr: $doknr})
                        MATCH (norm:LegalNorm)
                        WHERE norm.norm_doknr STARTS WITH $doknr
                          AND NOT EXISTS {
                              MATCH (any_doc:LegalDocument)-[:CONTAINS_NORM]->(norm)
                          }
                        CREATE (doc)-[:CONTAINS_NORM]->(norm)
                        RETURN count(*) as created
                    ''', sgb=sgb_num, doknr=doknr_prefix)
                    
                    count = result.single()['created']
                    if count > 0:
                        print(f"  SGB {sgb_num:<4}: Created {count:>5,} links")
                    total_created += count
        
        print("-" * 80)
        if dry_run:
            print(f"  TOTAL: Would create {total_created:,} links")
            print("\n⚠️  Run with --create-links to apply changes")
        else:
            print(f"  TOTAL: Created {total_created:,} links")
            print("\n✅ Links created successfully!")
        
        return total_created
    
    def verify_coverage(self):
        """Verifiziert Coverage nach Linking."""
        print(f"\n{'='*80}")
        print("VERIFICATION: Coverage After DOKNR Linking")
        print("=" * 80)
        
        with self.driver.session() as session:
            # Total orphaned
            result = session.run('''
                MATCH (norm:LegalNorm)-[:HAS_CHUNK]->(c:Chunk)
                WHERE NOT EXISTS {
                    MATCH (doc:LegalDocument)-[:CONTAINS_NORM]->(norm)
                }
                RETURN count(DISTINCT norm) as orphans, count(c) as orphan_chunks
            ''')
            r = result.single()
            
            print(f"\n📊 Remaining Orphans:")
            print(f"  Orphaned norms: {r['orphans']:,}")
            print(f"  Orphaned chunks: {r['orphan_chunks']:,}")
            
            # Total accessible
            result = session.run('''
                MATCH (doc:LegalDocument)-[:CONTAINS_NORM]->(norm:LegalNorm)
                                        -[:HAS_CHUNK]->(c:Chunk)
                RETURN count(DISTINCT c) as accessible_chunks
            ''')
            accessible = result.single()['accessible_chunks']
            
            result = session.run('MATCH (c:Chunk) RETURN count(c) as total')
            total = result.single()['total']
            
            coverage = (accessible / total * 100) if total > 0 else 0
            
            print(f"\n📈 Total Coverage:")
            print(f"  Total chunks: {total:,}")
            print(f"  Accessible: {accessible:,} ({coverage:.1f}%)")
            print(f"  Orphaned: {total - accessible:,} ({100-coverage:.1f}%)")
            
            if r['orphans'] == 0:
                print("\n✅ SUCCESS: All norms with chunks are now connected!")
            elif r['orphans'] < 100:
                print(f"\n⚠️  Only {r['orphans']} orphaned norms remaining - excellent progress!")
            else:
                print(f"\n⚠️  {r['orphans']} orphaned norms remaining - further investigation needed")


def main():
    parser = argparse.ArgumentParser(description='Find and map DOKNR patterns to SGBs')
    parser.add_argument('--unmapped-only', action='store_true',
                       help='Show only unmapped doknr patterns')
    parser.add_argument('--create-links', action='store_true',
                       help='Create CONTAINS_NORM links (WARNING: modifies database!)')
    parser.add_argument('--verify', action='store_true',
                       help='Verify coverage after linking')
    
    args = parser.parse_args()
    
    if not any([args.unmapped_only, args.create_links, args.verify]):
        parser.print_help()
        print("\n⚠️  Please specify at least one action")
        return
    
    mapper = DoknrMapper()
    
    try:
        if args.unmapped_only or (not args.create_links and not args.verify):
            mapper.analyze_unmapped()
        
        if args.create_links:
            # Dry run first
            mapper.create_links(dry_run=True)
            
            print("\n" + "="*80)
            print("⚠️  WARNING: This will modify the Neo4j database!")
            print("="*80)
            confirm = input("\nType 'yes' to proceed: ")
            if confirm.lower() == 'yes':
                mapper.create_links(dry_run=False)
            else:
                print("\n❌ Aborted by user")
                return
        
        if args.verify or args.create_links:
            mapper.verify_coverage()
    
    finally:
        mapper.close()


if __name__ == '__main__':
    main()
