#!/usr/bin/env python3
"""
Optimize Graph Relations and Structure
Apply identified optimizations to improve query performance
"""

import sys
import os
from pathlib import Path
import time

sys.path.append(str(Path(__file__).parent.parent))

from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()


class GraphOptimizer:
    def __init__(self, driver):
        self.driver = driver
        self.optimizations_applied = []
    
    def apply_optimization(self, name, query, description):
        """Apply an optimization and track it"""
        print(f"\n{len(self.optimizations_applied) + 1}. {name}")
        print("-" * 70)
        print(f"   {description}")
        
        start = time.time()
        
        try:
            with self.driver.session() as session:
                result = session.run(query)
                summary = result.consume()
                
                elapsed = time.time() - start
                
                # Get counters
                counters = summary.counters
                
                self.optimizations_applied.append({
                    'name': name,
                    'time_ms': elapsed * 1000,
                    'nodes_created': counters.nodes_created,
                    'relationships_created': counters.relationships_created,
                    'properties_set': counters.properties_set,
                    'indexes_added': counters.indexes_added
                })
                
                print(f"   ✅ Applied in {elapsed*1000:.2f}ms")
                if counters.relationships_created > 0:
                    print(f"   📊 Relationships created: {counters.relationships_created:,}")
                if counters.properties_set > 0:
                    print(f"   📊 Properties set: {counters.properties_set:,}")
                if counters.indexes_added > 0:
                    print(f"   📊 Indexes added: {counters.indexes_added}")
                
                return True
                
        except Exception as e:
            print(f"   ❌ Failed: {str(e)[:100]}")
            return False
    
    def optimize_1_direct_doc_to_norm(self):
        """Add direct LegalDocument -> LegalNorm relationship"""
        return self.apply_optimization(
            "Add Direct Document-to-Norm Relationship",
            """
            MATCH (doc:LegalDocument)-[:HAS_STRUCTURE]->(struct:StructuralUnit)
                  -[:CONTAINS_NORM]->(norm:LegalNorm)
            WHERE NOT (doc)-[:CONTAINS_NORM]->(norm)
            WITH doc, norm
            MERGE (doc)-[:CONTAINS_NORM]->(norm)
            """,
            "Create shortcut: Skip StructuralUnit for direct paragraph access"
        )
    
    def optimize_2_denormalize_sgb(self):
        """Copy sgb_nummer to LegalNorm nodes"""
        return self.apply_optimization(
            "Denormalize SGB Number to Norms",
            """
            MATCH (doc:LegalDocument)-[:HAS_STRUCTURE]->()
                  -[:CONTAINS_NORM]->(norm:LegalNorm)
            WHERE norm.sgb_nummer IS NULL
            SET norm.sgb_nummer = doc.sgb_nummer
            """,
            "Copy sgb_nummer: Filter by SGB without joining to Document"
        )
    
    def optimize_3_composite_index(self):
        """Create composite index on LegalNorm"""
        return self.apply_optimization(
            "Add Composite Index on LegalNorm",
            """
            CREATE INDEX idx_norm_sgb_para IF NOT EXISTS
            FOR (n:LegalNorm) ON (n.sgb_nummer, n.paragraph_nummer)
            """,
            "Fast lookup: Combined SGB + paragraph_nummer filter"
        )
    
    def optimize_4_paragraph_nummer_index(self):
        """Ensure paragraph_nummer index exists"""
        return self.apply_optimization(
            "Add Index on paragraph_nummer",
            """
            CREATE INDEX idx_norm_paragraph IF NOT EXISTS
            FOR (n:LegalNorm) ON (n.paragraph_nummer)
            """,
            "Fast lookup: Individual paragraph queries"
        )
    
    def optimize_5_document_direct_to_chunk(self):
        """Add direct LegalDocument -> Chunk relationship for faster access"""
        return self.apply_optimization(
            "Add Direct Document-to-Chunk Relationship",
            """
            MATCH (doc:LegalDocument)-[:CONTAINS_NORM]->(norm:LegalNorm)
                  -[:HAS_CHUNK]->(chunk:Chunk)
            WHERE NOT (doc)-[:HAS_CHUNK]->(chunk)
            WITH doc, chunk
            LIMIT 10000
            MERGE (doc)-[:HAS_CHUNK]->(chunk)
            """,
            "Fast chunk access: Direct document to chunks (batched)"
        )
    
    def optimize_6_add_document_to_chunk_batch(self):
        """Continue adding document-to-chunk relationships in batches"""
        query = """
        MATCH (doc:LegalDocument)-[:CONTAINS_NORM]->(norm:LegalNorm)
              -[:HAS_CHUNK]->(chunk:Chunk)
        WHERE NOT (doc)-[:HAS_CHUNK]->(chunk)
        WITH doc, chunk
        LIMIT 10000
        MERGE (doc)-[:HAS_CHUNK]->(chunk)
        RETURN count(*) as added
        """
        
        print(f"\n6. Continue Document-to-Chunk Relationships (Batched)")
        print("-" * 70)
        
        total_added = 0
        batch_num = 0
        
        with self.driver.session() as session:
            while True:
                result = session.run(query)
                count = result.single()['added']
                
                if count == 0:
                    break
                
                batch_num += 1
                total_added += count
                print(f"   Batch {batch_num}: +{count:,} relationships (total: {total_added:,})")
                
                if batch_num > 100:  # Safety limit
                    print("   ⚠️  Reached batch limit, stopping")
                    break
        
        if total_added > 0:
            print(f"   ✅ Total added: {total_added:,} relationships")
            return True
        else:
            print(f"   ✅ All relationships already exist")
            return True
    
    def optimize_7_add_relationship_properties(self):
        """Add order_index to relationships for fast sorting"""
        return self.apply_optimization(
            "Add Order Property to Relationships",
            """
            MATCH (struct:StructuralUnit)-[r:CONTAINS_NORM]->(norm:LegalNorm)
            WHERE r.order_index IS NULL AND norm.order_index IS NOT NULL
            SET r.order_index = norm.order_index
            """,
            "Fast sorting: Order relationships without loading node properties"
        )
    
    def optimize_8_fix_orphaned_norms(self):
        """Connect orphaned LegalNorms to their documents"""
        print(f"\n8. Fix Orphaned LegalNorms")
        print("-" * 70)
        
        with self.driver.session() as session:
            # Find orphaned norms
            result = session.run("""
                MATCH (norm:LegalNorm)
                WHERE NOT (norm)--()
                RETURN count(norm) as count
            """)
            orphaned_count = result.single()['count']
            
            if orphaned_count == 0:
                print("   ✅ No orphaned norms found")
                return True
            
            print(f"   Found {orphaned_count} orphaned norms")
            print("   ⚠️  These norms are not connected to any document")
            print("   ⚠️  Manual investigation recommended")
            
            return False
    
    def print_summary(self):
        """Print optimization summary"""
        print("\n" + "="*70)
        print("📊 OPTIMIZATION SUMMARY")
        print("="*70)
        
        successful = sum(1 for o in self.optimizations_applied if o.get('relationships_created', 0) > 0 or o.get('properties_set', 0) > 0 or o.get('indexes_added', 0) > 0)
        
        print(f"\nOptimizations Applied: {len(self.optimizations_applied)}")
        print(f"Successful: {successful}")
        
        total_time = sum(o['time_ms'] for o in self.optimizations_applied)
        print(f"Total Time: {total_time:.2f}ms")
        
        # Totals
        total_rels = sum(o.get('relationships_created', 0) for o in self.optimizations_applied)
        total_props = sum(o.get('properties_set', 0) for o in self.optimizations_applied)
        total_indexes = sum(o.get('indexes_added', 0) for o in self.optimizations_applied)
        
        print(f"\n📊 Total Changes:")
        print(f"   Relationships: {total_rels:,}")
        print(f"   Properties: {total_props:,}")
        print(f"   Indexes: {total_indexes}")


def main():
    print("\n⚡ Graph Optimization Suite")
    print("="*70)
    print("Applying identified optimizations to improve query performance")
    print("="*70)
    
    uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    username = os.getenv("NEO4J_USERNAME", "neo4j")
    password = os.getenv("NEO4J_PASSWORD")
    
    if not password:
        print("❌ NEO4J_PASSWORD not set in .env")
        return 1
    
    driver = GraphDatabase.driver(uri, auth=(username, password))
    
    try:
        optimizer = GraphOptimizer(driver)
        
        # Apply optimizations in order of impact
        print("\n🎯 HIGH IMPACT OPTIMIZATIONS")
        print("="*70)
        
        optimizer.optimize_1_direct_doc_to_norm()
        optimizer.optimize_2_denormalize_sgb()
        optimizer.optimize_3_composite_index()
        optimizer.optimize_4_paragraph_nummer_index()
        
        print("\n\n📈 MEDIUM IMPACT OPTIMIZATIONS")
        print("="*70)
        
        optimizer.optimize_5_document_direct_to_chunk()
        optimizer.optimize_6_add_document_to_chunk_batch()
        optimizer.optimize_7_add_relationship_properties()
        
        print("\n\n🔍 QUALITY CHECKS")
        print("="*70)
        
        optimizer.optimize_8_fix_orphaned_norms()
        
        # Print summary
        optimizer.print_summary()
        
        print("\n" + "="*70)
        print("✅ Optimization Complete!")
        print("="*70)
        print("\nNext steps:")
        print("1. Re-run efficiency tests: python scripts/test_graphrag_efficiency.py")
        print("2. Compare before/after metrics")
        print("3. Verify query performance improvements")
        
    finally:
        driver.close()
    
    return 0


if __name__ == "__main__":
    exit(main())
