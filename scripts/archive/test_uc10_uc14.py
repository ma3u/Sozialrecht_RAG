#!/usr/bin/env python3
"""
Test UC10 (Widerspruch) und UC14 (Datenschutz) nach SGB X Import

Prüft:
1. UC10: Widerspruchsverfahren (§§ 79, 80, 84, 85)
2. UC14: Datenschutz-Compliance (§§ 67-85)
3. Chunk-Qualität und Verfügbarkeit
4. Cypher-Queries für beide Use Cases
"""

import os
from dotenv import load_dotenv
from neo4j import GraphDatabase

load_dotenv()

class UC10UC14Tester:
    def __init__(self):
        self.uri = os.getenv('NEO4J_URI')
        self.password = os.getenv('NEO4J_PASSWORD')
        self.driver = GraphDatabase.driver(self.uri, auth=('neo4j', self.password))
    
    def close(self):
        self.driver.close()
    
    def test_uc10_widerspruch(self):
        """UC10: Widerspruchsverfahren - SGB X §§ 79, 80, 84, 85"""
        print("\n" + "="*80)
        print("🔍 UC10: Widerspruch bearbeiten")
        print("="*80)
        
        query = """
            MATCH (doc:LegalDocument {sgb_nummer: 'X'})
                  -[:CONTAINS_NORM]->(norm:LegalNorm)
            WHERE norm.paragraph_nummer IN ['79', '80', '84', '85']
            OPTIONAL MATCH (norm)-[:HAS_CHUNK]->(chunk:Chunk)
            WITH norm, 
                 count(chunk) as chunk_count,
                 collect(chunk.text)[0..2] as sample_chunks
            RETURN 
                norm.paragraph_nummer as paragraph,
                norm.enbez as titel,
                chunk_count,
                [c IN sample_chunks | substring(c, 0, 150) + '...'] as beispiele
            ORDER BY norm.paragraph_nummer
        """
        
        with self.driver.session() as session:
            result = session.run(query)
            records = list(result)
            
            if not records:
                print("❌ FAIL: Keine SGB X Normen gefunden!")
                return False
            
            print(f"\n✅ {len(records)} Normen gefunden für Widerspruchsverfahren:\n")
            
            total_chunks = 0
            for record in records:
                chunks = record['chunk_count']
                total_chunks += chunks
                status = "✅" if chunks > 0 else "⚠️"
                print(f"{status} {record['titel']} ({record['paragraph']}): {chunks} Chunks")
                
                if chunks > 0 and record['beispiele']:
                    print(f"   Beispiel: {record['beispiele'][0][:120]}...")
            
            print(f"\n📊 Gesamt: {total_chunks} Chunks über {len(records)} Normen")
            
            # Erfolgskriterien
            success = len(records) >= 4 and total_chunks >= 20
            if success:
                print("✅ UC10 PASS: Widerspruchsverfahren funktionsfähig!")
            else:
                print(f"⚠️ UC10 PARTIAL: {total_chunks}/20+ Chunks vorhanden")
            
            return success
    
    def test_uc14_datenschutz(self):
        """UC14: Datenschutz-Compliance - SGB X §§ 67-85"""
        print("\n" + "="*80)
        print("🔒 UC14: Compliance-Check Datenschutz")
        print("="*80)
        
        query = """
            MATCH (doc:LegalDocument {sgb_nummer: 'X'})
                  -[:CONTAINS_NORM]->(norm:LegalNorm)
            WHERE toInteger(norm.paragraph_nummer) >= 67 
              AND toInteger(norm.paragraph_nummer) <= 85
            OPTIONAL MATCH (norm)-[:HAS_CHUNK]->(chunk:Chunk)
            WHERE chunk.text CONTAINS 'Sozialdaten' 
               OR chunk.text CONTAINS 'Datenschutz'
               OR chunk.text CONTAINS 'personenbezogen'
               OR chunk.text CONTAINS 'Geheimnis'
            RETURN 
                norm.paragraph_nummer as paragraph,
                norm.enbez as titel,
                count(DISTINCT chunk) as relevante_chunks
            ORDER BY toInteger(norm.paragraph_nummer)
        """
        
        with self.driver.session() as session:
            result = session.run(query)
            records = list(result)
            
            if not records:
                print("❌ FAIL: Keine Datenschutz-Normen (§§ 67-85) gefunden!")
                return False
            
            print(f"\n✅ {len(records)} Datenschutz-Normen gefunden:\n")
            
            total_chunks = 0
            key_paragraphs = ['67', '68', '69', '76', '78', '79']
            key_found = []
            
            for record in records:
                chunks = record['relevante_chunks']
                total_chunks += chunks
                para = record['paragraph']
                
                if para in key_paragraphs:
                    key_found.append(para)
                
                status = "✅" if chunks > 0 else "⚪"
                print(f"{status} {record['titel']} ({para}): {chunks} Chunks")
            
            print(f"\n📊 Gesamt: {total_chunks} relevante Datenschutz-Chunks")
            print(f"🎯 Kern-Paragraphen gefunden: {len(key_found)}/6")
            print(f"   {', '.join(['§' + p for p in key_found])}")
            
            # Erfolgskriterien
            success = len(key_found) >= 4 and total_chunks >= 10
            if success:
                print("✅ UC14 PASS: Datenschutz-Compliance funktionsfähig!")
            else:
                print(f"⚠️ UC14 PARTIAL: Nicht alle Kern-Paragraphen verfügbar")
            
            return success
    
    def test_sgb_x_coverage(self):
        """Prüfe generelle SGB X Verfügbarkeit"""
        print("\n" + "="*80)
        print("📚 SGB X Gesamtabdeckung")
        print("="*80)
        
        query = """
            MATCH (doc:LegalDocument {sgb_nummer: 'X'})
                  -[:CONTAINS_NORM]->(norm:LegalNorm)
            OPTIONAL MATCH (norm)-[:HAS_CHUNK]->(chunk:Chunk)
            WITH count(DISTINCT norm) as norm_count,
                 count(DISTINCT chunk) as chunk_count,
                 count(DISTINCT CASE WHEN chunk IS NOT NULL THEN norm END) as norms_with_chunks
            RETURN 
                norm_count,
                chunk_count,
                norms_with_chunks,
                toFloat(norms_with_chunks) / norm_count * 100 as coverage_percent
        """
        
        with self.driver.session() as session:
            result = session.run(query)
            record = result.single()
            
            if not record or record['norm_count'] == 0:
                print("❌ SGB X nicht in Datenbank!")
                return False
            
            norms = record['norm_count']
            chunks = record['chunk_count']
            coverage = record['coverage_percent']
            
            print(f"\n📖 Normen: {norms}")
            print(f"📄 Chunks: {chunks}")
            print(f"📊 Coverage: {coverage:.1f}% der Normen haben Chunks")
            
            if chunks > 0:
                print(f"✅ SGB X ist verfügbar!")
                return True
            else:
                print("⚠️ SGB X Normen vorhanden, aber keine Chunks")
                return False
    
    def run_all_tests(self):
        """Führe alle Tests aus"""
        print("\n" + "="*80)
        print("🧪 UC10 & UC14 Test Suite - SGB X Verfügbarkeit")
        print("="*80)
        
        # Test 1: SGB X Verfügbarkeit
        sgb_x_available = self.test_sgb_x_coverage()
        
        if not sgb_x_available:
            print("\n❌ SGB X nicht verfügbar - Tests abgebrochen")
            return
        
        # Test 2: UC10 Widerspruch
        uc10_pass = self.test_uc10_widerspruch()
        
        # Test 3: UC14 Datenschutz
        uc14_pass = self.test_uc14_datenschutz()
        
        # Zusammenfassung
        print("\n" + "="*80)
        print("📊 TEST ZUSAMMENFASSUNG")
        print("="*80)
        print(f"{'✅' if sgb_x_available else '❌'} SGB X Verfügbarkeit")
        print(f"{'✅' if uc10_pass else '⚠️'} UC10: Widerspruchsverfahren")
        print(f"{'✅' if uc14_pass else '⚠️'} UC14: Datenschutz-Compliance")
        
        if uc10_pass and uc14_pass:
            print("\n🎉 ERFOLG: Beide Use Cases sind funktionsfähig!")
            print("\nNächste Schritte:")
            print("1. ✅ UC10: Widerspruchsverfahren in Produktion testen")
            print("2. ✅ UC14: Datenschutz-Compliance prüfen")
            print("3. 📝 Use Cases in MVP-Roadmap aufnehmen")
        elif uc10_pass or uc14_pass:
            print("\n⚠️ PARTIAL: Mindestens ein Use Case funktionsfähig")
            print("→ Daten für beide Use Cases vorhanden, aber teilweise eingeschränkt")
        else:
            print("\n❌ FAIL: Use Cases nicht funktionsfähig")
            print("→ Phase 1 Reparatur erforderlich")

if __name__ == '__main__':
    tester = UC10UC14Tester()
    try:
        tester.run_all_tests()
    finally:
        tester.close()
