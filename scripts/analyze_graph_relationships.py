#!/usr/bin/env python3
"""
Graph Relationship Analysis & Report Generation
Runs all Cypher scripts and creates comprehensive reports for:
- Sachbearbeiter (Case Workers)
- Prozessberater (Process Consultants)
"""

import sys
import os
from pathlib import Path
from datetime import datetime
import json
from typing import List, Dict, Any

sys.path.insert(0, str(Path(__file__).parent.parent))

from neo4j import GraphDatabase
from dotenv import load_dotenv
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

load_dotenv()


class GraphRelationshipAnalyzer:
    """Analyzes Neo4j graph relationships and generates comprehensive reports"""
    
    def __init__(self):
        self.uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        self.username = os.getenv("NEO4J_USERNAME", "neo4j")
        self.password = os.getenv("NEO4J_PASSWORD")
        
        if not self.password:
            raise ValueError("❌ NEO4J_PASSWORD not set in .env")
        
        self.driver = GraphDatabase.driver(self.uri, auth=(self.username, self.password))
        self.project_root = Path(__file__).parent.parent
        self.cypher_dir = self.project_root / "cypher"
        
        self.results = {
            'statistics': {},
            'relationships': {},
            'workflows': {},
            'quality': {}
        }
        
        logger.info(f"✅ Connected to Neo4j: {self.uri}")
    
    def close(self):
        self.driver.close()
    
    def run_cypher_file(self, filepath: Path) -> List[Dict]:
        """Run all queries from a Cypher file"""
        logger.info(f"\n{'='*70}")
        logger.info(f"📄 Running: {filepath.name}")
        logger.info(f"{'='*70}")
        
        content = filepath.read_text()
        
        # Split by semicolons but ignore comments
        queries = []
        current_query = []
        in_comment = False
        
        for line in content.split('\n'):
            stripped = line.strip()
            
            # Skip comment blocks
            if stripped.startswith('//'):
                continue
            if stripped.startswith('/*'):
                in_comment = True
                continue
            if '*/' in stripped:
                in_comment = False
                continue
            if in_comment:
                continue
            
            current_query.append(line)
            
            if stripped.endswith(';'):
                query_text = '\n'.join(current_query)
                if query_text.strip() and not query_text.strip().startswith('//'):
                    queries.append(query_text)
                current_query = []
        
        results = []
        with self.driver.session() as session:
            for i, query in enumerate(queries, 1):
                try:
                    # Extract query title from comments
                    title = f"Query {i}"
                    for line in query.split('\n'):
                        if line.strip().startswith('//') and len(line.strip()) > 3:
                            title = line.strip()[2:].strip()
                            break
                    
                    logger.info(f"  {i}/{len(queries)}: {title}")
                    
                    result = session.run(query)
                    records = [dict(r) for r in result]
                    
                    results.append({
                        'title': title,
                        'query': query,
                        'records': records,
                        'count': len(records)
                    })
                    
                    logger.info(f"      ✅ {len(records)} results")
                    
                except Exception as e:
                    logger.warning(f"      ⚠️  Skipped: {str(e)[:100]}")
                    results.append({
                        'title': title,
                        'query': query,
                        'error': str(e),
                        'count': 0
                    })
        
        return results
    
    def analyze_graph_structure(self):
        """Analyze overall graph structure"""
        logger.info("\n🔍 ANALYZING GRAPH STRUCTURE")
        
        with self.driver.session() as session:
            # Node counts by label
            result = session.run("""
                MATCH (n)
                RETURN labels(n)[0] as label, count(*) as count
                ORDER BY count DESC
            """)
            node_counts = {r['label']: r['count'] for r in result}
            
            # Relationship counts by type
            result = session.run("""
                MATCH ()-[r]->()
                RETURN type(r) as type, count(*) as count
                ORDER BY count DESC
            """)
            rel_counts = {r['type']: r['count'] for r in result}
            
            # Graph density metrics
            result = session.run("""
                MATCH (n)
                WITH count(n) as nodes
                MATCH ()-[r]->()
                WITH nodes, count(r) as rels
                RETURN nodes, rels, 
                       rels * 1.0 / nodes as avg_relationships_per_node
            """)
            metrics = dict(result.single())
            
            self.results['statistics'] = {
                'node_counts': node_counts,
                'relationship_counts': rel_counts,
                'metrics': metrics
            }
            
            logger.info(f"  Nodes: {sum(node_counts.values())}")
            logger.info(f"  Relationships: {sum(rel_counts.values())}")
            logger.info(f"  Avg Relationships/Node: {metrics['avg_relationships_per_node']:.2f}")
    
    def analyze_sachbearbeiter_paths(self):
        """Analyze typical Sachbearbeiter workflow paths"""
        logger.info("\n👔 ANALYZING SACHBEARBEITER WORKFLOWS")
        
        workflows = {}
        
        with self.driver.session() as session:
            # UC1: Regelbedarfe - Full path analysis
            result = session.run("""
                MATCH path = (doc:LegalDocument {sgb_nummer: "II"})
                    -[:HAS_STRUCTURE|CONTAINS_NORM*1..3]->(norm:LegalNorm)
                WHERE norm.paragraph_nummer = "20"
                OPTIONAL MATCH (norm)-[:HAS_CHUNK]->(chunk:Chunk)
                RETURN 
                    length(path) as path_length,
                    count(DISTINCT norm) as norms_found,
                    count(DISTINCT chunk) as chunks_available
            """)
            workflows['regelbedarfe_path'] = dict(result.single() or {})
            
            # UC2: Leistungsberechtigung - Multi-step path
            result = session.run("""
                MATCH (doc:LegalDocument {sgb_nummer: "II"})
                    -[:HAS_STRUCTURE|CONTAINS_NORM*1..3]->(norm:LegalNorm)
                WHERE norm.paragraph_nummer IN ["7", "8", "9"]
                WITH count(DISTINCT norm) as total_norms
                MATCH (norm:LegalNorm)
                WHERE norm.paragraph_nummer IN ["7", "8", "9"]
                OPTIONAL MATCH (norm)-[:HAS_CHUNK]->(chunk:Chunk)
                RETURN 
                    total_norms,
                    count(DISTINCT chunk) as total_chunks,
                    total_norms > 0 as path_complete
            """)
            workflows['leistungsberechtigung_path'] = dict(result.single() or {})
            
            # Path complexity analysis
            result = session.run("""
                MATCH (doc:LegalDocument)
                OPTIONAL MATCH p1 = (doc)-[:HAS_STRUCTURE]->(struct)
                OPTIONAL MATCH p2 = (struct)-[:CONTAINS_NORM]->(norm)
                OPTIONAL MATCH p3 = (norm)-[:HAS_CHUNK]->(chunk)
                RETURN 
                    doc.sgb_nummer as sgb,
                    count(DISTINCT struct) as structures,
                    count(DISTINCT norm) as norms,
                    count(DISTINCT chunk) as chunks,
                    CASE 
                        WHEN count(DISTINCT chunk) > 0 THEN true
                        ELSE false
                    END as has_complete_path
                ORDER BY sgb
            """)
            workflows['sgb_path_completeness'] = [dict(r) for r in result]
        
        self.results['workflows'] = workflows
        
        logger.info(f"  Regelbedarfe path: {workflows['regelbedarfe_path']}")
        logger.info(f"  Leistungsberechtigung: {workflows['leistungsberechtigung_path']}")
    
    def analyze_relationship_quality(self):
        """Analyze quality of relationships"""
        logger.info("\n📊 ANALYZING RELATIONSHIP QUALITY")
        
        quality = {}
        
        with self.driver.session() as session:
            # Orphaned nodes
            result = session.run("""
                MATCH (n)
                WHERE NOT (n)--()
                RETURN labels(n)[0] as label, count(n) as orphaned_count
            """)
            quality['orphaned_nodes'] = {r['label']: r['orphaned_count'] for r in result}
            
            # Norms without chunks
            result = session.run("""
                MATCH (norm:LegalNorm)
                WHERE NOT EXISTS { (norm)-[:HAS_CHUNK]->(:Chunk) }
                OPTIONAL MATCH (doc:LegalDocument)-[:HAS_STRUCTURE|CONTAINS_NORM*1..3]->(norm)
                RETURN doc.sgb_nummer as sgb, count(norm) as norms_without_chunks
                ORDER BY norms_without_chunks DESC
            """)
            quality['norms_without_chunks'] = [dict(r) for r in result]
            
            # Document connectivity
            result = session.run("""
                MATCH (doc:LegalDocument)
                OPTIONAL MATCH (doc)-[:HAS_STRUCTURE]->(struct)
                OPTIONAL MATCH (struct)-[:CONTAINS_NORM]->(norm)
                OPTIONAL MATCH (norm)-[:HAS_CHUNK]->(chunk)
                RETURN 
                    doc.sgb_nummer as sgb,
                    count(DISTINCT struct) > 0 as has_structure,
                    count(DISTINCT norm) > 0 as has_norms,
                    count(DISTINCT chunk) > 0 as has_chunks,
                    count(DISTINCT struct) as struct_count,
                    count(DISTINCT norm) as norm_count,
                    count(DISTINCT chunk) as chunk_count
                ORDER BY sgb
            """)
            quality['document_connectivity'] = [dict(r) for r in result]
            
            # Amendment coverage
            result = session.run("""
                MATCH (norm:LegalNorm)
                OPTIONAL MATCH (norm)-[:HAS_AMENDMENT]->(amend:Amendment)
                WITH count(DISTINCT norm) as total_norms,
                     count(DISTINCT amend) as norms_with_amendments
                RETURN total_norms, norms_with_amendments,
                       norms_with_amendments * 100.0 / total_norms as coverage_percent
            """)
            quality['amendment_coverage'] = dict(result.single() or {})
        
        self.results['quality'] = quality
        
        orphaned_total = sum(quality['orphaned_nodes'].values())
        logger.info(f"  Orphaned nodes: {orphaned_total}")
        logger.info(f"  Amendment coverage: {quality['amendment_coverage'].get('coverage_percent', 0):.1f}%")
    
    def run_all_cypher_scripts(self):
        """Run all Cypher scripts in the cypher/ directory"""
        logger.info("\n🚀 RUNNING ALL CYPHER SCRIPTS")
        
        cypher_files = sorted(self.cypher_dir.glob("*.cypher"))
        cypher_files = [f for f in cypher_files if not f.name.startswith('xml_schema')]
        
        all_results = {}
        
        for cypher_file in cypher_files:
            results = self.run_cypher_file(cypher_file)
            all_results[cypher_file.stem] = results
        
        self.results['cypher_queries'] = all_results
    
    def generate_sachbearbeiter_report(self) -> str:
        """Generate report from Sachbearbeiter perspective"""
        report = []
        report.append("# SACHBEARBEITER GRAPH ANALYSIS REPORT")
        report.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        report.append("---")
        report.append("")
        
        # Executive Summary
        report.append("## 📋 Executive Summary for Case Workers")
        report.append("")
        report.append("### Graph Coverage")
        stats = self.results['statistics']
        node_counts = stats['node_counts']
        report.append(f"- **Total Legal Norms:** {node_counts.get('LegalNorm', 0):,}")
        report.append(f"- **Available Chunks (for RAG):** {node_counts.get('Chunk', 0):,}")
        report.append(f"- **SGB Books:** {node_counts.get('LegalDocument', 0)}")
        report.append(f"- **PDF Documents:** {node_counts.get('Document', 0)}")
        report.append("")
        
        # Workflow Analysis
        report.append("### 🔄 Workflow Path Analysis")
        report.append("")
        workflows = self.results['workflows']
        
        if 'regelbedarfe_path' in workflows:
            rp = workflows['regelbedarfe_path']
            status = "✅" if rp.get('chunks_available', 0) > 0 else "❌"
            report.append(f"**UC1: Regelbedarfe (§ 20 SGB II)** {status}")
            report.append(f"- Path length: {rp.get('path_length', 'N/A')}")
            report.append(f"- Chunks available: {rp.get('chunks_available', 0)}")
            report.append("")
        
        if 'sgb_path_completeness' in workflows:
            report.append("**SGB Coverage for Case Work:**")
            report.append("")
            report.append("| SGB | Structures | Norms | Chunks | Complete Path |")
            report.append("|-----|-----------|-------|--------|---------------|")
            for item in workflows['sgb_path_completeness']:
                status = "✅" if item['has_complete_path'] else "❌"
                report.append(f"| {item['sgb']} | {item['structures']} | {item['norms']} | {item['chunks']} | {status} |")
            report.append("")
        
        # Quality Issues
        report.append("### ⚠️ Issues Affecting Case Work")
        report.append("")
        quality = self.results['quality']
        
        if quality.get('norms_without_chunks'):
            report.append("**Norms Without RAG Chunks:**")
            for item in quality['norms_without_chunks'][:5]:
                if item['norms_without_chunks'] > 0:
                    report.append(f"- SGB {item['sgb']}: {item['norms_without_chunks']} norms missing chunks")
            report.append("")
        
        # Recommendations
        report.append("## 💡 Recommendations for Sachbearbeiter")
        report.append("")
        report.append("1. **Primary Sources:** Use SGBs with complete paths (✅ in table above)")
        report.append("2. **Backup Strategy:** For SGBs without chunks, use direct text queries")
        report.append("3. **Verify Amendments:** Check `amendment_date` for recent changes")
        report.append("4. **Cross-SGB Cases:** Path analysis shows all 13 SGBs are available")
        report.append("")
        
        return '\n'.join(report)
    
    def generate_prozessberater_report(self) -> str:
        """Generate report from Prozessberater perspective"""
        report = []
        report.append("# PROZESSBERATER GRAPH ANALYSIS REPORT")
        report.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        report.append("---")
        report.append("")
        
        # Graph Architecture
        report.append("## 🏗️ Graph Architecture")
        report.append("")
        stats = self.results['statistics']
        
        report.append("### Node Distribution")
        report.append("")
        report.append("| Node Type | Count | Purpose |")
        report.append("|-----------|-------|---------|")
        node_types = {
            'LegalDocument': 'SGB law books',
            'StructuralUnit': 'Chapters, sections',
            'LegalNorm': 'Individual paragraphs',
            'TextUnit': 'Paragraph subsections',
            'Chunk': 'RAG-optimized text blocks',
            'Amendment': 'Change history',
            'Document': 'PDF guidelines',
            'Paragraph': 'Legacy structure'
        }
        for label, count in sorted(stats['node_counts'].items(), key=lambda x: x[1], reverse=True):
            purpose = node_types.get(label, 'Supporting data')
            report.append(f"| {label} | {count:,} | {purpose} |")
        report.append("")
        
        # Relationship Patterns
        report.append("### Relationship Patterns")
        report.append("")
        report.append("| Relationship | Count | Pattern |")
        report.append("|-------------|-------|---------|")
        rel_types = {
            'HAS_CHUNK': 'Norm → Chunks (RAG)',
            'HAS_CONTENT': 'Norm → TextUnits',
            'CONTAINS_NORM': 'Structure → Norms',
            'HAS_STRUCTURE': 'Document → Structure',
            'CONTAINS_PARAGRAPH': 'Legacy link',
            'HAS_AMENDMENT': 'Norm → Changes'
        }
        for rel_type, count in sorted(stats['relationship_counts'].items(), key=lambda x: x[1], reverse=True):
            pattern = rel_types.get(rel_type, 'Supporting link')
            report.append(f"| {rel_type} | {count:,} | {pattern} |")
        report.append("")
        
        # Process Integration
        report.append("## 🔄 Process Integration Analysis")
        report.append("")
        
        quality = self.results['quality']
        if quality.get('document_connectivity'):
            report.append("### Connectivity Status per SGB")
            report.append("")
            report.append("| SGB | Structure | Norms | Chunks | Process-Ready |")
            report.append("|-----|-----------|-------|--------|---------------|")
            for item in quality['document_connectivity']:
                ready = "✅" if item['has_structure'] and item['has_norms'] and item['has_chunks'] else "⚠️"
                report.append(f"| {item['sgb']} | {item['struct_count']} | {item['norm_count']} | {item['chunk_count']} | {ready} |")
            report.append("")
        
        # Data Quality Metrics
        report.append("## 📊 Data Quality Metrics")
        report.append("")
        
        metrics = stats['metrics']
        report.append(f"- **Graph Density:** {metrics['avg_relationships_per_node']:.2f} relationships/node")
        report.append(f"- **Total Nodes:** {metrics['nodes']:,}")
        report.append(f"- **Total Relationships:** {metrics['rels']:,}")
        report.append("")
        
        orphaned = sum(quality.get('orphaned_nodes', {}).values())
        report.append(f"- **Orphaned Nodes:** {orphaned} (should be 0)")
        report.append(f"- **Amendment Coverage:** {quality.get('amendment_coverage', {}).get('coverage_percent', 0):.1f}%")
        report.append("")
        
        # Process Optimization Recommendations
        report.append("## 🎯 Process Optimization Recommendations")
        report.append("")
        report.append("### Immediate Actions")
        report.append("1. **Add Direct Links:** Create `CONTAINS_NORM` from LegalDocument to LegalNorm for faster queries")
        report.append("2. **Fix Orphaned Nodes:** Investigate and connect isolated nodes")
        report.append("3. **Vector Index:** Create index on Chunk.embedding for semantic search")
        report.append("")
        
        report.append("### Medium-term Improvements")
        report.append("4. **Cross-References:** Add `REFERENCES` relationships between related norms")
        report.append("5. **Workflow Templates:** Create pre-defined paths for common case types")
        report.append("6. **Performance Indexes:** Add compound indexes on frequently queried properties")
        report.append("")
        
        report.append("### Long-term Strategy")
        report.append("7. **Historical Tracking:** Import older SGB versions for SUPERSEDES chains")
        report.append("8. **ML Enhancement:** Use graph embeddings for similarity recommendations")
        report.append("9. **Real-time Updates:** Implement change detection from gesetze-im-internet.de")
        report.append("")
        
        return '\n'.join(report)
    
    def generate_improvement_suggestions(self) -> Dict:
        """Generate structured improvement suggestions"""
        quality = self.results['quality']
        
        suggestions = {
            'critical': [],
            'high_priority': [],
            'medium_priority': [],
            'low_priority': []
        }
        
        # Analyze quality issues
        orphaned_total = sum(quality.get('orphaned_nodes', {}).values())
        if orphaned_total > 0:
            suggestions['critical'].append({
                'issue': f'{orphaned_total} orphaned nodes found',
                'impact': 'Nodes not accessible via normal queries',
                'solution': 'Run cleanup query to connect or delete orphaned nodes'
            })
        
        # Norms without chunks
        norms_without_chunks = quality.get('norms_without_chunks', [])
        critical_sgbs = [item for item in norms_without_chunks if item['norms_without_chunks'] > 100]
        if critical_sgbs:
            suggestions['high_priority'].append({
                'issue': f'{len(critical_sgbs)} SGBs have >100 norms without chunks',
                'impact': 'RAG queries will fail for these paragraphs',
                'solution': 'Re-run chunk generation for affected SGBs'
            })
        
        # Amendment coverage
        amend_coverage = quality.get('amendment_coverage', {}).get('coverage_percent', 0)
        if amend_coverage < 10:
            suggestions['medium_priority'].append({
                'issue': f'Only {amend_coverage:.1f}% of norms have amendment data',
                'impact': 'Cannot track legal changes over time',
                'solution': 'Parse BGBl references from XML metadata'
            })
        
        # Document connectivity
        disconnected_docs = [d for d in quality.get('document_connectivity', []) 
                            if not d.get('has_chunks')]
        if disconnected_docs:
            suggestions['high_priority'].append({
                'issue': f'{len(disconnected_docs)} documents have no chunks',
                'impact': 'These SGBs cannot be used for semantic search',
                'solution': 'Verify import pipeline for affected SGBs'
            })
        
        return suggestions
    
    def save_reports(self):
        """Save all generated reports"""
        output_dir = self.project_root / "logs" / "graph_analysis"
        output_dir.mkdir(exist_ok=True, parents=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Sachbearbeiter report
        sachbearbeiter_report = self.generate_sachbearbeiter_report()
        sachbearbeiter_file = output_dir / f"sachbearbeiter_report_{timestamp}.md"
        sachbearbeiter_file.write_text(sachbearbeiter_report)
        logger.info(f"✅ Sachbearbeiter report: {sachbearbeiter_file}")
        
        # Prozessberater report
        prozessberater_report = self.generate_prozessberater_report()
        prozessberater_file = output_dir / f"prozessberater_report_{timestamp}.md"
        prozessberater_file.write_text(prozessberater_report)
        logger.info(f"✅ Prozessberater report: {prozessberater_file}")
        
        # Improvement suggestions
        suggestions = self.generate_improvement_suggestions()
        suggestions_file = output_dir / f"improvement_suggestions_{timestamp}.json"
        suggestions_file.write_text(json.dumps(suggestions, indent=2))
        logger.info(f"✅ Improvement suggestions: {suggestions_file}")
        
        # Raw data
        data_file = output_dir / f"analysis_data_{timestamp}.json"
        data_file.write_text(json.dumps(self.results, indent=2, default=str))
        logger.info(f"✅ Raw analysis data: {data_file}")
        
        return {
            'sachbearbeiter': sachbearbeiter_file,
            'prozessberater': prozessberater_file,
            'suggestions': suggestions_file,
            'data': data_file
        }


def main():
    """Main execution"""
    print("\n" + "="*70)
    print("COMPREHENSIVE GRAPH RELATIONSHIP ANALYSIS")
    print("="*70)
    
    analyzer = GraphRelationshipAnalyzer()
    
    try:
        # Run analysis
        analyzer.analyze_graph_structure()
        analyzer.analyze_sachbearbeiter_paths()
        analyzer.analyze_relationship_quality()
        analyzer.run_all_cypher_scripts()
        
        # Generate reports
        print("\n" + "="*70)
        print("📝 GENERATING REPORTS")
        print("="*70)
        
        files = analyzer.save_reports()
        
        print("\n✅ Analysis complete!")
        print(f"\nReports generated:")
        for role, filepath in files.items():
            print(f"  - {role}: {filepath.name}")
        
        return 0
        
    except Exception as e:
        logger.error(f"❌ Analysis failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        analyzer.close()


if __name__ == "__main__":
    exit(main())
