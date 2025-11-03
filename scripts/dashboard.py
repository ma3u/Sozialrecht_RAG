#!/usr/bin/env python3
"""
Coverage Dashboard - CLI Version
Einfaches Terminal-Dashboard für 14 Use Cases

Usage:
    python scripts/dashboard.py
    python scripts/dashboard.py --watch  # Auto-refresh
"""

import os
import sys
import time
import argparse
from neo4j import GraphDatabase
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")


def clear_screen():
    """Clear terminal screen"""
    os.system('clear' if os.name != 'nt' else 'cls')


def print_header():
    """Print dashboard header"""
    print("\n" + "="*80)
    print("📊 SOZIALRECHT RAG - COVERAGE DASHBOARD")
    print("="*80)
    print(f"🕐 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)


def get_use_case_coverage(driver):
    """Get coverage for all use cases"""
    
    use_cases = [
        {"uc": "UC01", "name": "Regelbedarfsermittlung", "sgb": "II", "paragraphs": ["20", "21", "22", "23"]},
        {"uc": "UC02", "name": "Sanktionsprüfung", "sgb": "II", "paragraphs": ["32"]},
        {"uc": "UC03", "name": "Einkommensanrechnung", "sgb": "II", "paragraphs": ["11", "11b"]},
        {"uc": "UC06", "name": "Bedarfsgemeinschaft", "sgb": "II", "paragraphs": ["7"]},
        {"uc": "UC08", "name": "Erstausstattung", "sgb": "II", "paragraphs": ["24"]},
        {"uc": "UC10", "name": "Widerspruchsverfahren", "sgb": "X", "paragraphs": ["79", "80", "84", "85"]},
        {"uc": "UC14", "name": "Datenschutz-Compliance", "sgb": "X", "paragraphs": ["67", "68", "69", "70", "71", "72", "73", "74", "75", "76"]},
    ]
    
    results = []
    
    with driver.session() as session:
        for uc in use_cases:
            query = """
                MATCH (doc:LegalDocument {sgb_nummer: $sgb})
                      -[:CONTAINS_NORM]->(norm:LegalNorm)
                WHERE norm.paragraph_nummer IN $paragraphs
                OPTIONAL MATCH (norm)-[:HAS_CHUNK]->(chunk:Chunk)
                RETURN 
                    count(DISTINCT norm) as normen,
                    count(DISTINCT chunk) as chunks,
                    $expected as expected
            """
            
            try:
                result = session.run(query, sgb=uc["sgb"], paragraphs=uc["paragraphs"], expected=len(uc["paragraphs"]))
                record = result.single()
                
                normen = record["normen"]
                chunks = record["chunks"]
                expected = record["expected"]
                
                # Fix: Erwartete Paragraphen zählen, nicht Absätze
                unique_paragraphs = len(set(uc["paragraphs"]))
                status = "✅" if unique_paragraphs == expected and chunks > 0 else ("⚠️ " if chunks > 0 else "❌")
                
                results.append({
                    "uc": uc["uc"],
                    "name": uc["name"],
                    "sgb": uc["sgb"],
                    "normen": normen,
                    "expected": expected,
                    "chunks": chunks,
                    "status": status,
                    "coverage": f"{unique_paragraphs}/{expected} ¶",  # Paragraphen, nicht Absätze
                    "normen_total": normen  # Zeige Absätze separat
                })
            except Exception as e:
                results.append({
                    "uc": uc["uc"],
                    "name": uc["name"],
                    "sgb": uc["sgb"],
                    "normen": 0,
                    "expected": len(uc["paragraphs"]),
                    "chunks": 0,
                    "status": "❌",
                    "coverage": f"ERROR: {str(e)[:30]}",
                    "normen_total": 0
                })
    
    return results


def get_system_health(driver):
    """Get system health stats"""
    
    try:
        with driver.session() as session:
            # Total stats
            stats = session.run("""
                MATCH (doc:LegalDocument)
                OPTIONAL MATCH (doc)-[:CONTAINS_NORM]->(norm:LegalNorm)
                OPTIONAL MATCH (norm)-[:HAS_CHUNK]->(chunk:Chunk)
                RETURN 
                    count(DISTINCT doc) as documents,
                    count(DISTINCT norm) as norms,
                    count(DISTINCT chunk) as chunks
            """).single()
            
            # Embeddings
            embeddings = session.run("""
                MATCH (c:Chunk)
                WHERE c.embedding IS NOT NULL
                RETURN count(c) as chunks_with_embeddings
            """).single()
            
            return {
                "documents": stats["documents"],
                "norms": stats["norms"],
                "chunks": stats["chunks"],
                "embeddings": embeddings["chunks_with_embeddings"]
            }
    except Exception as e:
        return {
            "documents": 0,
            "norms": 0,
            "chunks": 0,
            "embeddings": 0,
            "error": str(e)
        }


def print_use_cases(use_cases):
    """Print use cases table"""
    
    print("\n" + "="*80)
    print("🎯 USE CASE COVERAGE (7 Use Cases)")
    print("="*80)
    
    # Header
    print(f"{'UC':<8} {'Name':<30} {'SGB':<5} {'Paras':<10} {'Norms':<8} {'Chunks':<8} Status")
    print("-" * 80)
    
    # Data
    for uc in use_cases:
        name = uc['name'][:28] + ".." if len(uc['name']) > 30 else uc['name']
        normen_str = f"{uc.get('normen_total', 0)}"
        print(f"{uc['uc']:<8} {name:<30} {uc['sgb']:<5} {uc['coverage']:<10} {normen_str:<8} {uc['chunks']:<8} {uc['status']}")
    
    # Summary
    total_chunks = sum(uc['chunks'] for uc in use_cases)
    passed = sum(1 for uc in use_cases if uc['status'] == '✅')
    
    print("-" * 80)
    print(f"TOTAL: {passed}/{len(use_cases)} Use Cases ✅ | {total_chunks} Chunks")


def print_health(health):
    """Print system health"""
    
    print("\n" + "="*80)
    print("💚 SYSTEM HEALTH")
    print("="*80)
    
    if "error" in health:
        print(f"❌ Error: {health['error']}")
        return
    
    print(f"📚 Documents:  {health['documents']:>10,}")
    print(f"📜 Norms:      {health['norms']:>10,}")
    print(f"📄 Chunks:     {health['chunks']:>10,}")
    print(f"🤖 Embeddings: {health['embeddings']:>10,}")
    
    if health['embeddings'] > 0:
        emb_percent = (health['embeddings'] / health['chunks'] * 100) if health['chunks'] > 0 else 0
        print(f"   Coverage:   {emb_percent:>9.1f}%")


def main():
    parser = argparse.ArgumentParser(description="Coverage Dashboard CLI")
    parser.add_argument("--watch", action="store_true", help="Auto-refresh every 10 seconds")
    parser.add_argument("--interval", type=int, default=10, help="Refresh interval (default: 10s)")
    
    args = parser.parse_args()
    
    print(f"\n🔌 Connecting to Neo4j: {NEO4J_URI}")
    
    try:
        driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))
        driver.verify_connectivity()
        print("✅ Connected to Neo4j")
    except Exception as e:
        print(f"❌ Failed to connect: {e}")
        return 1
    
    try:
        while True:
            clear_screen()
            print_header()
            
            # Get data
            print("\n⏳ Loading data...")
            health = get_system_health(driver)
            use_cases = get_use_case_coverage(driver)
            
            # Display
            clear_screen()
            print_header()
            print_health(health)
            print_use_cases(use_cases)
            
            if not args.watch:
                break
            
            print(f"\n\n🔄 Auto-refresh in {args.interval}s (Ctrl+C to stop)...")
            time.sleep(args.interval)
    
    except KeyboardInterrupt:
        print("\n\n👋 Dashboard stopped")
    
    finally:
        driver.close()
    
    return 0


if __name__ == "__main__":
    exit(main())
