#!/usr/bin/env python3
"""
Validation Script for Phase 2 Import
Verifies amendment data in Neo4j after import
"""

import os
from neo4j import GraphDatabase
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

NEO4J_URI = os.getenv('NEO4J_URI', 'bolt://localhost:7687')
NEO4J_USER = os.getenv('NEO4J_USER', 'neo4j')
NEO4J_PASSWORD = os.getenv('NEO4J_PASSWORD', 'password')


def run_validation():
    """Run all validation queries"""
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    
    print("=" * 70)
    print("PHASE 2 IMPORT VALIDATION")
    print("=" * 70)
    print()
    
    with driver.session() as session:
        # 1. Verify Amendment nodes
        print("📊 1. Amendment Nodes")
        print("-" * 70)
        result = session.run("""
            MATCH (a:Amendment)
            RETURN count(a) as count,
                   collect(DISTINCT a.amendment_type) as types,
                   collect(DISTINCT a.amendment_date)[0..5] as sample_dates
        """)
        record = result.single()
        print(f"   Total Amendments: {record['count']}")
        print(f"   Amendment Types: {record['types']}")
        print(f"   Sample Dates: {record['sample_dates']}")
        
        # Get detailed amendment info
        result = session.run("""
            MATCH (n:Norm)-[:HAS_AMENDMENT]->(a:Amendment)
            RETURN n.norm_doknr as norm,
                   a.amendment_date as date,
                   a.artikel as artikel,
                   a.gesetz_ref as gesetz,
                   a.raw_text as text
            LIMIT 3
        """)
        print("\n   Sample Amendments:")
        for i, record in enumerate(result, 1):
            print(f"   [{i}] Norm: {record['norm']}")
            print(f"       Date: {record['date']}")
            print(f"       Artikel: {record['artikel']}")
            print(f"       Gesetz: {record['gesetz']}")
            print(f"       Text: {record['text'][:100]}...")
            print()
        
        # 2. Verify BGBl nodes
        print("\n📊 2. BGBl References")
        print("-" * 70)
        result = session.run("""
            MATCH (b:BGBl)
            RETURN count(b) as count
        """)
        count = result.single()['count']
        print(f"   Total BGBl Nodes: {count}")
        
        result = session.run("""
            MATCH (doc:LegalDocument)-[:PUBLISHED_IN]->(b:BGBl)
            RETURN doc.kurzue as document,
                   b.full_reference as reference,
                   b.year as year,
                   b.page as page
        """)
        print("\n   BGBl Details:")
        for record in result:
            print(f"   Document: {record['document']}")
            print(f"   Reference: {record['reference']}")
            print(f"   Year: {record['year']}, Page: {record['page']}")
        
        # 3. Verify Fussnoten nodes
        print("\n📊 3. Fussnote Nodes")
        print("-" * 70)
        result = session.run("""
            MATCH (f:Fussnote)
            RETURN count(f) as count
        """)
        count = result.single()['count']
        print(f"   Total Fussnoten: {count}")
        
        result = session.run("""
            MATCH (n:Norm)-[:HAS_FUSSNOTE]->(f:Fussnote)
            RETURN count(DISTINCT n) as norms_with_fussnoten,
                   collect(DISTINCT f.valid_from)[0..5] as sample_dates
        """)
        record = result.single()
        print(f"   Norms with Fussnoten: {record['norms_with_fussnoten']}")
        print(f"   Sample Valid-From Dates: {record['sample_dates']}")
        
        # Show sample fussnote
        result = session.run("""
            MATCH (n:Norm)-[:HAS_FUSSNOTE]->(f:Fussnote)
            RETURN n.norm_doknr as norm,
                   f.valid_from as valid_from,
                   f.in_kraft as in_kraft,
                   f.context as context
            LIMIT 2
        """)
        print("\n   Sample Fussnoten:")
        for i, record in enumerate(result, 1):
            print(f"   [{i}] Norm: {record['norm']}")
            print(f"       Valid From: {record['valid_from']}")
            print(f"       In Kraft: {record['in_kraft']}")
            print(f"       Context: {record['context'][:100]}...")
            print()
        
        # 4. Verify SUPERSEDED_BY relationships
        print("\n📊 4. SUPERSEDED_BY Relationships")
        print("-" * 70)
        result = session.run("""
            MATCH ()-[r:SUPERSEDED_BY]->()
            RETURN count(r) as count
        """)
        count = result.single()['count']
        print(f"   Total SUPERSEDED_BY Relationships: {count}")
        
        if count > 0:
            result = session.run("""
                MATCH (a1:Amendment)-[:SUPERSEDED_BY]->(a2:Amendment)
                RETURN a1.amendment_date as old_date,
                       a2.amendment_date as new_date,
                       a1.raw_text as old_text
                LIMIT 3
            """)
            print("\n   Sample Superseded Chains:")
            for i, record in enumerate(result, 1):
                print(f"   [{i}] {record['old_date']} → {record['new_date']}")
                print(f"       {record['old_text'][:80]}...")
        
        # 5. Verify Indexes
        print("\n📊 5. Indexes")
        print("-" * 70)
        result = session.run("""
            SHOW INDEXES
            YIELD name, labelsOrTypes, properties, type
            WHERE any(label IN labelsOrTypes WHERE label IN ['Amendment', 'BGBl', 'Fussnote'])
            RETURN name, labelsOrTypes, properties, type
        """)
        print("   Amendment-Related Indexes:")
        for record in result:
            print(f"   - {record['name']}: {record['labelsOrTypes']} ON {record['properties']} ({record['type']})")
        
        # 6. Coverage Statistics
        print("\n📊 6. Coverage Statistics")
        print("-" * 70)
        result = session.run("""
            MATCH (n:Norm)
            WITH count(n) as total_norms
            MATCH (n:Norm)-[:HAS_AMENDMENT]->(a:Amendment)
            WITH total_norms, count(DISTINCT n) as norms_with_amendments
            RETURN total_norms,
                   norms_with_amendments,
                   round(100.0 * norms_with_amendments / total_norms, 2) as coverage_pct
        """)
        record = result.single()
        print(f"   Total Norms: {record['total_norms']}")
        print(f"   Norms with Amendments: {record['norms_with_amendments']}")
        print(f"   Coverage: {record['coverage_pct']}%")
        
        # 7. Data Quality Check
        print("\n📊 7. Data Quality Checks")
        print("-" * 70)
        
        # Amendments with dates
        result = session.run("""
            MATCH (a:Amendment)
            WITH count(a) as total,
                 count(a.amendment_date) as with_dates
            RETURN total, with_dates,
                   round(100.0 * with_dates / total, 2) as pct
        """)
        record = result.single()
        print(f"   ✓ Amendments with dates: {record['with_dates']}/{record['total']} ({record['pct']}%)")
        
        # Amendments with Artikel
        result = session.run("""
            MATCH (a:Amendment)
            WHERE a.artikel IS NOT NULL
            RETURN count(a) as count
        """)
        count = result.single()['count']
        print(f"   ✓ Amendments with Artikel: {count}")
        
        # Amendments with Gesetz reference
        result = session.run("""
            MATCH (a:Amendment)
            WHERE a.gesetz_ref IS NOT NULL
            RETURN count(a) as count
        """)
        count = result.single()['count']
        print(f"   ✓ Amendments with Gesetz ref: {count}")
        
        # Orphaned amendments (should be 0)
        result = session.run("""
            MATCH (a:Amendment)
            WHERE NOT (a)<-[:HAS_AMENDMENT]-()
            RETURN count(a) as count
        """)
        count = result.single()['count']
        status = "✓" if count == 0 else "⚠"
        print(f"   {status} Orphaned Amendments: {count}")
    
    print("\n" + "=" * 70)
    print("✅ VALIDATION COMPLETE")
    print("=" * 70)
    
    driver.close()


if __name__ == '__main__':
    try:
        run_validation()
    except Exception as e:
        print(f"\n❌ Validation failed: {e}")
        import traceback
        traceback.print_exc()
