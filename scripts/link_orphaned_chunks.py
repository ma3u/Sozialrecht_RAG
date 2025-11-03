#!/usr/bin/env python3
"""
Link Orphaned Chunks to Legal Norms
Verlinkt Chunks die existieren aber nicht mit LegalNorms verbunden sind

Usage:
    python scripts/link_orphaned_chunks.py --sgb III
    python scripts/link_orphaned_chunks.py --all
    python scripts/link_orphaned_chunks.py --sgb V --dry-run
"""

import os
import sys
import argparse
import re
from typing import List, Dict, Optional
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")


def extract_paragraph_from_context(paragraph_context: str) -> Optional[str]:
    """Extrahiert Paragraph-Nummer aus dem Kontext"""
    # Beispiel: "SGB III § 44 (1)" -> "44"
    # Beispiel: "SGB V §§ 140a-140d" -> "140a"
    
    patterns = [
        r'§§?\s*(\d+[a-z]?)',  # § 44 oder §§ 140a
        r'Paragraph\s+(\d+[a-z]?)',
        r'Para\.\s+(\d+[a-z]?)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, paragraph_context)
        if match:
            return match.group(1)
    
    return None


def find_orphaned_chunks(driver, sgb_nummer: str) -> List[Dict]:
    """Findet verwaiste Chunks für ein SGB"""
    
    with driver.session() as session:
        result = session.run("""
            MATCH (chunk:Chunk)
            WHERE chunk.paragraph_context CONTAINS $sgb_pattern
            AND NOT EXISTS {
                MATCH (chunk)<-[:HAS_CHUNK]-(:LegalNorm)
            }
            RETURN 
                elementId(chunk) as chunk_id,
                chunk.paragraph_context as context,
                chunk.text as text
            LIMIT 1000
        """, sgb_pattern=f"SGB {sgb_nummer}")
        
        return [dict(record) for record in result]


def find_matching_norm(driver, sgb_nummer: str, paragraph: str) -> Optional[str]:
    """Findet passende LegalNorm für einen Paragraphen"""
    
    with driver.session() as session:
        # Versuche exakte Übereinstimmung
        result = session.run("""
            MATCH (doc:LegalDocument {sgb_nummer: $sgb})-[:CONTAINS_NORM]->(norm:LegalNorm)
            WHERE norm.paragraph_nummer = $paragraph
            RETURN elementId(norm) as norm_id
            LIMIT 1
        """, sgb=sgb_nummer, paragraph=paragraph)
        
        record = result.single()
        if record:
            return record["norm_id"]
        
        # Versuche mit führenden Nullen entfernt (z.B. "044" -> "44")
        paragraph_stripped = paragraph.lstrip('0')
        if paragraph_stripped != paragraph:
            result = session.run("""
                MATCH (doc:LegalDocument {sgb_nummer: $sgb})-[:CONTAINS_NORM]->(norm:LegalNorm)
                WHERE norm.paragraph_nummer = $paragraph
                RETURN elementId(norm) as norm_id
                LIMIT 1
            """, sgb=sgb_nummer, paragraph=paragraph_stripped)
            
            record = result.single()
            if record:
                return record["norm_id"]
    
    return None


def link_chunk_to_norm(driver, chunk_id: str, norm_id: str) -> bool:
    """Erstellt Verbindung zwischen Chunk und LegalNorm"""
    
    with driver.session() as session:
        try:
            session.run("""
                MATCH (chunk:Chunk), (norm:LegalNorm)
                WHERE elementId(chunk) = $chunk_id
                AND elementId(norm) = $norm_id
                MERGE (norm)-[:HAS_CHUNK]->(chunk)
            """, chunk_id=chunk_id, norm_id=norm_id)
            return True
        except Exception as e:
            print(f"❌ Fehler beim Verlinken: {e}")
            return False


def main():
    parser = argparse.ArgumentParser(description="Link Orphaned Chunks to Legal Norms")
    parser.add_argument("--sgb", type=str, help="SGB Nummern (komma-separiert)")
    parser.add_argument("--all", action="store_true", help="Alle SGBs verarbeiten")
    parser.add_argument("--dry-run", action="store_true", help="Nur Analyse, keine Änderungen")
    
    args = parser.parse_args()
    
    print("\n" + "="*80)
    print("🔗 ORPHANED CHUNKS LINKER")
    print("="*80)
    print(f"\nModus: {'DRY-RUN' if args.dry_run else 'EXECUTE'}")
    
    # Connect to Neo4j
    try:
        driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))
        driver.verify_connectivity()
        print(f"✅ Connected to Neo4j: {NEO4J_URI}")
    except Exception as e:
        print(f"❌ Neo4j connection failed: {e}")
        return 1
    
    # Determine which SGBs to process
    if args.all:
        sgb_list = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X", "XI", "XII", "XIII", "XIV"]
    elif args.sgb:
        sgb_list = [s.strip() for s in args.sgb.split(",")]
    else:
        # Default: problematic SGBs
        sgb_list = ["III", "V", "VI", "VII", "XI"]
    
    print(f"\n📋 Processing SGBs: {', '.join(sgb_list)}")
    
    total_found = 0
    total_linked = 0
    total_not_found = 0
    
    for sgb in sgb_list:
        print(f"\n{'='*80}")
        print(f"📊 SGB {sgb}")
        print(f"{'='*80}")
        
        # Find orphaned chunks
        orphaned = find_orphaned_chunks(driver, sgb)
        print(f"✅ Gefunden: {len(orphaned)} verwaiste Chunks")
        
        if not orphaned:
            continue
        
        total_found += len(orphaned)
        
        linked = 0
        not_found = 0
        
        for i, chunk in enumerate(orphaned, 1):
            # Extract paragraph from context
            paragraph = extract_paragraph_from_context(chunk["context"])
            
            if not paragraph:
                if i <= 5:  # Show first 5 failures
                    print(f"  ⚠️  Chunk {i}: Konnte Paragraph nicht aus Kontext extrahieren")
                    print(f"      Context: {chunk['context'][:80]}...")
                not_found += 1
                continue
            
            # Find matching norm
            norm_id = find_matching_norm(driver, sgb, paragraph)
            
            if not norm_id:
                if i <= 5:
                    print(f"  ⚠️  Chunk {i}: Keine LegalNorm für § {paragraph} gefunden")
                not_found += 1
                continue
            
            # Link chunk to norm
            if not args.dry_run:
                if link_chunk_to_norm(driver, chunk["chunk_id"], norm_id):
                    linked += 1
                    if i <= 10:  # Show first 10 successes
                        print(f"  ✅ Chunk {i}: Verlinkt mit § {paragraph}")
                else:
                    not_found += 1
            else:
                linked += 1
                if i <= 10:
                    print(f"  🔍 Chunk {i}: Würde verlinken mit § {paragraph}")
        
        total_linked += linked
        total_not_found += not_found
        
        print(f"\n  Ergebnis: {linked} verlinkt, {not_found} nicht gefunden")
    
    # Summary
    print(f"\n{'='*80}")
    print("📈 ZUSAMMENFASSUNG")
    print(f"{'='*80}")
    print(f"Verwaiste Chunks gefunden: {total_found}")
    print(f"Erfolgreich verlinkt:      {total_linked}")
    print(f"Nicht gefunden:            {total_not_found}")
    
    if args.dry_run:
        print(f"\n➡️  Führe ohne --dry-run aus um Verlinkungen zu erstellen")
    else:
        print(f"\n🎉 Verlinkungen erstellt!")
    
    print("="*80 + "\n")
    
    driver.close()
    return 0


if __name__ == "__main__":
    exit(main())
