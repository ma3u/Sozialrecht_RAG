#!/usr/bin/env python3
"""
Analyze Graph Schema and Identify Optimization Opportunities
"""

import sys
import os
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from neo4j import GraphDatabase
from dotenv import load_dotenv
import json

load_dotenv()


def analyze_schema(driver):
    """Analyze current graph schema"""
    print("\n" + "="*70)
    print("📊 GRAPH SCHEMA ANALYSIS")
    print("="*70)
    
    with driver.session() as session:
        # 1. Node labels and counts
        print("\n1️⃣  NODE TYPES")
        print("-" * 70)
        result = session.run("""
            CALL db.labels() YIELD label
            RETURN label
            ORDER BY label
        """)
        
        labels = [r['label'] for r in result]
        node_stats = []
        
        for label in labels:
            count_result = session.run(f"MATCH (n:`{label}`) RETURN count(n) as count")
            count = count_result.single()['count']
            node_stats.append((label, count))
        
        
        # Sort by count
        node_stats.sort(key=lambda x: x[1], reverse=True)
        
        for label, count in node_stats:
            print(f"  {label:<25} {count:>10,}")
        
        # 2. Relationship types and counts
        print("\n2️⃣  RELATIONSHIP TYPES")
        print("-" * 70)
        result = session.run("""
            CALL db.relationshipTypes() YIELD relationshipType
            RETURN relationshipType
            ORDER BY relationshipType
        """)
        
        rel_types = [r['relationshipType'] for r in result]
        rel_stats = []
        
        for rel_type in rel_types:
            count_result = session.run(f"MATCH ()-[r:`{rel_type}`]->() RETURN count(r) as count")
            count = count_result.single()['count']
            rel_stats.append((rel_type, count))
        
        # Sort by count
        rel_stats.sort(key=lambda x: x[1], reverse=True)
        
        for rel_type, count in rel_stats:
            print(f"  {rel_type:<25} {count:>10,}")
        
        # 3. Detailed relationship patterns
        print("\n3️⃣  RELATIONSHIP PATTERNS (with cardinality)")
        print("-" * 70)
        result = session.run("""
            MATCH (a)-[r]->(b)
            WITH labels(a)[0] as source, type(r) as rel, labels(b)[0] as target, count(*) as count
            RETURN source, rel, target, count
            ORDER BY count DESC
            LIMIT 20
        """)
        
        patterns = []
        for r in result:
            patterns.append({
                'source': r['source'],
                'rel': r['rel'],
                'target': r['target'],
                'count': r['count']
            })
            print(f"  ({r['source']})-[:{r['rel']}]->({r['target']})  {r['count']:>10,}")
        
        # 4. Orphaned nodes (nodes without relationships)
        print("\n4️⃣  ORPHANED NODES (nodes with no relationships)")
        print("-" * 70)
        
        orphaned = []
        for label in labels:
            count_result = session.run(f"""
                MATCH (n:`{label}`)
                WHERE NOT (n)--()
                RETURN count(n) as count
            """)
            count = count_result.single()['count']
            if count > 0:
                orphaned.append({'label': label, 'count': count})
        
        if orphaned:
            for r in orphaned:
                print(f"  {r['label']:<25} {r['count']:>10,} orphans")
        else:
            print("  ✅ No orphaned nodes found")
        
        # 5. Average degree (connections per node)
        print("\n5️⃣  AVERAGE DEGREE (avg connections per node)")
        print("-" * 70)
        
        degree_stats = []
        for label in labels:
            result = session.run(f"""
                MATCH (n:`{label}`)
                RETURN avg(COUNT {{ (n)--() }}) as avg_degree
            """)
            avg_degree = result.single()['avg_degree']
            if avg_degree is not None:
                degree_stats.append((label, avg_degree))
        
        # Sort by degree
        degree_stats.sort(key=lambda x: x[1], reverse=True)
        
        for label, avg_degree in degree_stats:
            print(f"  {label:<25} {avg_degree:>10.2f} connections/node")
        
        # 6. Property analysis
        print("\n6️⃣  PROPERTY KEYS (most common)")
        print("-" * 70)
        result = session.run("""
            CALL db.propertyKeys() YIELD propertyKey
            RETURN propertyKey
            ORDER BY propertyKey
            LIMIT 20
        """)
        
        props = [r['propertyKey'] for r in result]
        for prop in props:
            print(f"  • {prop}")
        
        return {
            'nodes': node_stats,
            'relationships': rel_stats,
            'patterns': patterns,
            'orphaned': orphaned
        }


def analyze_query_performance(driver):
    """Analyze performance of common query patterns"""
    print("\n" + "="*70)
    print("⚡ QUERY PERFORMANCE ANALYSIS")
    print("="*70)
    
    test_queries = [
        {
            'name': 'Direct Paragraph Lookup',
            'query': """
                MATCH (doc:LegalDocument {sgb_nummer: "II"})
                -[:HAS_STRUCTURE]->(struct:StructuralUnit)
                -[:CONTAINS_NORM]->(norm:LegalNorm)
                WHERE norm.paragraph_nummer = "20"
                RETURN norm.enbez
            """
        },
        {
            'name': 'Multi-hop Traversal (Doc -> Norm -> Chunk)',
            'query': """
                MATCH (doc:LegalDocument {sgb_nummer: "II"})
                -[:HAS_STRUCTURE]->()
                -[:CONTAINS_NORM]->(norm:LegalNorm)
                -[:HAS_CHUNK]->(chunk:Chunk)
                RETURN count(chunk) as chunks
                LIMIT 1
            """
        },
        {
            'name': 'Cross-document Pattern',
            'query': """
                MATCH (doc:LegalDocument)
                WHERE doc.sgb_nummer IN ["II", "III", "V"]
                RETURN doc.sgb_nummer, count(*) as count
            """
        },
        {
            'name': 'PDF Document Lookup',
            'query': """
                MATCH (d:Document {document_type: "Fachliche Weisung"})
                -[:HAS_CHUNK]->(c:Chunk)
                RETURN count(c) as chunks
                LIMIT 1
            """
        }
    ]
    
    print("\nQuery Patterns with EXPLAIN Analysis:\n")
    
    with driver.session() as session:
        for test in test_queries:
            print(f"📊 {test['name']}")
            print("-" * 70)
            
            # Run PROFILE to get actual execution stats
            result = session.run(f"PROFILE {test['query']}")
            
            # Get profile info
            profile = result.consume().profile
            
            if profile:
                print(f"  DB Hits: {profile.db_hits:,}")
                print(f"  Records: {profile.records:,}")
                
                # Print operator tree
                def print_operator(op, indent=0):
                    print(f"  {'  '*indent}└─ {op.operator_type}")
                    if op.arguments:
                        for key, val in list(op.arguments.items())[:3]:
                            print(f"  {'  '*indent}   {key}: {val}")
                    for child in op.children:
                        print_operator(child, indent+1)
                
                print_operator(profile)
            
            print()


def identify_optimization_opportunities(schema_data):
    """Identify specific optimization opportunities"""
    print("\n" + "="*70)
    print("💡 OPTIMIZATION OPPORTUNITIES")
    print("="*70)
    
    opportunities = []
    
    # 1. Check for long paths that could be shortcut
    print("\n1️⃣  RELATIONSHIP PATH OPTIMIZATIONS")
    print("-" * 70)
    
    # Check if we have doc -> struct -> norm pattern
    has_multi_hop = any(
        p['source'] == 'LegalDocument' and p['rel'] == 'HAS_STRUCTURE'
        for p in schema_data['patterns']
    )
    
    if has_multi_hop:
        opportunities.append({
            'type': 'Add Direct Relationship',
            'description': 'Create direct LegalDocument -> LegalNorm relationship',
            'reason': 'Avoid 2-hop traversal (Doc->Structure->Norm)',
            'impact': 'High - Most common query pattern',
            'query': """
                MATCH (doc:LegalDocument)-[:HAS_STRUCTURE]->(struct:StructuralUnit)
                      -[:CONTAINS_NORM]->(norm:LegalNorm)
                MERGE (doc)-[:CONTAINS_NORM]->(norm)
            """
        })
        print("  ✅ Add LegalDocument-[:CONTAINS_NORM]->LegalNorm")
        print("     Reason: Skip StructuralUnit hop for direct paragraph access")
    
    # 2. Check for potential denormalization
    print("\n2️⃣  DENORMALIZATION OPPORTUNITIES")
    print("-" * 70)
    
    opportunities.append({
        'type': 'Add SGB to Norm',
        'description': 'Copy sgb_nummer to LegalNorm nodes',
        'reason': 'Avoid join back to Document for SGB filtering',
        'impact': 'Medium - Speeds up SGB-specific queries',
        'query': """
            MATCH (doc:LegalDocument)-[:HAS_STRUCTURE]->()
                  -[:CONTAINS_NORM]->(norm:LegalNorm)
            SET norm.sgb_nummer = doc.sgb_nummer
        """
    })
    print("  ✅ Denormalize sgb_nummer to LegalNorm")
    print("     Reason: Filter by SGB without joining to Document")
    
    # 3. Check for missing indexes
    print("\n3️⃣  INDEX OPPORTUNITIES")
    print("-" * 70)
    
    opportunities.append({
        'type': 'Composite Index',
        'description': 'Create composite index on LegalNorm',
        'reason': 'Speed up common query pattern (SGB + paragraph number)',
        'impact': 'High - Most frequent query',
        'query': """
            CREATE INDEX idx_norm_sgb_para IF NOT EXISTS
            FOR (n:LegalNorm) ON (n.sgb_nummer, n.paragraph_nummer)
        """
    })
    print("  ✅ Composite index: LegalNorm(sgb_nummer, paragraph_nummer)")
    print("     Reason: Most queries filter by both SGB and paragraph")
    
    # 4. Relationship properties
    print("\n4️⃣  RELATIONSHIP PROPERTY OPTIMIZATIONS")
    print("-" * 70)
    
    opportunities.append({
        'type': 'Add Order Property',
        'description': 'Add order_index to relationships',
        'reason': 'Fast sorting without loading all nodes',
        'impact': 'Medium - Improves ordered queries',
        'query': """
            MATCH (struct:StructuralUnit)-[r:CONTAINS_NORM]->(norm:LegalNorm)
            SET r.order_index = norm.order_index
        """
    })
    print("  ✅ Add order_index to CONTAINS_NORM relationships")
    print("     Reason: Sort paragraphs without loading node properties")
    
    # 5. Bidirectional relationships
    print("\n5️⃣  BIDIRECTIONAL RELATIONSHIP OPPORTUNITIES")
    print("-" * 70)
    
    opportunities.append({
        'type': 'Add Reverse Relationships',
        'description': 'Create reverse lookup relationships',
        'reason': 'Fast "belongs to" queries',
        'impact': 'Low - Only for specific use cases',
        'query': """
            MATCH (norm:LegalNorm)-[r:HAS_CHUNK]->(chunk:Chunk)
            MERGE (chunk)-[:BELONGS_TO_NORM]->(norm)
        """
    })
    print("  ⚠️  Add BELONGS_TO_NORM reverse relationship")
    print("     Reason: Fast chunk -> norm lookup (optional)")
    
    return opportunities


def generate_optimization_report(schema_data, opportunities):
    """Generate comprehensive optimization report"""
    
    report = {
        'schema': {
            'total_nodes': sum(count for _, count in schema_data['nodes']),
            'total_relationships': sum(count for _, count in schema_data['relationships']),
            'node_types': len(schema_data['nodes']),
            'relationship_types': len(schema_data['relationships'])
        },
        'opportunities': opportunities,
        'priority_actions': []
    }
    
    # Prioritize high-impact optimizations
    high_impact = [o for o in opportunities if o.get('impact') == 'High']
    report['priority_actions'] = high_impact
    
    # Save to file
    output_file = Path(__file__).parent.parent / "logs" / "graph_optimization_report.json"
    output_file.parent.mkdir(exist_ok=True)
    
    with open(output_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    print("\n" + "="*70)
    print("📄 OPTIMIZATION REPORT GENERATED")
    print("="*70)
    print(f"\nSaved to: {output_file}")
    
    print("\n🎯 HIGH PRIORITY OPTIMIZATIONS:")
    for i, opp in enumerate(high_impact, 1):
        print(f"\n{i}. {opp['description']}")
        print(f"   Impact: {opp['impact']}")
        print(f"   Reason: {opp['reason']}")
    
    return report


def main():
    print("\n🔍 Graph Schema & Optimization Analysis")
    print("="*70)
    
    uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    username = os.getenv("NEO4J_USERNAME", "neo4j")
    password = os.getenv("NEO4J_PASSWORD")
    
    if not password:
        print("❌ NEO4J_PASSWORD not set in .env")
        return 1
    
    driver = GraphDatabase.driver(uri, auth=(username, password))
    
    try:
        # Check if APOC is available
        with driver.session() as session:
            try:
                session.run("RETURN apoc.version() as version")
                has_apoc = True
            except:
                has_apoc = False
                print("\n⚠️  APOC plugin not detected")
                print("Some analysis features will be limited\n")
        
        # Analyze current schema
        schema_data = analyze_schema(driver)
        
        # Analyze query performance
        analyze_query_performance(driver)
        
        # Identify opportunities
        opportunities = identify_optimization_opportunities(schema_data)
        
        # Generate report
        report = generate_optimization_report(schema_data, opportunities)
        
        print("\n✅ Analysis complete!")
        print("\nNext step: Run optimization script")
        print("  python scripts/optimize_graph_relations.py")
        
    finally:
        driver.close()
    
    return 0


if __name__ == "__main__":
    exit(main())
