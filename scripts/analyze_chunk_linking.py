#!/usr/bin/env python3
"""
Analyze Chunk Linking Issues
Prüft warum bestimmte Rechtsnormen keine Chunks haben

Usage:
    python scripts/analyze_chunk_linking.py --sgb III,V,VI,VII,XI
    python scripts/analyze_chunk_linking.py --all
    python scripts/analyze_chunk_linking.py --sgb X --verbose
"""

import os
import sys
import argparse
import json
from typing import List, Dict, Optional
from datetime import datetime
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")


def analyze_sgb_chunk_linking(driver, sgb_nummer: str) -> Dict:
    """Analysiert Chunk-Verlinkung für ein bestimmtes SGB"""
    
    with driver.session() as session:
        # 1. Norms über LegalDocument verlinkt
        result = session.run("""
            MATCH (doc:LegalDocument {sgb_nummer: $sgb})-[:CONTAINS_NORM]->(norm:LegalNorm)
            OPTIONAL MATCH (norm)-[:HAS_CHUNK]->(chunk:Chunk)
            RETURN 
                count(DISTINCT norm) as total_norms,
                count(DISTINCT chunk) as chunks_via_norm,
                count(DISTINCT CASE WHEN chunk IS NULL THEN norm ELSE NULL END) as norms_without_chunks
        """, sgb=sgb_nummer)
        legal_doc_stats = result.single()
        
        # 2. Chunks über Document verlinkt
        result = session.run("""
            MATCH (doc:Document)-[:HAS_CHUNK]->(chunk:Chunk)
            WHERE doc.filepath CONTAINS $sgb_pattern
            RETURN count(DISTINCT chunk) as chunks_via_document
        """, sgb_pattern=f"SGB_{sgb_nummer}")
        doc_stats = result.single()
        
        # 3. Orphaned Chunks (existieren aber nicht verlinkt)
        result = session.run("""
            MATCH (chunk:Chunk)
            WHERE chunk.paragraph_context CONTAINS $sgb_pattern
            AND NOT EXISTS {
                MATCH (chunk)<-[:HAS_CHUNK]-(:LegalNorm)<-[:CONTAINS_NORM]-(:LegalDocument {sgb_nummer: $sgb})
            }
            RETURN count(chunk) as orphaned_chunks
        """, sgb_pattern=f"SGB {sgb_nummer}", sgb=sgb_nummer)
        orphan_stats = result.single()
        
        # 4. Norms mit TextUnits aber ohne Chunks
        result = session.run("""
            MATCH (doc:LegalDocument {sgb_nummer: $sgb})-[:CONTAINS_NORM]->(norm:LegalNorm)
            WHERE EXISTS {
                MATCH (norm)-[:HAS_CONTENT]->(:TextUnit)
            }
            AND NOT EXISTS {
                MATCH (norm)-[:HAS_CHUNK]->(:Chunk)
            }
            RETURN 
                count(norm) as norms_with_textunits_no_chunks,
                collect(norm.paragraph_nummer)[0..10] as sample_paragraphs
        """, sgb=sgb_nummer)
        textunit_stats = result.single()
        
        # 5. Sample von Norms ohne Chunks
        result = session.run("""
            MATCH (doc:LegalDocument {sgb_nummer: $sgb})-[:CONTAINS_NORM]->(norm:LegalNorm)
            WHERE NOT EXISTS {
                MATCH (norm)-[:HAS_CHUNK]->(:Chunk)
            }
            RETURN 
                norm.paragraph_nummer as paragraph,
                norm.enbez as enbez,
                norm.titel as titel,
                EXISTS((norm)-[:HAS_CONTENT]->(:TextUnit)) as has_textunits
            LIMIT 20
        """, sgb=sgb_nummer)
        samples = [dict(record) for record in result]
        
        return {
            "sgb": sgb_nummer,
            "legal_document_path": {
                "total_norms": legal_doc_stats["total_norms"],
                "chunks_via_norm": legal_doc_stats["chunks_via_norm"],
                "norms_without_chunks": legal_doc_stats["norms_without_chunks"]
            },
            "document_path": {
                "chunks_via_document": doc_stats["chunks_via_document"] if doc_stats else 0
            },
            "orphaned_chunks": orphan_stats["orphaned_chunks"] if orphan_stats else 0,
            "textunits_without_chunks": {
                "count": textunit_stats["norms_with_textunits_no_chunks"],
                "sample_paragraphs": textunit_stats["sample_paragraphs"]
            },
            "sample_norms_without_chunks": samples
        }


def get_all_sgbs(driver) -> List[str]:
    """Holt alle verfügbaren SGB Nummern"""
    with driver.session() as session:
        result = session.run("""
            MATCH (doc:LegalDocument)
            WHERE doc.sgb_nummer IS NOT NULL
            RETURN DISTINCT doc.sgb_nummer as sgb
            ORDER BY sgb
        """)
        return [record["sgb"] for record in result]


def print_analysis(analysis: Dict, verbose: bool = False):
    """Formatierte Ausgabe der Analyse"""
    
    print(f"\n{'='*80}")
    print(f"📊 SGB {analysis['sgb']} - CHUNK LINKING ANALYSIS")
    print(f"{'='*80}")
    
    ld = analysis['legal_document_path']
    doc = analysis['document_path']
    
    print(f"\n1️⃣  LegalDocument → Norm → Chunk Path:")
    print(f"   Total Norms:           {ld['total_norms']:>6}")
    print(f"   Chunks via Norm:       {ld['chunks_via_norm']:>6}")
    print(f"   Norms WITHOUT Chunks:  {ld['norms_without_chunks']:>6} ⚠️")
    
    print(f"\n2️⃣  Document → Chunk Path:")
    print(f"   Chunks via Document:   {doc['chunks_via_document']:>6}")
    
    print(f"\n3️⃣  Orphaned Chunks:")
    print(f"   Chunks not linked:     {analysis['orphaned_chunks']:>6}")
    
    tu = analysis['textunits_without_chunks']
    print(f"\n4️⃣  Norms with TextUnits but NO Chunks:")
    print(f"   Count:                 {tu['count']:>6}")
    if tu['sample_paragraphs'] and verbose:
        print(f"   Samples: {', '.join(tu['sample_paragraphs'][:5])}")
    
    # Diagnose
    print(f"\n🔍 DIAGNOSE:")
    
    if ld['norms_without_chunks'] > 0 and tu['count'] > 0:
        print(f"   ⚠️  {tu['count']} Norms haben TextUnits aber keine Chunks")
        print(f"   → Chunks wurden vermutlich nicht generiert oder verlinkt")
        print(f"   → Lösung: Chunk-Generierung für diese Norms ausführen")
    
    if analysis['orphaned_chunks'] > 0:
        print(f"   ⚠️  {analysis['orphaned_chunks']} Chunks existieren aber sind nicht verlinkt")
        print(f"   → Lösung: Verlinkung korrigieren")
    
    if doc['chunks_via_document'] > ld['chunks_via_norm']:
        diff = doc['chunks_via_document'] - ld['chunks_via_norm']
        print(f"   ℹ️  {diff} Chunks sind über Document aber nicht über LegalNorm verlinkt")
        print(f"   → Dies ist OK wenn PDFs direkt importiert wurden")
    
    if verbose and analysis['sample_norms_without_chunks']:
        print(f"\n📝 Sample Norms ohne Chunks:")
        for i, norm in enumerate(analysis['sample_norms_without_chunks'][:10], 1):
            has_tu = "✅ TextUnits" if norm['has_textunits'] else "❌ No TextUnits"
            print(f"   {i}. {norm['paragraph']} - {norm['enbez']} ({has_tu})")


def suggest_fixes(all_analyses: List[Dict]) -> List[Dict]:
    """Generiert konkrete Fix-Vorschläge"""
    
    suggestions = []
    
    for analysis in all_analyses:
        sgb = analysis['sgb']
        norms_without_chunks = analysis['legal_document_path']['norms_without_chunks']
        textunits_without_chunks = analysis['textunits_without_chunks']['count']
        orphaned_chunks = analysis['orphaned_chunks']
        
        if textunits_without_chunks > 0:
            suggestions.append({
                "sgb": sgb,
                "priority": "HIGH",
                "issue": f"{textunits_without_chunks} Norms mit TextUnits aber ohne Chunks",
                "fix": f"python scripts/generate_chunks_from_textunits.py --sgb {sgb}",
                "expected_impact": f"+{textunits_without_chunks * 2} Chunks (geschätzt)"
            })
        
        if orphaned_chunks > 0:
            suggestions.append({
                "sgb": sgb,
                "priority": "MEDIUM",
                "issue": f"{orphaned_chunks} verwaiste Chunks",
                "fix": f"python scripts/link_orphaned_chunks.py --sgb {sgb}",
                "expected_impact": f"Verbesserte RAG-Abdeckung"
            })
        
        if norms_without_chunks > 50 and textunits_without_chunks == 0:
            suggestions.append({
                "sgb": sgb,
                "priority": "LOW",
                "issue": f"{norms_without_chunks} Norms ohne Content",
                "fix": "Manuelle Prüfung: Sind diese Norms leer oder Verweise?",
                "expected_impact": "Dokumentation"
            })
    
    return suggestions


def main():
    parser = argparse.ArgumentParser(description="Analyze Chunk Linking Issues")
    parser.add_argument("--sgb", type=str, help="SGB Nummern (komma-separiert, z.B. 'III,V,VI')")
    parser.add_argument("--all", action="store_true", help="Alle SGBs analysieren")
    parser.add_argument("--verbose", action="store_true", help="Detaillierte Ausgabe")
    parser.add_argument("--output", type=str, help="Output JSON file")
    
    args = parser.parse_args()
    
    print("\n" + "="*80)
    print("🔍 CHUNK LINKING ANALYSIS")
    print("="*80)
    
    # Connect to Neo4j
    try:
        driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))
        driver.verify_connectivity()
        print(f"\n✅ Connected to Neo4j: {NEO4J_URI}")
    except Exception as e:
        print(f"\n❌ Neo4j connection failed: {e}")
        return 1
    
    # Determine which SGBs to analyze
    if args.all:
        sgb_list = get_all_sgbs(driver)
        print(f"✅ Analyzing all SGBs: {', '.join(sgb_list)}")
    elif args.sgb:
        sgb_list = [s.strip() for s in args.sgb.split(",")]
        print(f"✅ Analyzing SGBs: {', '.join(sgb_list)}")
    else:
        # Default: problematic SGBs from report
        sgb_list = ["III", "V", "VI", "VII", "XI"]
        print(f"✅ Analyzing problematic SGBs: {', '.join(sgb_list)}")
    
    # Analyze each SGB
    all_analyses = []
    for sgb in sgb_list:
        analysis = analyze_sgb_chunk_linking(driver, sgb)
        all_analyses.append(analysis)
        print_analysis(analysis, args.verbose)
    
    # Summary
    print(f"\n{'='*80}")
    print("📊 SUMMARY")
    print(f"{'='*80}")
    
    total_norms = sum(a['legal_document_path']['total_norms'] for a in all_analyses)
    total_without_chunks = sum(a['legal_document_path']['norms_without_chunks'] for a in all_analyses)
    total_orphaned = sum(a['orphaned_chunks'] for a in all_analyses)
    
    print(f"\nAcross {len(sgb_list)} SGBs:")
    print(f"  Total Norms:           {total_norms:>6}")
    print(f"  Norms without Chunks:  {total_without_chunks:>6} ({100*total_without_chunks/total_norms:.1f}%)")
    print(f"  Orphaned Chunks:       {total_orphaned:>6}")
    
    # Fix suggestions
    suggestions = suggest_fixes(all_analyses)
    
    if suggestions:
        print(f"\n{'='*80}")
        print("💡 FIX SUGGESTIONS")
        print(f"{'='*80}")
        
        for i, sug in enumerate(suggestions, 1):
            print(f"\n{i}. [{sug['priority']}] SGB {sug['sgb']}")
            print(f"   Issue:  {sug['issue']}")
            print(f"   Fix:    {sug['fix']}")
            print(f"   Impact: {sug['expected_impact']}")
    
    # Save output
    output_data = {
        "timestamp": datetime.now().isoformat(),
        "analyses": all_analyses,
        "summary": {
            "total_sgbs": len(sgb_list),
            "total_norms": total_norms,
            "norms_without_chunks": total_without_chunks,
            "orphaned_chunks": total_orphaned
        },
        "suggestions": suggestions
    }
    
    output_file = args.output or f"logs/chunk_linking_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Analysis saved to: {output_file}")
    print()
    
    driver.close()
    return 0


if __name__ == "__main__":
    exit(main())
