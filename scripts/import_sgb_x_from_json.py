#!/usr/bin/env python3
"""
Importiert SGB X Paragraphen §§ 67-76 aus JSON in Neo4j

Liest die geparsten Paragraphen und importiert sie vollständig:
- Erstellt LegalNorm Nodes
- Erstellt CONTAINS_NORM Relationships
- Chunked Text und erstellt HAS_CHUNK Relationships

Usage:
    python scripts/import_sgb_x_from_json.py temp_data/sgb_x_paragraphs_67-76.json --dry-run
    python scripts/import_sgb_x_from_json.py temp_data/sgb_x_paragraphs_67-76.json --execute
"""

import os
import sys
import json
import re
import argparse
from pathlib import Path
from typing import List, Dict
from dotenv import load_dotenv
from neo4j import GraphDatabase

load_dotenv()

class SGBXJSONImporter:
    """Importiert SGB X Paragraphen aus JSON in Neo4j"""
    
    def __init__(self):
        self.uri = os.getenv('NEO4J_URI')
        self.password = os.getenv('NEO4J_PASSWORD')
        self.driver = GraphDatabase.driver(self.uri, auth=('neo4j', self.password))
        self.sgb_x_doknr = 'BJNR114690980'
    
    def close(self):
        self.driver.close()
    
    def load_json(self, json_file: str) -> List[Dict]:
        """Lädt Paragraphen aus JSON"""
        with open(json_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def chunk_text(self, text: str) -> List[str]:
        """
        Teilt Paragraph-Text in sinnvolle Chunks
        
        Strategie:
        1. Split bei Absätzen (1), (2), etc.
        2. Falls keine Absätze: Split bei doppelten Zeilenumbrüchen
        3. Falls zu lang: Split bei Satzenden
        """
        # Versuch 1: Split bei (1), (2), etc.
        absaetze = re.split(r'(?=\(\d+\)\s)', text)
        absaetze = [a.strip() for a in absaetze if a.strip()]
        
        if len(absaetze) > 1:
            return absaetze
        
        # Versuch 2: Split bei doppelten Absätzen
        chunks = text.split('\n\n')
        chunks = [c.strip() for c in chunks if c.strip()]
        
        if len(chunks) > 1:
            return chunks
        
        # Versuch 3: Ganzer Text als ein Chunk (falls keine natürlichen Breaks)
        return [text]
    
    def check_existing_norm(self, paragraph: str) -> bool:
        """Prüft ob Paragraph bereits existiert"""
        query = """
            MATCH (doc:LegalDocument {sgb_nummer: 'X'})
                  -[:CONTAINS_NORM]->(norm:LegalNorm {paragraph_nummer: $paragraph})
            RETURN count(norm) as count
        """
        
        with self.driver.session() as session:
            result = session.run(query, paragraph=paragraph)
            record = result.single()
            return record['count'] > 0 if record else False
    
    def create_or_update_norm(self, para_data: Dict, dry_run: bool = True) -> str:
        """Erstellt oder aktualisiert LegalNorm Node"""
        
        # Prüfe ob Norm bereits existiert (als orphan)
        check_query = """
            MATCH (norm:LegalNorm {
                paragraph_nummer: $paragraph,
                norm_doknr: $doknr
            })
            RETURN norm.id as norm_id, count(norm) as count
        """
        
        with self.driver.session() as session:
            result = session.run(
                check_query,
                paragraph=para_data['paragraph'],
                doknr=self.sgb_x_doknr
            )
            record = result.single()
            
            if record and record['count'] > 0:
                print(f"   ℹ️  Norm bereits vorhanden: {para_data['enbez']}")
                return record['norm_id']
        
        # Erstelle neue Norm
        create_query = """
            CREATE (norm:LegalNorm {
                id: $id,
                paragraph_nummer: $paragraph,
                enbez: $enbez,
                titel: $titel,
                norm_doknr: $doknr,
                text: $text
            })
            RETURN norm.id as norm_id
        """
        
        norm_id = f"norm_sgb_x_{para_data['paragraph']}"
        
        if dry_run:
            print(f"   [DRY-RUN] Würde erstellen: {norm_id}")
            return norm_id
        
        with self.driver.session() as session:
            result = session.run(
                create_query,
                id=norm_id,
                paragraph=para_data['paragraph'],
                enbez=para_data['enbez'],
                titel=para_data['titel'],
                doknr=self.sgb_x_doknr,
                text=para_data['text']
            )
            record = result.single()
            print(f"   ✅ Norm erstellt: {record['norm_id']}")
            return record['norm_id']
    
    def link_to_document(self, paragraph: str, dry_run: bool = True):
        """Erstellt CONTAINS_NORM Relationship"""
        query = """
            MATCH (doc:LegalDocument {sgb_nummer: 'X'})
            MATCH (norm:LegalNorm {
                paragraph_nummer: $paragraph,
                norm_doknr: $doknr
            })
            MERGE (doc)-[:CONTAINS_NORM]->(norm)
            RETURN doc.title as doc_title, norm.enbez as norm_title
        """
        
        if dry_run:
            print(f"   [DRY-RUN] Würde verlinken: SGB X → § {paragraph}")
            return
        
        with self.driver.session() as session:
            result = session.run(query, paragraph=paragraph, doknr=self.sgb_x_doknr)
            record = result.single()
            if record:
                print(f"   ✅ CONTAINS_NORM: {record['doc_title']} → {record['norm_title']}")
    
    def create_chunks(self, para_data: Dict, dry_run: bool = True) -> int:
        """Erstellt Chunks für einen Paragraphen"""
        chunks = self.chunk_text(para_data['text'])
        
        print(f"   📝 {len(chunks)} Chunks für {para_data['enbez']}")
        
        if dry_run:
            for i, chunk_text in enumerate(chunks[:2]):  # Preview ersten 2
                preview = chunk_text[:80].replace('\n', ' ')
                print(f"      [DRY-RUN] Chunk {i}: {preview}...")
            if len(chunks) > 2:
                print(f"      ... und {len(chunks)-2} weitere")
            return len(chunks)
        
        # Lösche alte Chunks (falls welche existieren)
        delete_query = """
            MATCH (norm:LegalNorm {
                paragraph_nummer: $paragraph,
                norm_doknr: $doknr
            })-[r:HAS_CHUNK]->(chunk:Chunk)
            DELETE r, chunk
        """
        
        with self.driver.session() as session:
            session.run(delete_query, paragraph=para_data['paragraph'], doknr=self.sgb_x_doknr)
        
        # Erstelle neue Chunks
        create_query = """
            MATCH (norm:LegalNorm {
                paragraph_nummer: $paragraph,
                norm_doknr: $doknr
            })
            UNWIND $chunks as chunk_data
            CREATE (chunk:Chunk {
                id: chunk_data.id,
                text: chunk_data.text,
                chunk_index: chunk_data.index
            })
            CREATE (norm)-[:HAS_CHUNK]->(chunk)
            RETURN count(chunk) as chunks_created
        """
        
        chunks_data = [
            {
                'id': f'chunk_sgb_x_{para_data["paragraph"]}_{i}',
                'text': chunk_text,
                'index': i
            }
            for i, chunk_text in enumerate(chunks)
        ]
        
        with self.driver.session() as session:
            result = session.run(
                create_query,
                paragraph=para_data['paragraph'],
                doknr=self.sgb_x_doknr,
                chunks=chunks_data
            )
            record = result.single()
            count = record['chunks_created']
            print(f"   ✅ {count} Chunks erstellt")
            return count
    
    def run_import(self, json_file: str, dry_run: bool = True):
        """Führt vollständigen Import durch"""
        print("\n" + "="*80)
        print("📥 SGB X Import aus JSON - §§ 67-76 für UC14")
        print("="*80)
        
        if dry_run:
            print("\n⚠️  DRY-RUN Modus")
        else:
            print("\n✅ EXECUTE Modus - Daten werden importiert!")
        
        # Lade JSON
        print(f"\n📄 Lade: {json_file}")
        paragraphs = self.load_json(json_file)
        print(f"   ✅ {len(paragraphs)} Paragraphen geladen")
        
        # Importiere jeden Paragraphen
        total_chunks = 0
        imported = 0
        skipped = 0
        
        for para_data in paragraphs:
            paragraph = para_data['paragraph']
            
            print(f"\n📦 Importiere {para_data['enbez']} - {para_data['titel']}")
            
            # Prüfe ob bereits verlinkt
            if self.check_existing_norm(paragraph):
                print(f"   ⚠️  Bereits verlinkt - überspringe")
                skipped += 1
                continue
            
            # Erstelle/Update Norm
            self.create_or_update_norm(para_data, dry_run=dry_run)
            
            # Verlinke mit Document
            self.link_to_document(paragraph, dry_run=dry_run)
            
            # Erstelle Chunks
            chunk_count = self.create_chunks(para_data, dry_run=dry_run)
            total_chunks += chunk_count
            imported += 1
        
        # Zusammenfassung
        print("\n" + "="*80)
        print("📊 Import-Zusammenfassung")
        print("="*80)
        print(f"✅ Importiert: {imported} Paragraphen")
        print(f"⚠️  Übersprungen: {skipped} (bereits vorhanden)")
        print(f"📝 Chunks erstellt: {total_chunks}")
        
        if dry_run:
            print("\n⚠️  Zum Ausführen: --execute")
        else:
            print("\n✅ Import abgeschlossen!")
            print("\nNächster Schritt:")
            print("   python scripts/test_uc10_uc14.py")

def main():
    parser = argparse.ArgumentParser(description='Import SGB X §§ 67-76 aus JSON')
    parser.add_argument('json_file', help='JSON-Datei mit Paragraphen')
    parser.add_argument('--execute', action='store_true', help='Execute import (default: dry-run)')
    parser.add_argument('--dry-run', action='store_true', help='Dry-run only')
    args = parser.parse_args()
    
    if not Path(args.json_file).exists():
        print(f"❌ Datei nicht gefunden: {args.json_file}")
        sys.exit(1)
    
    dry_run = not args.execute
    
    importer = SGBXJSONImporter()
    try:
        importer.run_import(args.json_file, dry_run=dry_run)
    finally:
        importer.close()

if __name__ == '__main__':
    main()
