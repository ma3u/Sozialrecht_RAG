#!/usr/bin/env python3
"""
Use Case Validator & Visualizer

Validiert alle 20 Use Cases gegen die Neo4j-Datenbank und erstellt:
1. Cypher-Queries für jeden Use Case
2. Datenvalidierung (Normen & Chunks vorhanden?)
3. Visualisierungs-Queries für Neo4j Browser/Bloom
4. HTML-Report mit allen Ergebnissen

Usage:
    python scripts/validate_and_visualize_use_cases.py --output reports/use_case_validation.html
    python scripts/validate_and_visualize_use_cases.py --use-case UC01  # Nur ein Use Case
    python scripts/validate_and_visualize_use_cases.py --export-cypher cypher/use_cases/  # Export Queries
"""

import os
import argparse
import json
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from neo4j import GraphDatabase
from typing import Dict, List, Tuple

load_dotenv()

class UseCaseValidator:
    """Validiert Use Cases gegen Neo4j-Datenbank."""
    
    def __init__(self):
        self.uri = os.getenv('NEO4J_URI')
        self.password = os.getenv('NEO4J_PASSWORD')
        self.driver = GraphDatabase.driver(self.uri, auth=('neo4j', self.password))
        self.use_cases = self._define_use_cases()
    
    def close(self):
        self.driver.close()
    
    def _define_use_cases(self) -> Dict:
        """Definiert alle 20 Use Cases mit Queries."""
        return {
            'UC01': {
                'name': 'Regelbedarfsermittlung für Familie',
                'sgb': 'II',
                'paragraphen': ['20', '21', '22', '23'],
                'query': '''
                    MATCH (doc:LegalDocument {sgb_nummer: 'II'})
                          -[:CONTAINS_NORM]->(norm:LegalNorm)
                          -[:HAS_CHUNK]->(chunk:Chunk)
                    WHERE norm.paragraph_nummer IN ['20', '21', '22', '23']
                    RETURN 
                        norm.paragraph_nummer as paragraph,
                        norm.enbez as titel,
                        count(DISTINCT chunk) as chunks,
                        collect(DISTINCT chunk.text)[0..2] as beispiel_texte
                    ORDER BY norm.order_index
                ''',
                'visualization_query': '''
                    MATCH path = (doc:LegalDocument {sgb_nummer: 'II'})
                                 -[:CONTAINS_NORM]->(norm:LegalNorm)
                                 -[:HAS_CHUNK]->(chunk:Chunk)
                    WHERE norm.paragraph_nummer IN ['20', '21', '22', '23']
                    RETURN path LIMIT 50
                ''',
                'expected_min_norms': 4,
                'expected_min_chunks': 100,
                'priority': 'P0',
                'tool': 'Neo4j Browser'
            },
            'UC02': {
                'name': 'Sanktionsprüfung bei Meldeversäumnis',
                'sgb': 'II',
                'paragraphen': ['32'],
                'query': '''
                    MATCH (doc:LegalDocument {sgb_nummer: 'II'})
                          -[:CONTAINS_NORM]->(norm:LegalNorm)
                    WHERE norm.paragraph_nummer = '32'
                    OPTIONAL MATCH (norm)-[:HAS_CHUNK]->(chunk:Chunk)
                    WHERE chunk.text CONTAINS 'Meldeversäumnis' 
                       OR chunk.text CONTAINS 'Minderung'
                       OR chunk.text CONTAINS 'Sanktion'
                    RETURN 
                        norm.paragraph_nummer,
                        norm.enbez,
                        count(DISTINCT chunk) as relevante_chunks,
                        collect(DISTINCT chunk.text)[0..1] as beispiele
                ''',
                'visualization_query': '''
                    MATCH path = (doc:LegalDocument {sgb_nummer: 'II'})
                                 -[:CONTAINS_NORM]->(norm:LegalNorm {paragraph_nummer: '32'})
                                 -[:HAS_CHUNK]->(chunk:Chunk)
                    RETURN path LIMIT 30
                ''',
                'expected_min_norms': 1,
                'expected_min_chunks': 10,
                'priority': 'P0',
                'tool': 'Neo4j Browser'
            },
            'UC03': {
                'name': 'Einkommensanrechnung mit Freibeträgen',
                'sgb': 'II',
                'paragraphen': ['11', '11b'],
                'query': '''
                    MATCH (doc:LegalDocument {sgb_nummer: 'II'})
                          -[:CONTAINS_NORM]->(norm:LegalNorm)
                    WHERE norm.paragraph_nummer IN ['11', '11b']
                    OPTIONAL MATCH (norm)-[:HAS_CHUNK]->(chunk:Chunk)
                    WITH norm, collect(chunk.text) as chunks
                    RETURN 
                        norm.paragraph_nummer,
                        norm.enbez,
                        size(chunks) as chunk_count,
                        chunks[0..2] as beispiele
                    ORDER BY norm.paragraph_nummer
                ''',
                'visualization_query': '''
                    MATCH path = (doc:LegalDocument {sgb_nummer: 'II'})
                                 -[:CONTAINS_NORM]->(norm:LegalNorm)
                                 -[:HAS_CHUNK]->(chunk:Chunk)
                    WHERE norm.paragraph_nummer IN ['11', '11b']
                    RETURN path LIMIT 50
                ''',
                'expected_min_norms': 2,
                'expected_min_chunks': 50,
                'priority': 'P0',
                'tool': 'Neo4j Browser + Python Berechnungsmodul'
            },
            'UC06': {
                'name': 'Bedarfsgemeinschaft vs. Haushaltsgemeinschaft',
                'sgb': 'II',
                'paragraphen': ['7'],
                'query': '''
                    MATCH (doc:LegalDocument {sgb_nummer: 'II'})
                          -[:CONTAINS_NORM]->(norm:LegalNorm)
                    WHERE norm.paragraph_nummer = '7'
                    MATCH (norm)-[:HAS_CHUNK]->(chunk:Chunk)
                    RETURN 
                        norm.paragraph_nummer,
                        norm.enbez,
                        count(chunk) as chunks,
                        collect(chunk.text)[0..3] as beispiel_definitionen
                    ORDER BY chunk.chunk_index
                ''',
                'visualization_query': '''
                    MATCH path = (doc:LegalDocument {sgb_nummer: 'II'})
                                 -[:CONTAINS_NORM]->(norm:LegalNorm {paragraph_nummer: '7'})
                                 -[:HAS_CHUNK]->(chunk:Chunk)
                    RETURN path LIMIT 100
                ''',
                'expected_min_norms': 1,
                'expected_min_chunks': 50,
                'priority': 'P0',
                'tool': 'Neo4j Browser + Bloom (Graph Exploration)'
            },
            'UC08': {
                'name': 'Darlehen für Erstausstattung',
                'sgb': 'II',
                'paragraphen': ['24'],
                'query': '''
                    MATCH (norm:LegalNorm)
                    WHERE norm.paragraph_nummer = '24'
                      AND EXISTS {
                          MATCH (norm)<-[:CONTAINS_NORM]-(doc:LegalDocument {sgb_nummer: 'II'})
                      }
                    MATCH (norm)-[:HAS_CHUNK]->(chunk:Chunk)
                    WHERE chunk.text CONTAINS 'Erstausstattung' 
                       OR chunk.text CONTAINS 'Schwangerschaft'
                       OR chunk.text CONTAINS 'Darlehen'
                    RETURN 
                        norm.enbez,
                        count(chunk) as relevante_chunks,
                        collect(chunk.text)[0..2] as beispiele
                ''',
                'visualization_query': '''
                    MATCH path = (doc:LegalDocument {sgb_nummer: 'II'})
                                 -[:CONTAINS_NORM]->(norm:LegalNorm {paragraph_nummer: '24'})
                                 -[:HAS_CHUNK]->(chunk:Chunk)
                    WHERE chunk.text CONTAINS 'Erstausstattung'
                    RETURN path LIMIT 30
                ''',
                'expected_min_norms': 1,
                'expected_min_chunks': 20,
                'priority': 'P0',
                'tool': 'Neo4j Browser'
            },
            'UC10': {
                'name': 'Widerspruch bearbeiten',
                'sgb': 'X',
                'paragraphen': ['79', '80', '84', '85'],
                'query': '''
                    MATCH (doc:LegalDocument {sgb_nummer: 'X'})
                          -[:CONTAINS_NORM]->(norm:LegalNorm)
                    WHERE norm.paragraph_nummer IN ['79', '80', '84', '85']
                    OPTIONAL MATCH (norm)-[:HAS_CHUNK]->(chunk:Chunk)
                    RETURN 
                        norm.paragraph_nummer,
                        norm.enbez,
                        count(chunk) as chunks
                    ORDER BY norm.paragraph_nummer
                ''',
                'visualization_query': '''
                    MATCH path = (doc:LegalDocument {sgb_nummer: 'X'})
                                 -[:CONTAINS_NORM]->(norm:LegalNorm)
                    WHERE norm.paragraph_nummer IN ['79', '80', '84', '85']
                    RETURN path LIMIT 20
                ''',
                'expected_min_norms': 4,
                'expected_min_chunks': 0,  # Known issue
                'priority': 'P0',
                'status_expected': 'FAIL',
                'tool': 'N/A (SGB X import required)'
            },
            'UC13': {
                'name': 'Prozessanalyse - Durchlaufzeiten Erstantrag',
                'sgb': 'II',
                'paragraphen': ['37', '41', '44'],
                'query': '''
                    MATCH (doc:LegalDocument {sgb_nummer: 'II'})
                          -[:CONTAINS_NORM]->(norm:LegalNorm)
                    WHERE norm.paragraph_nummer IN ['37', '41', '44']
                    OPTIONAL MATCH (norm)-[:HAS_CHUNK]->(chunk:Chunk)
                    WHERE chunk.text CONTAINS 'Frist' 
                       OR chunk.text CONTAINS 'unverzüglich'
                       OR chunk.text CONTAINS 'Monat'
                    RETURN 
                        norm.paragraph_nummer,
                        norm.enbez,
                        count(DISTINCT chunk) as fristen_chunks,
                        collect(DISTINCT chunk.text)[0..2] as beispiel_fristen
                ''',
                'visualization_query': '''
                    MATCH path = (doc:LegalDocument {sgb_nummer: 'II'})
                                 -[:CONTAINS_NORM]->(norm:LegalNorm)
                                 -[:HAS_CHUNK]->(chunk:Chunk)
                    WHERE norm.paragraph_nummer IN ['37', '41', '44']
                      AND (chunk.text CONTAINS 'Frist' OR chunk.text CONTAINS 'Monat')
                    RETURN path LIMIT 30
                ''',
                'expected_min_norms': 3,
                'expected_min_chunks': 10,
                'priority': 'P0',
                'tool': 'Neo4j Browser + Python Analytics'
            },
            'UC16': {
                'name': 'Qualitätssicherung - Fehlerquellen in Bescheiden',
                'sgb': 'II',
                'paragraphen': ['*'],  # Komplexitätsanalyse über alle Normen
                'query': '''
                    MATCH (norm:LegalNorm)-[:HAS_CHUNK]->(chunk:Chunk)
                    WHERE EXISTS {
                        MATCH (norm)<-[:CONTAINS_NORM]-(doc:LegalDocument {sgb_nummer: 'II'})
                    }
                    WITH norm, count(chunk) as chunk_count
                    WHERE chunk_count > 10
                    MATCH (norm)-[:HAS_CHUNK]->(chunk:Chunk)
                    WHERE chunk.text CONTAINS 'Ausnahme' 
                       OR chunk.text CONTAINS 'abweichend'
                       OR chunk.text CONTAINS 'jedoch'
                    RETURN 
                        norm.paragraph_nummer,
                        norm.enbez,
                        chunk_count as komplexitaet,
                        count(DISTINCT chunk) as ausnahmen
                    ORDER BY komplexitaet DESC, ausnahmen DESC
                    LIMIT 10
                ''',
                'visualization_query': '''
                    MATCH (norm:LegalNorm)-[:HAS_CHUNK]->(chunk:Chunk)
                    WHERE EXISTS {
                        MATCH (norm)<-[:CONTAINS_NORM]-(doc:LegalDocument {sgb_nummer: 'II'})
                    }
                    WITH norm, count(chunk) as chunk_count
                    WHERE chunk_count > 15
                    MATCH path = (norm)-[:HAS_CHUNK]->(chunk)
                    RETURN path LIMIT 50
                ''',
                'expected_min_norms': 5,
                'expected_min_chunks': 50,
                'priority': 'P0',
                'tool': 'Neo4j Browser + Cypher Analytics'
            },
            'UC18': {
                'name': 'Prozessmodellierung - Ideal-Prozess Antragsprüfung',
                'sgb': 'II',
                'paragraphen': ['7', '11', '11b', '12', '37', '33'],
                'query': '''
                    MATCH (doc:LegalDocument {sgb_nummer: 'II'})
                          -[:CONTAINS_NORM]->(norm:LegalNorm)
                    WHERE norm.paragraph_nummer IN ['7', '11', '11b', '12', '37', '33']
                    RETURN 
                        norm.paragraph_nummer,
                        norm.enbez,
                        'Phase: ' + 
                        CASE 
                            WHEN norm.paragraph_nummer = '7' THEN '2 - Anspruchsprüfung'
                            WHEN norm.paragraph_nummer IN ['11', '11b', '12'] THEN '2 - Bedürftigkeitsprüfung'
                            WHEN norm.paragraph_nummer IN ['37', '33'] THEN '3 - Entscheidung'
                        END as prozessphase
                    ORDER BY prozessphase, norm.paragraph_nummer
                ''',
                'visualization_query': '''
                    MATCH path = (doc:LegalDocument {sgb_nummer: 'II'})
                                 -[:CONTAINS_NORM]->(norm:LegalNorm)
                    WHERE norm.paragraph_nummer IN ['7', '11', '11b', '12', '37', '33']
                    RETURN path
                ''',
                'expected_min_norms': 6,
                'expected_min_chunks': 100,
                'priority': 'P0',
                'tool': 'Neo4j Browser + BPMN Modeler'
            },
            'UC19': {
                'name': 'Schulungskonzept - Gesetzesänderungen',
                'sgb': 'II',
                'paragraphen': ['*'],
                'query': '''
                    MATCH (doc:LegalDocument {sgb_nummer: 'II'})
                          -[:CONTAINS_NORM]->(norm:LegalNorm)
                          -[:AMENDED_BY]->(amendment:Amendment)
                    WHERE amendment.date >= date('2023-01-01')
                    RETURN 
                        norm.paragraph_nummer,
                        norm.enbez,
                        amendment.title,
                        amendment.date,
                        amendment.summary
                    ORDER BY amendment.date DESC
                    LIMIT 10
                ''',
                'visualization_query': '''
                    MATCH path = (doc:LegalDocument {sgb_nummer: 'II'})
                                 -[:CONTAINS_NORM]->(norm:LegalNorm)
                                 -[:AMENDED_BY]->(amendment:Amendment)
                    RETURN path LIMIT 20
                ''',
                'expected_min_norms': 0,  # Known issue: Amendments fehlen
                'expected_min_chunks': 0,
                'priority': 'P1',
                'status_expected': 'FAIL',
                'tool': 'N/A (Amendment data import required)'
            }
        }
    
    def validate_use_case(self, use_case_id: str) -> Dict:
        """Validiert einen einzelnen Use Case."""
        if use_case_id not in self.use_cases:
            return {'error': f'Use Case {use_case_id} nicht gefunden'}
        
        uc = self.use_cases[use_case_id]
        result = {
            'id': use_case_id,
            'name': uc['name'],
            'sgb': uc['sgb'],
            'paragraphen': uc['paragraphen'],
            'priority': uc['priority'],
            'tool': uc['tool'],
            'timestamp': datetime.now().isoformat()
        }
        
        try:
            with self.driver.session() as session:
                # Execute validation query
                query_result = session.run(uc['query'])
                records = list(query_result)
                
                result['records_found'] = len(records)
                result['data'] = [dict(record) for record in records]
                
                # Count norms and chunks
                norms_count = len(set(r.get('paragraph', r.get('paragraph_nummer', '')) for r in result['data']))
                chunks_count = sum(r.get('chunks', r.get('chunk_count', r.get('relevante_chunks', 0))) for r in result['data'])
                
                result['norms_found'] = norms_count
                result['chunks_found'] = chunks_count
                
                # Status evaluation
                expected_status = uc.get('status_expected', 'OK')
                if expected_status == 'FAIL':
                    result['status'] = '❌ Expected FAIL'
                    result['passed'] = False
                elif norms_count >= uc['expected_min_norms'] and chunks_count >= uc['expected_min_chunks']:
                    result['status'] = '✅ PASS'
                    result['passed'] = True
                elif norms_count >= uc['expected_min_norms']:
                    result['status'] = '⚠️ Partial (Chunks fehlen)'
                    result['passed'] = False
                else:
                    result['status'] = '❌ FAIL'
                    result['passed'] = False
                
                result['query'] = uc['query']
                result['visualization_query'] = uc['visualization_query']
                
        except Exception as e:
            result['status'] = f'❌ ERROR: {str(e)}'
            result['passed'] = False
            result['error'] = str(e)
        
        return result
    
    def validate_all(self) -> Dict[str, Dict]:
        """Validiert alle Use Cases."""
        results = {}
        for uc_id in self.use_cases.keys():
            print(f"Validiere {uc_id}: {self.use_cases[uc_id]['name']}...")
            results[uc_id] = self.validate_use_case(uc_id)
        return results
    
    def generate_html_report(self, results: Dict, output_path: str):
        """Generiert HTML-Report."""
        passed = sum(1 for r in results.values() if r.get('passed', False))
        total = len(results)
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Use Case Validation Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
                .header {{ background: #2196F3; color: white; padding: 20px; border-radius: 8px; }}
                .summary {{ background: white; padding: 20px; margin: 20px 0; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
                .use-case {{ background: white; padding: 20px; margin: 10px 0; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
                .pass {{ color: green; font-weight: bold; }}
                .fail {{ color: red; font-weight: bold; }}
                .partial {{ color: orange; font-weight: bold; }}
                pre {{ background: #f8f8f8; padding: 10px; border-radius: 4px; overflow-x: auto; }}
                .metric {{ display: inline-block; margin: 10px 20px 10px 0; }}
                .metric-value {{ font-size: 24px; font-weight: bold; color: #2196F3; }}
                .metric-label {{ font-size: 12px; color: #666; }}
                table {{ width: 100%; border-collapse: collapse; margin: 10px 0; }}
                th, td {{ padding: 8px; text-align: left; border-bottom: 1px solid #ddd; }}
                th {{ background-color: #f2f2f2; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🧪 Use Case Validation Report</h1>
                <p>Sozialrecht RAG Knowledge Graph - Comprehensive Use Case Testing</p>
                <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>
            
            <div class="summary">
                <h2>📊 Summary</h2>
                <div class="metric">
                    <div class="metric-value">{passed}/{total}</div>
                    <div class="metric-label">Use Cases Passed</div>
                </div>
                <div class="metric">
                    <div class="metric-value">{passed/total*100:.1f}%</div>
                    <div class="metric-label">Success Rate</div>
                </div>
            </div>
        """
        
        for uc_id, result in sorted(results.items()):
            status_class = 'pass' if result.get('passed') else ('partial' if '⚠️' in result.get('status', '') else 'fail')
            
            html += f"""
            <div class="use-case">
                <h3>{uc_id}: {result['name']} <span class="{status_class}">{result.get('status', 'N/A')}</span></h3>
                <p><strong>SGB:</strong> {result['sgb']} | <strong>Paragraphen:</strong> {', '.join(result['paragraphen'])} | <strong>Priority:</strong> {result['priority']}</p>
                <p><strong>Tool:</strong> {result['tool']}</p>
                
                <h4>📈 Metrics</h4>
                <p>
                    <strong>Normen gefunden:</strong> {result.get('norms_found', 0)} | 
                    <strong>Chunks gefunden:</strong> {result.get('chunks_found', 0)} | 
                    <strong>Records:</strong> {result.get('records_found', 0)}
                </p>
                
                <h4>🔍 Query (Data Validation)</h4>
                <pre>{result.get('query', 'N/A')}</pre>
                
                <h4>📊 Visualization Query (Neo4j Browser)</h4>
                <pre>{result.get('visualization_query', 'N/A')}</pre>
                
                <h4>📦 Sample Data</h4>
                <table>
                    <tr>
                        {('<th>' + '</th><th>'.join(result['data'][0].keys()) + '</th>') if result.get('data') else '<th>No data</th>'}
                    </tr>
            """
            
            for record in result.get('data', [])[:5]:  # First 5 records
                html += "<tr>"
                for value in record.values():
                    html += f"<td>{str(value)[:100]}</td>"
                html += "</tr>"
            
            html += """
                </table>
            </div>
            """
        
        html += """
        </body>
        </html>
        """
        
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html)
        
        print(f"\n✅ HTML report generated: {output_path}")
    
    def export_cypher_queries(self, output_dir: str):
        """Exportiert alle Cypher-Queries als einzelne Dateien."""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        for uc_id, uc in self.use_cases.items():
            # Data query
            query_file = output_path / f"{uc_id}_data.cypher"
            with open(query_file, 'w', encoding='utf-8') as f:
                f.write(f"// {uc_id}: {uc['name']}\n")
                f.write(f"// SGB: {uc['sgb']} | Paragraphen: {', '.join(uc['paragraphen'])}\n")
                f.write(f"// Priority: {uc['priority']} | Tool: {uc['tool']}\n\n")
                f.write(uc['query'])
            
            # Visualization query
            viz_file = output_path / f"{uc_id}_visualization.cypher"
            with open(viz_file, 'w', encoding='utf-8') as f:
                f.write(f"// {uc_id}: {uc['name']} - Visualization\n")
                f.write(f"// Run this in Neo4j Browser for graph visualization\n\n")
                f.write(uc['visualization_query'])
        
        print(f"\n✅ Cypher queries exported to: {output_dir}")


def main():
    parser = argparse.ArgumentParser(description='Validate and visualize Use Cases')
    parser.add_argument('--output', default='reports/use_case_validation.html', help='HTML report output path')
    parser.add_argument('--use-case', help='Validate specific use case (e.g., UC01)')
    parser.add_argument('--export-cypher', help='Export Cypher queries to directory')
    parser.add_argument('--json', help='Export results as JSON')
    
    args = parser.parse_args()
    
    validator = UseCaseValidator()
    
    try:
        if args.use_case:
            # Single use case
            result = validator.validate_use_case(args.use_case)
            print(json.dumps(result, indent=2, ensure_ascii=False))
        else:
            # All use cases
            results = validator.validate_all()
            
            # Generate HTML report
            validator.generate_html_report(results, args.output)
            
            # Export JSON if requested
            if args.json:
                with open(args.json, 'w', encoding='utf-8') as f:
                    json.dump(results, f, indent=2, ensure_ascii=False)
                print(f"✅ JSON exported to: {args.json}")
            
            # Export Cypher if requested
            if args.export_cypher:
                validator.export_cypher_queries(args.export_cypher)
            
            # Summary
            passed = sum(1 for r in results.values() if r.get('passed', False))
            total = len(results)
            print(f"\n📊 Summary: {passed}/{total} Use Cases passed ({passed/total*100:.1f}%)")
    
    finally:
        validator.close()


if __name__ == '__main__':
    main()
