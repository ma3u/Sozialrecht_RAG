#!/usr/bin/env python3
"""
Evaluate Graph Quality for 20 Sachbearbeiter Use Cases
Tests real-world case worker scenarios and measures connection quality
"""

import sys
import os
from pathlib import Path
import time
from typing import Dict, List, Tuple

sys.path.insert(0, str(Path(__file__).parent.parent))

from neo4j import GraphDatabase
from dotenv import load_dotenv
import json

load_dotenv()


class SachbearbeiterUseCaseEvaluator:
    """Evaluate graph quality for real case worker scenarios"""
    
    def __init__(self):
        self.uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        self.username = os.getenv("NEO4J_USERNAME", "neo4j")
        self.password = os.getenv("NEO4J_PASSWORD")
        
        self.driver = GraphDatabase.driver(self.uri, auth=(self.username, self.password))
        self.results = []
        
    def close(self):
        self.driver.close()
    
    def evaluate_use_case(self, name: str, query: str, expected_min: int = 1, 
                         description: str = "") -> Dict:
        """Evaluate a single use case"""
        print(f"\n{'='*70}")
        print(f"USE CASE: {name}")
        print(f"{'='*70}")
        print(f"📋 {description}")
        
        start = time.time()
        
        with self.driver.session() as session:
            try:
                result = session.run(query)
                records = list(result)
                elapsed = time.time() - start
                
                # Evaluate quality
                found = len(records)
                quality_score = min(100, (found / expected_min * 100)) if expected_min > 0 else 100
                
                status = "✅" if found >= expected_min else "❌"
                speed_status = "🚀" if elapsed < 0.1 else "⚡" if elapsed < 0.5 else "⏱️"
                
                result_data = {
                    'use_case': name,
                    'description': description,
                    'found': found,
                    'expected_min': expected_min,
                    'quality_score': quality_score,
                    'time_ms': elapsed * 1000,
                    'status': 'PASS' if found >= expected_min else 'FAIL',
                    'records': records[:5]  # Sample of results
                }
                
                self.results.append(result_data)
                
                print(f"\n{status} Found: {found} results (expected min: {expected_min})")
                print(f"{speed_status} Time: {elapsed*1000:.2f}ms")
                print(f"📊 Quality Score: {quality_score:.1f}%")
                
                # Show sample results
                if records:
                    print(f"\n📄 Sample Results:")
                    for i, r in enumerate(records[:3], 1):
                        print(f"   {i}. {dict(r)}")
                
                return result_data
                
            except Exception as e:
                print(f"\n❌ Query Failed: {e}")
                self.results.append({
                    'use_case': name,
                    'status': 'ERROR',
                    'error': str(e)
                })
                return {'status': 'ERROR'}
    
    # === GRUNDSICHERUNG FÜR ARBEITSUCHENDE (SGB II) ===
    
    def uc01_regelbedarf_ermitteln(self):
        """UC01: Regelbedarf ermitteln (§ 20 SGB II)"""
        return self.evaluate_use_case(
            "UC01: Regelbedarf ermitteln",
            """
            MATCH (doc:LegalDocument {sgb_nummer: "II"})
                  -[:CONTAINS_NORM]->(norm:LegalNorm {paragraph_nummer: "20"})
            OPTIONAL MATCH (norm)-[:HAS_CHUNK]->(chunk:Chunk)
            RETURN norm.enbez as paragraph,
                   norm.titel as titel,
                   count(chunk) as chunks,
                   norm.content_text as text
            """,
            expected_min=1,
            description="Sachbearbeiter muss Regelbedarf für Alleinstehende/Familie prüfen"
        )
    
    def uc02_leistungsberechtigung_pruefen(self):
        """UC02: Leistungsberechtigung prüfen (§§ 7-9 SGB II)"""
        return self.evaluate_use_case(
            "UC02: Leistungsberechtigung prüfen",
            """
            MATCH (doc:LegalDocument {sgb_nummer: "II"})
                  -[:CONTAINS_NORM]->(norm:LegalNorm)
            WHERE norm.paragraph_nummer IN ["7", "8", "9"]
            OPTIONAL MATCH (norm)-[:HAS_CONTENT]->(text:TextUnit)
            RETURN norm.paragraph_nummer as para_nr,
                   norm.enbez as paragraph,
                   norm.titel as pruefpunkt,
                   count(text) as text_units
            ORDER BY para_nr
            """,
            expected_min=3,
            description="Prüfung: Alter (15-67), Erwerbsfähigkeit (3h/Tag), Hilfebedürftigkeit"
        )
    
    def uc03_einkommen_berechnen(self):
        """UC03: Einkommen anrechnen (§ 11 SGB II)"""
        return self.evaluate_use_case(
            "UC03: Einkommen berechnen",
            """
            MATCH (doc:LegalDocument {sgb_nummer: "II"})
                  -[:CONTAINS_NORM]->(norm:LegalNorm)
            WHERE norm.paragraph_nummer STARTS WITH "11"
            RETURN norm.paragraph_nummer as para,
                   norm.titel as thema,
                   norm.enbez as paragraph
            ORDER BY para
            """,
            expected_min=5,
            description="Einkommensanrechnung inkl. § 11a (Freibeträge), § 11b (Absetzbeträge)"
        )
    
    def uc04_vermoegen_pruefen(self):
        """UC04: Vermögen prüfen (§ 12 SGB II)"""
        return self.evaluate_use_case(
            "UC04: Vermögen prüfen",
            """
            MATCH (doc:LegalDocument {sgb_nummer: "II"})
                  -[:CONTAINS_NORM]->(norm:LegalNorm)
            WHERE norm.paragraph_nummer IN ["12", "12a"]
            OPTIONAL MATCH (norm)-[:HAS_CHUNK]->(chunk:Chunk)
            RETURN norm.paragraph_nummer as para,
                   norm.titel as titel,
                   count(chunk) as chunks
            """,
            expected_min=1,
            description="Vermögensprüfung und Freibeträge"
        )
    
    def uc05_mehrbedarf_alleinerziehende(self):
        """UC05: Mehrbedarf für Alleinerziehende (§ 21 SGB II)"""
        return self.evaluate_use_case(
            "UC05: Mehrbedarf Alleinerziehende",
            """
            MATCH (doc:LegalDocument {sgb_nummer: "II"})
                  -[:CONTAINS_NORM]->(norm:LegalNorm)
            WHERE norm.paragraph_nummer STARTS WITH "21"
            RETURN norm.paragraph_nummer as para,
                   norm.titel as mehrbedarf_typ
            ORDER BY para
            """,
            expected_min=2,
            description="Mehrbedarfe: Alleinerziehende, Behinderung, kostenaufwändige Ernährung"
        )
    
    def uc06_kosten_unterkunft(self):
        """UC06: Kosten der Unterkunft (§ 22 SGB II)"""
        return self.evaluate_use_case(
            "UC06: Kosten der Unterkunft",
            """
            MATCH (doc:LegalDocument {sgb_nummer: "II"})
                  -[:CONTAINS_NORM]->(norm:LegalNorm)
            WHERE norm.paragraph_nummer STARTS WITH "22"
            OPTIONAL MATCH (norm)-[:HAS_CHUNK]->(chunk:Chunk)
            RETURN norm.paragraph_nummer as para,
                   norm.titel as titel,
                   count(chunk) as chunks
            """,
            expected_min=1,
            description="Mietkosten, Heizkosten, Warmwasser"
        )
    
    def uc07_sanktionen_pflichtverletzung(self):
        """UC07: Sanktionen bei Pflichtverletzung (§§ 31-32 SGB II)"""
        return self.evaluate_use_case(
            "UC07: Sanktionen prüfen",
            """
            MATCH (doc:LegalDocument {sgb_nummer: "II"})
                  -[:CONTAINS_NORM]->(norm:LegalNorm)
            WHERE norm.paragraph_nummer IN ["31", "31a", "31b", "32"]
            RETURN norm.paragraph_nummer as para,
                   norm.titel as sanktion_typ
            ORDER BY para
            """,
            expected_min=3,
            description="Pflichtverletzungen und Minderung der Leistung"
        )
    
    def uc08_eingliederungsvereinbarung(self):
        """UC08: Eingliederungsvereinbarung (§ 15 SGB II)"""
        return self.evaluate_use_case(
            "UC08: Eingliederungsvereinbarung",
            """
            MATCH (doc:LegalDocument {sgb_nummer: "II"})
                  -[:CONTAINS_NORM]->(norm:LegalNorm {paragraph_nummer: "15"})
            OPTIONAL MATCH (norm)-[:HAS_CONTENT]->(text:TextUnit)
            RETURN norm.enbez as paragraph,
                   norm.titel as titel,
                   count(text) as text_units
            """,
            expected_min=1,
            description="EGV-Abschluss und Pflichten des Leistungsberechtigten"
        )
    
    def uc09_arbeitslosengeld_anspruch(self):
        """UC09: Arbeitslosengeld I prüfen (§§ 136-150 SGB III)"""
        return self.evaluate_use_case(
            "UC09: ALG I Anspruchsprüfung",
            """
            MATCH (doc:LegalDocument {sgb_nummer: "III"})
                  -[:CONTAINS_NORM]->(norm:LegalNorm)
            WHERE norm.paragraph_nummer IN ["136", "137", "138", "142", "143"]
            RETURN norm.paragraph_nummer as para,
                   norm.titel as titel
            ORDER BY para
            """,
            expected_min=2,
            description="Anspruchsvoraussetzungen für ALG I (Arbeitslosigkeit, Verfügbarkeit)"
        )
    
    def uc10_antrag_zustaendigkeit(self):
        """UC10: Zuständigkeit und Antrag (§§ 37, 40 SGB II)"""
        return self.evaluate_use_case(
            "UC10: Zuständigkeit klären",
            """
            MATCH (doc:LegalDocument {sgb_nummer: "II"})
                  -[:CONTAINS_NORM]->(norm:LegalNorm)
            WHERE norm.paragraph_nummer IN ["37", "37a", "37b", "37c", "40", "40a"]
            RETURN norm.paragraph_nummer as para,
                   norm.titel as titel
            ORDER BY para
            """,
            expected_min=2,
            description="Örtliche Zuständigkeit und Antragserfordernis"
        )
    
    # === CROSS-SGB USE CASES ===
    
    def uc11_krankenversicherung_pflicht(self):
        """UC11: Krankenversicherungspflicht (§ 5 SGB V)"""
        return self.evaluate_use_case(
            "UC11: Krankenversicherung",
            """
            MATCH (doc:LegalDocument {sgb_nummer: "V"})
                  -[:CONTAINS_NORM]->(norm:LegalNorm {paragraph_nummer: "5"})
            OPTIONAL MATCH (norm)-[:HAS_CHUNK]->(chunk:Chunk)
            RETURN norm.enbez as paragraph,
                   norm.titel as titel,
                   count(chunk) as chunks
            """,
            expected_min=1,
            description="KV-Pflicht für Leistungsbezieher"
        )
    
    def uc12_rentenversicherung_pruefen(self):
        """UC12: Rentenversicherung (§§ 1-4 SGB VI)"""
        return self.evaluate_use_case(
            "UC12: Rentenversicherung",
            """
            MATCH (doc:LegalDocument {sgb_nummer: "VI"})
                  -[:CONTAINS_NORM]->(norm:LegalNorm)
            WHERE norm.paragraph_nummer IN ["1", "2", "3", "4"]
            RETURN norm.paragraph_nummer as para,
                   norm.titel as titel
            ORDER BY para
            """,
            expected_min=2,
            description="Versicherungspflicht und Beiträge"
        )
    
    def uc13_rehabilitation_leistungen(self):
        """UC13: Rehabilitation (SGB IX)"""
        return self.evaluate_use_case(
            "UC13: Rehabilitation",
            """
            MATCH (doc:LegalDocument {sgb_nummer: "IX"})
                  -[:CONTAINS_NORM]->(norm:LegalNorm)
            WHERE norm.paragraph_nummer IN ["1", "2", "3", "4", "5"]
            RETURN norm.paragraph_nummer as para,
                   norm.titel as titel
            ORDER BY para
            """,
            expected_min=2,
            description="Teilhabe und Rehabilitation behinderter Menschen"
        )
    
    def uc14_sozialhilfe_grundsicherung(self):
        """UC14: Sozialhilfe (§§ 27-29 SGB XII)"""
        return self.evaluate_use_case(
            "UC14: Sozialhilfe",
            """
            MATCH (doc:LegalDocument {sgb_nummer: "XII"})
                  -[:CONTAINS_NORM]->(norm:LegalNorm)
            WHERE norm.paragraph_nummer IN ["27", "28", "29"]
            RETURN norm.paragraph_nummer as para,
                   norm.titel as leistungsart
            ORDER BY para
            """,
            expected_min=1,
            description="Hilfe zum Lebensunterhalt für nicht Erwerbsfähige"
        )
    
    def uc15_datenschutz_sozialdaten(self):
        """UC15: Datenschutz (§§ 67-85 SGB X)"""
        return self.evaluate_use_case(
            "UC15: Sozialdatenschutz",
            """
            MATCH (doc:LegalDocument {sgb_nummer: "X"})
                  -[:CONTAINS_NORM]->(norm:LegalNorm)
            WHERE norm.paragraph_nummer IN ["67", "67a", "67b", "68", "69"]
            RETURN norm.paragraph_nummer as para,
                   norm.titel as datenschutz_regel
            ORDER BY para
            """,
            expected_min=2,
            description="Schutz von Sozialdaten bei Antragsbearbeitung"
        )
    
    # === WORKFLOW USE CASES ===
    
    def uc16_kompletter_buergergeld_antrag(self):
        """UC16: Kompletter Bürgergeld-Antrag Workflow"""
        return self.evaluate_use_case(
            "UC16: Vollständiger Antrag",
            """
            MATCH (doc:LegalDocument {sgb_nummer: "II"})
                  -[:CONTAINS_NORM]->(norm:LegalNorm)
            WHERE norm.paragraph_nummer IN [
                "7", "8", "9",     // Berechtigung
                "11", "12",        // Einkommen & Vermögen
                "20", "21", "22",  // Bedarf
                "37", "40"         // Zuständigkeit & Antrag
            ]
            RETURN norm.paragraph_nummer as para,
                   norm.titel as pruefschritt
            ORDER BY 
                CASE norm.paragraph_nummer
                    WHEN "7" THEN 1 WHEN "8" THEN 2 WHEN "9" THEN 3
                    WHEN "11" THEN 4 WHEN "12" THEN 5
                    WHEN "20" THEN 6 WHEN "21" THEN 7 WHEN "22" THEN 8
                    WHEN "37" THEN 9 WHEN "40" THEN 10
                END
            """,
            expected_min=8,
            description="Alle Prüfschritte für Bürgergeld-Antrag"
        )
    
    def uc17_hierarchische_navigation(self):
        """UC17: Hierarchische Navigation durch SGB II"""
        return self.evaluate_use_case(
            "UC17: Strukturnavigation",
            """
            MATCH (doc:LegalDocument {sgb_nummer: "II"})
                  -[:HAS_STRUCTURE]->(struct:StructuralUnit)
                  -[:CONTAINS_NORM]->(norm:LegalNorm)
            RETURN struct.gliederungsbez as struktur,
                   struct.gliederungstitel as titel,
                   count(norm) as anzahl_normen
            ORDER BY struct.order_index
            LIMIT 10
            """,
            expected_min=5,
            description="Navigation durch Kapitel und Abschnitte"
        )
    
    def uc18_semantic_search_regelbedarfe(self):
        """UC18: Semantische Suche 'Regelbedarfe'"""
        return self.evaluate_use_case(
            "UC18: Semantische Suche",
            """
            MATCH (chunk:Chunk)
            WHERE chunk.paragraph_context CONTAINS "Regelbedarf"
               OR chunk.text CONTAINS "Regelbedarf"
            OPTIONAL MATCH (norm:LegalNorm)-[:HAS_CHUNK]->(chunk)
            RETURN DISTINCT norm.enbez as paragraph,
                   norm.titel as titel,
                   count(chunk) as relevante_chunks
            ORDER BY relevante_chunks DESC
            LIMIT 5
            """,
            expected_min=1,
            description="Textsuche über alle Chunks zu 'Regelbedarfe'"
        )
    
    def uc19_handlungsanweisungen_verknuepfung(self):
        """UC19: Handlungsanweisungen zu SGB II"""
        return self.evaluate_use_case(
            "UC19: Fachliche Weisungen",
            """
            MATCH (d:Document)
            WHERE d.document_type = "Fachliche Weisung"
              AND (d.sgb_nummer = "II" OR d.filename CONTAINS "SGB")
            OPTIONAL MATCH (d)-[:HAS_CHUNK]->(c:Chunk)
            RETURN d.filename as dokument,
                   d.trust_score as vertrauenswuerdigkeit,
                   count(c) as chunks
            ORDER BY d.trust_score DESC
            LIMIT 5
            """,
            expected_min=1,
            description="PDF-Handlungsanweisungen mit Verknüpfung zum Gesetzestext"
        )
    
    def uc20_aenderungen_nachvollziehen(self):
        """UC20: Gesetzesänderungen nachvollziehen"""
        return self.evaluate_use_case(
            "UC20: Änderungshistorie",
            """
            MATCH (norm:LegalNorm)-[:HAS_AMENDMENT]->(amendment:Amendment)
            MATCH (doc:LegalDocument {sgb_nummer: "II"})-[:CONTAINS_NORM]->(norm)
            WHERE amendment.amendment_date IS NOT NULL
            RETURN norm.enbez as paragraph,
                   norm.titel as titel,
                   amendment.standkommentar as aenderung,
                   amendment.amendment_date as datum
            ORDER BY amendment.amendment_date DESC
            LIMIT 10
            """,
            expected_min=1,
            description="BGBl-Änderungen mit Datum nachvollziehen"
        )
    
    def run_all_evaluations(self):
        """Run all 20 use case evaluations"""
        print("\n" + "="*70)
        print("SACHBEARBEITER USE CASE EVALUATION")
        print("20 Real-World Scenarios for Case Workers")
        print("="*70)
        
        # === GRUNDSICHERUNG (SGB II) ===
        print("\n\n🏛️  GRUNDSICHERUNG FÜR ARBEITSUCHENDE (SGB II)")
        print("="*70)
        
        self.uc01_regelbedarf_ermitteln()
        self.uc02_leistungsberechtigung_pruefen()
        self.uc03_einkommen_berechnen()
        self.uc04_vermoegen_pruefen()
        self.uc05_mehrbedarf_alleinerziehende()
        self.uc06_kosten_unterkunft()
        self.uc07_sanktionen_pflichtverletzung()
        self.uc08_eingliederungsvereinbarung()
        
        # === CROSS-SGB ===
        print("\n\n🔗 CROSS-SGB USE CASES")
        print("="*70)
        
        self.uc09_arbeitslosengeld_anspruch()
        self.uc10_antrag_zustaendigkeit()
        self.uc11_krankenversicherung_pflicht()
        self.uc12_rentenversicherung_pruefen()
        self.uc13_rehabilitation_leistungen()
        self.uc14_sozialhilfe_grundsicherung()
        self.uc15_datenschutz_sozialdaten()
        
        # === WORKFLOW ===
        print("\n\n⚙️  WORKFLOW & INTEGRATION")
        print("="*70)
        
        self.uc16_kompletter_buergergeld_antrag()
        self.uc17_hierarchische_navigation()
        self.uc18_semantic_search_regelbedarfe()
        self.uc19_handlungsanweisungen_verknuepfung()
        self.uc20_aenderungen_nachvollziehen()
        
        # Generate summary
        self.generate_summary()
    
    def generate_summary(self):
        """Generate evaluation summary"""
        print("\n\n" + "="*70)
        print("📊 EVALUATION SUMMARY")
        print("="*70)
        
        passed = sum(1 for r in self.results if r.get('status') == 'PASS')
        failed = sum(1 for r in self.results if r.get('status') == 'FAIL')
        errors = sum(1 for r in self.results if r.get('status') == 'ERROR')
        
        total = len(self.results)
        pass_rate = (passed / total * 100) if total > 0 else 0
        
        avg_quality = sum(r.get('quality_score', 0) for r in self.results if 'quality_score' in r) / total if total > 0 else 0
        avg_time = sum(r.get('time_ms', 0) for r in self.results if 'time_ms' in r) / total if total > 0 else 0
        
        print(f"\n📈 Overall Results:")
        print(f"   Total Use Cases: {total}")
        print(f"   ✅ Passed: {passed}")
        print(f"   ❌ Failed: {failed}")
        print(f"   ⚠️  Errors: {errors}")
        print(f"   Pass Rate: {pass_rate:.1f}%")
        
        print(f"\n⚡ Performance:")
        print(f"   Average Quality Score: {avg_quality:.1f}%")
        print(f"   Average Query Time: {avg_time:.2f}ms")
        
        # Failed cases
        if failed > 0 or errors > 0:
            print(f"\n❌ Failed/Error Cases:")
            for r in self.results:
                if r.get('status') in ['FAIL', 'ERROR']:
                    print(f"   - {r['use_case']}: {r.get('error', 'Not enough results')}")
        
        # Save report
        output_file = Path(__file__).parent.parent / "logs" / "sachbearbeiter_evaluation.json"
        output_file.parent.mkdir(exist_ok=True)
        
        with open(output_file, 'w') as f:
            json.dump({
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
                'summary': {
                    'total': total,
                    'passed': passed,
                    'failed': failed,
                    'errors': errors,
                    'pass_rate': pass_rate,
                    'avg_quality': avg_quality,
                    'avg_time_ms': avg_time
                },
                'results': self.results
            }, f, indent=2, default=str)
        
        print(f"\n💾 Detailed report saved to: {output_file}")
        
        # Overall assessment
        print("\n" + "="*70)
        if pass_rate >= 90:
            print("🎉 EXCELLENT: Graph connections are production-ready!")
        elif pass_rate >= 75:
            print("✅ GOOD: Graph connections work well, minor improvements possible")
        elif pass_rate >= 50:
            print("⚠️  FAIR: Graph connections need improvement")
        else:
            print("❌ POOR: Significant issues with graph connections")
        print("="*70)


def main():
    evaluator = SachbearbeiterUseCaseEvaluator()
    
    try:
        evaluator.run_all_evaluations()
    finally:
        evaluator.close()
    
    return 0


if __name__ == "__main__":
    exit(main())
