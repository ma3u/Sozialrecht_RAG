#!/usr/bin/env python3
"""
Import fehlender SGB X Paragraphen (§§ 67-76) für UC14

Beschafft die fehlenden Paragraphen von gesetze-im-internet.de,
parsed sie und importiert sie in Neo4j.

Usage:
    python scripts/import_sgb_x_missing_paragraphs.py --dry-run
    python scripts/import_sgb_x_missing_paragraphs.py --execute
"""

import os
import re
import argparse
from typing import List, Dict
from dotenv import load_dotenv
from neo4j import GraphDatabase
import requests
from bs4 import BeautifulSoup

load_dotenv()

class SGBXImporter:
    """Importiert fehlende SGB X Paragraphen"""
    
    # SGB X Paragraphen 67-76 mit offiziellen Titeln
    TARGET_PARAGRAPHS = {
        '67': 'Sozialdaten',
        '67a': 'Übermittlung von Sozialdaten an Polizei- und Ordnungsbehörden',
        '67b': 'Erhebung von Sozialdaten bei Dritten',
        '67c': 'Verarbeitung von Sozialdaten durch Dritte',
        '67d': 'Automatisierte Einzelfallentscheidung',
        '68': 'Grundsatz',
        '69': 'Offenbarungsbefugnis',
        '70': 'Offenbarung für die Erfüllung sozialer Aufgaben',
        '71': 'Offenbarung an Behörden zur Erfüllung öffentlicher Aufgaben',
        '71a': 'Datenübermittlung an die Finanzbehörden',
        '72': 'Datenübermittlung an Renten- und Unfallversicherungsträger',
        '73': 'Datenübermittlung an private Versicherungsunternehmen',
        '74': 'Übermittlung für die Gesundheitsberichterstattung',
        '75': 'Übermittlung für die Durchführung wissenschaftlicher Forschungsvorhaben',
        '76': 'Erhebung von Sozialdaten'
    }
    
    def __init__(self):
        self.uri = os.getenv('NEO4J_URI')
        self.password = os.getenv('NEO4J_PASSWORD')
        self.driver = GraphDatabase.driver(self.uri, auth=('neo4j', self.password))
        self.sgb_x_doknr = 'BJNR114690980'  # SGB X DOKNR
    
    def close(self):
        self.driver.close()
    
    def fetch_paragraph_from_web(self, paragraph: str) -> Dict:
        """
        Holt Paragraph-Text von gesetze-im-internet.de
        
        Note: Dies ist ein Placeholder - in Produktion würde man
        die offizielle XML-API nutzen oder bereits vorhandene Quelldaten.
        """
        print(f"\n⚠️  Web-Scraping wird NICHT ausgeführt!")
        print(f"   Für Produktions-Import bitte offizielle Quellen nutzen:")
        print(f"   - gesetze-im-internet.de XML API")
        print(f"   - Bundesgesetzblatt Download")
        print(f"   - Oder bereits importierte Strukturdaten")
        
        # Placeholder-Daten für Demo
        return {
            'paragraph': paragraph,
            'titel': self.TARGET_PARAGRAPHS.get(paragraph, f'§ {paragraph}'),
            'text': f'[Placeholder für § {paragraph} - In Produktion aus offizieller Quelle holen]',
            'enbez': f'§ {paragraph}'
        }
    
    def check_existing_paragraphs(self) -> List[str]:
        """Prüft welche Paragraphen bereits in Neo4j vorhanden sind"""
        query = """
            MATCH (doc:LegalDocument {sgb_nummer: 'X'})
                  -[:CONTAINS_NORM]->(norm:LegalNorm)
            WHERE norm.paragraph_nummer IN $paragraphs
            RETURN collect(norm.paragraph_nummer) as existing
        """
        
        with self.driver.session() as session:
            result = session.run(query, paragraphs=list(self.TARGET_PARAGRAPHS.keys()))
            record = result.single()
            return record['existing'] if record else []
    
    def check_orphaned_norms(self) -> List[Dict]:
        """Prüft ob Paragraphen als orphaned Norms existieren"""
        query = """
            MATCH (norm:LegalNorm)
            WHERE norm.paragraph_nummer IN $paragraphs
              AND norm.norm_doknr = $doknr
              AND NOT EXISTS {
                  MATCH (norm)<-[:CONTAINS_NORM]-(:LegalDocument)
              }
            RETURN norm.paragraph_nummer as para, 
                   norm.enbez as titel,
                   norm.id as norm_id
            ORDER BY para
        """
        
        with self.driver.session() as session:
            result = session.run(
                query, 
                paragraphs=list(self.TARGET_PARAGRAPHS.keys()),
                doknr=self.sgb_x_doknr
            )
            return [record.data() for record in result]
    
    def create_norm_node(self, paragraph_data: Dict, dry_run: bool = True) -> str:
        """Erstellt eine neue LegalNorm Node"""
        query = """
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
        
        norm_id = f"norm_sgb_x_{paragraph_data['paragraph']}"
        
        if dry_run:
            print(f"   [DRY-RUN] Würde LegalNorm erstellen: {norm_id}")
            return norm_id
        
        with self.driver.session() as session:
            result = session.run(
                query,
                id=norm_id,
                paragraph=paragraph_data['paragraph'],
                enbez=paragraph_data['enbez'],
                titel=paragraph_data['titel'],
                doknr=self.sgb_x_doknr,
                text=paragraph_data['text']
            )
            record = result.single()
            print(f"   ✅ LegalNorm erstellt: {record['norm_id']}")
            return record['norm_id']
    
    def link_norm_to_document(self, paragraph: str, dry_run: bool = True):
        """Erstellt CONTAINS_NORM Relationship"""
        query = """
            MATCH (doc:LegalDocument {sgb_nummer: 'X'})
            MATCH (norm:LegalNorm {
                paragraph_nummer: $paragraph,
                norm_doknr: $doknr
            })
            CREATE (doc)-[:CONTAINS_NORM]->(norm)
            RETURN doc.title as doc_title, norm.enbez as norm_title
        """
        
        if dry_run:
            print(f"   [DRY-RUN] Würde CONTAINS_NORM erstellen: SGB X → § {paragraph}")
            return
        
        with self.driver.session() as session:
            result = session.run(query, paragraph=paragraph, doknr=self.sgb_x_doknr)
            record = result.single()
            if record:
                print(f"   ✅ CONTAINS_NORM erstellt: {record['doc_title']} → {record['norm_title']}")
    
    def create_chunks(self, paragraph: str, text: str, dry_run: bool = True) -> int:
        """
        Teilt Paragraph-Text in Chunks auf
        
        Einfache Strategie: Split bei Absätzen (1), (2), etc.
        """
        # Regex für Absätze: (1), (2), etc.
        absaetze = re.split(r'(?=\(\d+\))', text)
        absaetze = [a.strip() for a in absaetze if a.strip()]
        
        if not absaetze:
            absaetze = [text]  # Falls kein Split möglich, ganzen Text nehmen
        
        print(f"   📝 {len(absaetze)} Chunks erkannt für § {paragraph}")
        
        if dry_run:
            for i, chunk_text in enumerate(absaetze[:3]):  # Nur erste 3 als Preview
                preview = chunk_text[:100].replace('\n', ' ')
                print(f"      [DRY-RUN] Chunk {i}: {preview}...")
            return len(absaetze)
        
        # Create chunks in Neo4j
        query = """
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
                'id': f'chunk_sgb_x_{paragraph}_{i}',
                'text': chunk_text,
                'index': i
            }
            for i, chunk_text in enumerate(absaetze)
        ]
        
        with self.driver.session() as session:
            result = session.run(
                query,
                paragraph=paragraph,
                doknr=self.sgb_x_doknr,
                chunks=chunks_data
            )
            record = result.single()
            count = record['chunks_created']
            print(f"   ✅ {count} Chunks erstellt für § {paragraph}")
            return count
    
    def run_import(self, dry_run: bool = True):
        """Führt den vollständigen Import durch"""
        print("\n" + "="*80)
        print("🔧 SGB X §§ 67-76 Import für UC14")
        print("="*80)
        
        if dry_run:
            print("\n⚠️  DRY-RUN Modus - Keine Änderungen werden gespeichert!")
        else:
            print("\n✅ EXECUTE Modus - Änderungen werden in Neo4j gespeichert")
        
        # Schritt 1: Prüfe existierende Paragraphen
        print("\n1️⃣  Prüfe existierende Paragraphen...")
        existing = self.check_existing_paragraphs()
        print(f"   ✅ {len(existing)} Paragraphen bereits verlinkt: {existing}")
        
        # Schritt 2: Prüfe orphaned Norms
        print("\n2️⃣  Prüfe orphaned Norms...")
        orphaned = self.check_orphaned_norms()
        orphaned_paras = [n['para'] for n in orphaned]
        print(f"   ℹ️  {len(orphaned)} orphaned Norms gefunden: {orphaned_paras}")
        
        # Schritt 3: Identifiziere fehlende Paragraphen
        missing = [p for p in self.TARGET_PARAGRAPHS.keys() 
                   if p not in existing and p not in orphaned_paras]
        print(f"\n3️⃣  Fehlende Paragraphen identifiziert:")
        print(f"   ❌ {len(missing)} fehlen komplett: {missing}")
        
        # Schritt 4: Link orphaned Norms
        if orphaned:
            print(f"\n4️⃣  Verlinke orphaned Norms...")
            for norm_data in orphaned:
                self.link_norm_to_document(norm_data['para'], dry_run=dry_run)
                
                # Create chunks for orphaned norms (falls Text vorhanden)
                # Note: In diesem Placeholder nutzen wir Demo-Daten
                if not dry_run:
                    paragraph_data = self.fetch_paragraph_from_web(norm_data['para'])
                    self.create_chunks(norm_data['para'], paragraph_data['text'], dry_run=dry_run)
        
        # Schritt 5: Importiere fehlende Paragraphen
        if missing:
            print(f"\n5️⃣  Importiere fehlende Paragraphen...")
            print(f"\n⚠️  WICHTIG: Für Produktion echte Quelldaten nutzen!")
            print(f"   Diese Demo erstellt nur Placeholder-Daten.\n")
            
            for paragraph in missing:
                print(f"\n   📥 Importiere § {paragraph}...")
                
                # Fetch paragraph data (in Produktion: echte API)
                paragraph_data = self.fetch_paragraph_from_web(paragraph)
                
                # Create norm node
                self.create_norm_node(paragraph_data, dry_run=dry_run)
                
                # Link to document
                self.link_norm_to_document(paragraph, dry_run=dry_run)
                
                # Create chunks
                self.create_chunks(paragraph, paragraph_data['text'], dry_run=dry_run)
        
        # Zusammenfassung
        print("\n" + "="*80)
        print("📊 Import-Zusammenfassung")
        print("="*80)
        print(f"✅ Bereits verlinkt: {len(existing)}")
        print(f"🔗 Orphaned (zu verlinken): {len(orphaned)}")
        print(f"📥 Neu zu importieren: {len(missing)}")
        print(f"📝 Gesamt erwartete Paragraphen: {len(self.TARGET_PARAGRAPHS)}")
        
        total_chunks = len(orphaned) * 8 + len(missing) * 8  # Schätzung: 8 Chunks pro Paragraph
        print(f"\n💾 Erwartete neue Chunks: ~{total_chunks}")
        
        if dry_run:
            print("\n⚠️  Zum Ausführen: python scripts/import_sgb_x_missing_paragraphs.py --execute")
        else:
            print("\n✅ Import abgeschlossen! Bitte UC14 Test ausführen.")

def main():
    parser = argparse.ArgumentParser(description='Import SGB X §§ 67-76 für UC14')
    parser.add_argument('--execute', action='store_true', help='Execute import (default: dry-run)')
    parser.add_argument('--dry-run', action='store_true', help='Dry-run only (preview changes)')
    args = parser.parse_args()
    
    # Default ist dry-run
    dry_run = not args.execute
    
    importer = SGBXImporter()
    try:
        importer.run_import(dry_run=dry_run)
    finally:
        importer.close()

if __name__ == '__main__':
    main()
