#!/usr/bin/env python3
"""
Analyze Remaining Orphaned Chunks

Analysiert die verbleibenden 603 orphaned Norms mit 2,475 Chunks und
identifiziert Muster für weitere Reparatur-Strategien.

Usage:
    python scripts/analyze_remaining_orphans.py --output logs/orphan_analysis.json
"""

import os
import json
import argparse
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from neo4j import GraphDatabase
from collections import defaultdict

load_dotenv()


class OrphanAnalyzer:
    """Analysiert verbleibende orphaned Chunks."""
    
    def __init__(self):
        self.uri = os.getenv('NEO4J_URI')
        self.password = os.getenv('NEO4J_PASSWORD')
        self.driver = GraphDatabase.driver(self.uri, auth=('neo4j', self.password))
    
    def close(self):
        self.driver.close()
    
    def analyze(self) -> dict:
        """Führt Analyse durch."""
        results = {
            'timestamp': datetime.now().isoformat(),
            'total_orphans': 0,
            'total_orphan_chunks': 0,
            'patterns': {},
            'recommendations': []
        }
        
        with self.driver.session() as session:
            # 1. Count orphaned norms with chunks
            result = session.run('''
                MATCH (norm:LegalNorm)-[:HAS_CHUNK]->(c:Chunk)
                WHERE NOT EXISTS {
                    MATCH (doc:LegalDocument)-[:CONTAINS_NORM]->(norm)
                }
                RETURN count(DISTINCT norm) as orphan_norms, 
                       count(DISTINCT c) as orphan_chunks
            ''')
            r = result.single()
            results['total_orphans'] = r['orphan_norms']
            results['total_orphan_chunks'] = r['orphan_chunks']
            
            # 2. Analyze by norm_doknr patterns
            result = session.run('''
                MATCH (norm:LegalNorm)-[:HAS_CHUNK]->(c:Chunk)
                WHERE NOT EXISTS {
                    MATCH (doc:LegalDocument)-[:CONTAINS_NORM]->(norm)
                }
                WITH norm, count(c) as chunk_count
                WHERE norm.norm_doknr IS NOT NULL
                RETURN 
                    substring(norm.norm_doknr, 0, 13) as doknr_prefix,
                    count(DISTINCT norm) as norms,
                    sum(chunk_count) as chunks
                ORDER BY chunks DESC
                LIMIT 20
            ''')
            
            doknr_patterns = {}
            for r in result:
                prefix = r['doknr_prefix']
                doknr_patterns[prefix] = {
                    'norms': r['norms'],
                    'chunks': r['chunks']
                }
            results['patterns']['doknr'] = doknr_patterns
            
            # 3. Analyze norms without norm_doknr
            result = session.run('''
                MATCH (norm:LegalNorm)-[:HAS_CHUNK]->(c:Chunk)
                WHERE NOT EXISTS {
                    MATCH (doc:LegalDocument)-[:CONTAINS_NORM]->(norm)
                }
                AND (norm.norm_doknr IS NULL OR norm.norm_doknr = '')
                RETURN count(DISTINCT norm) as norms_without_doknr,
                       count(c) as chunks_without_doknr
            ''')
            r = result.single()
            results['norms_without_doknr'] = r['norms_without_doknr']
            results['chunks_without_doknr'] = r['chunks_without_doknr']
            
            # 4. Check if orphans are connected via StructuralUnit
            result = session.run('''
                MATCH (norm:LegalNorm)-[:HAS_CHUNK]->(c:Chunk)
                WHERE NOT EXISTS {
                    MATCH (doc:LegalDocument)-[:CONTAINS_NORM]->(norm)
                }
                OPTIONAL MATCH (struct:StructuralUnit)-[:CONTAINS_NORM]->(norm)
                OPTIONAL MATCH (doc:LegalDocument)-[:HAS_STRUCTURE]->(struct)
                WITH 
                    CASE WHEN doc IS NOT NULL THEN 'via_structure' ELSE 'no_path' END as status,
                    count(DISTINCT norm) as norms,
                    count(DISTINCT c) as chunks
                RETURN status, norms, chunks
            ''')
            
            connection_status = {}
            for r in result:
                connection_status[r['status']] = {
                    'norms': r['norms'],
                    'chunks': r['chunks']
                }
            results['connection_status'] = connection_status
            
            # 5. Sample orphaned norms for manual inspection
            result = session.run('''
                MATCH (norm:LegalNorm)-[:HAS_CHUNK]->(c:Chunk)
                WHERE NOT EXISTS {
                    MATCH (doc:LegalDocument)-[:CONTAINS_NORM]->(norm)
                }
                WITH norm, count(c) as chunks
                RETURN 
                    norm.norm_doknr as doknr,
                    norm.enbez as enbez,
                    norm.paragraph_nummer as para,
                    norm.titel as titel,
                    chunks
                ORDER BY chunks DESC
                LIMIT 20
            ''')
            
            samples = []
            for r in result:
                samples.append({
                    'doknr': r['doknr'],
                    'enbez': r['enbez'],
                    'paragraph': r['para'],
                    'titel': r['titel'],
                    'chunks': r['chunks']
                })
            results['sample_orphans'] = samples
            
            # 6. Generate recommendations
            results['recommendations'] = self._generate_recommendations(results)
        
        return results
    
    def _generate_recommendations(self, results: dict) -> list:
        """Generiert Empfehlungen basierend auf Analyseergebnissen."""
        recommendations = []
        
        # Recommendation 1: doknr patterns
        if results.get('patterns', {}).get('doknr'):
            top_pattern = max(
                results['patterns']['doknr'].items(),
                key=lambda x: x[1]['chunks'],
                default=(None, None)
            )
            if top_pattern[0]:
                recommendations.append({
                    'priority': 'HIGH',
                    'type': 'doknr_mapping',
                    'description': f"Largest doknr pattern: {top_pattern[0]} ({top_pattern[1]['chunks']} chunks)",
                    'action': f"Research which SGB/law corresponds to {top_pattern[0]} and create mapping"
                })
        
        # Recommendation 2: norms without doknr
        if results.get('norms_without_doknr', 0) > 0:
            recommendations.append({
                'priority': 'MEDIUM',
                'type': 'missing_doknr',
                'description': f"{results['norms_without_doknr']} norms without norm_doknr",
                'action': "Investigate if these norms can be linked via enbez/titel or should be marked as reference norms"
            })
        
        # Recommendation 3: structure-connected orphans
        via_structure = results.get('connection_status', {}).get('via_structure', {})
        if via_structure.get('norms', 0) > 0:
            recommendations.append({
                'priority': 'HIGH',
                'type': 'structure_linking',
                'description': f"{via_structure['norms']} orphans connected via StructuralUnit",
                'action': "Run fix_sgb_coverage.py to create direct CONTAINS_NORM links"
            })
        
        # Recommendation 4: truly orphaned (no path)
        no_path = results.get('connection_status', {}).get('no_path', {})
        if no_path.get('norms', 0) > 0:
            recommendations.append({
                'priority': 'LOW',
                'type': 'reference_norms',
                'description': f"{no_path['norms']} norms with no connection path",
                'action': "Mark as reference norms (external laws, historical versions) and create separate index"
            })
        
        return recommendations
    
    def print_report(self, results: dict):
        """Druckt formatierte Analyse."""
        print("=" * 80)
        print("ORPHANED CHUNKS ANALYSIS REPORT")
        print("=" * 80)
        print(f"\nGenerated: {results['timestamp']}")
        print(f"\n📊 SUMMARY")
        print(f"  Total orphaned norms: {results['total_orphans']:,}")
        print(f"  Total orphaned chunks: {results['total_orphan_chunks']:,}")
        print(f"  Norms without doknr: {results.get('norms_without_doknr', 0):,}")
        print(f"  Chunks without doknr: {results.get('chunks_without_doknr', 0):,}")
        
        print(f"\n🔍 CONNECTION STATUS")
        for status, data in results.get('connection_status', {}).items():
            print(f"  {status}: {data['norms']:,} norms, {data['chunks']:,} chunks")
        
        print(f"\n📋 TOP DOKNR PATTERNS")
        for i, (prefix, data) in enumerate(
            sorted(
                results.get('patterns', {}).get('doknr', {}).items(),
                key=lambda x: x[1]['chunks'],
                reverse=True
            )[:10], 1
        ):
            print(f"  {i}. {prefix}: {data['norms']:,} norms, {data['chunks']:,} chunks")
        
        print(f"\n📌 SAMPLE ORPHANED NORMS (Top 10)")
        for i, sample in enumerate(results.get('sample_orphans', [])[:10], 1):
            doknr = sample['doknr'][:30] if sample['doknr'] else 'N/A'
            print(f"  {i}. {doknr} | {sample['paragraph']} | {sample['chunks']} chunks")
        
        print(f"\n💡 RECOMMENDATIONS")
        for i, rec in enumerate(results.get('recommendations', []), 1):
            print(f"\n  {i}. [{rec['priority']}] {rec['type']}")
            print(f"     {rec['description']}")
            print(f"     → {rec['action']}")
        
        print("\n" + "=" * 80)


def main():
    parser = argparse.ArgumentParser(description='Analyze remaining orphaned chunks')
    parser.add_argument('--output', default='logs/orphan_analysis.json', 
                       help='Output JSON file path')
    parser.add_argument('--verbose', action='store_true', 
                       help='Print detailed report to console')
    
    args = parser.parse_args()
    
    analyzer = OrphanAnalyzer()
    
    try:
        print("🔍 Analyzing remaining orphaned chunks...")
        results = analyzer.analyze()
        
        # Print report if verbose
        if args.verbose or not args.output:
            analyzer.print_report(results)
        
        # Save to JSON
        if args.output:
            Path(args.output).parent.mkdir(parents=True, exist_ok=True)
            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            print(f"\n✅ Analysis saved to: {args.output}")
    
    finally:
        analyzer.close()


if __name__ == '__main__':
    main()
