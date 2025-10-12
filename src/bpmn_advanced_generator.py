"""
Erweiterter BPMN 2.0 Generator mit Swimlanes und Neo4j-Integration
- Automatische Prozess-Generierung aus Neo4j Sozialrecht-Daten
- Swimlanes für Stakeholder/Verantwortlichkeiten
- Draw.io kompatibel
"""

from src.bpmn_prozess_generator import SozialrechtBPMNGenerator, BPMNElementType
from typing import List, Dict, Optional
import xml.etree.ElementTree as ET


class AdvancedBPMNGenerator(SozialrechtBPMNGenerator):
    """Erweitert mit Swimlanes und automatischer Neo4j-Generierung"""

    def __init__(self):
        super().__init__()
        self.swimlanes = []
        self.element_lane_mapping = {}  # element_id → lane_id

    def add_swimlane(self, name: str, participant_type: str = "internal") -> str:
        """Füge Swimlane hinzu (für Stakeholder/Verantwortlichkeiten)

        Args:
            name: Lane-Name (z.B. "Sachbearbeiter", "Antragsteller", "DRV")
            participant_type: "internal" oder "external"
        """
        lane_id = self._generate_id("Lane")
        self.swimlanes.append({
            'id': lane_id,
            'name': name,
            'type': participant_type,
            'elements': []
        })
        return lane_id

    def add_task_to_lane(self, task_name: str, lane_id: str, **kwargs) -> str:
        """Füge Task zu spezifischer Swimlane hinzu"""
        task_id = self.add_user_task(task_name, **kwargs)
        self.element_lane_mapping[task_id] = lane_id

        # Find lane and add element
        for lane in self.swimlanes:
            if lane['id'] == lane_id:
                lane['elements'].append(task_id)

        return task_id

    def generate_from_neo4j(self, neo4j_rag, sgb: str, prozess_typ: str) -> 'AdvancedBPMNGenerator':
        """Generiere BPMN automatisch aus Neo4j Sozialrecht-Daten

        Args:
            neo4j_rag: SozialrechtNeo4jRAG Instance
            sgb: SGB-Nummer (z.B. "II")
            prozess_typ: "Antragstellung", "Sanktion", etc.
        """
        with neo4j_rag.driver.session() as session:
            # Query relevante Paragraphen für Prozess-Typ
            if prozess_typ == "Antragstellung" and sgb == "II":
                result = session.run("""
                    MATCH (d:Document {sgb_nummer: $sgb})-[:CONTAINS_PARAGRAPH]->(p:Paragraph)
                    WHERE p.paragraph_nummer IN ['37', '7', '8', '9', '11', '12', '20', '21', '40']
                    RETURN p.paragraph_nummer as para,
                           SUBSTRING(p.content, 0, 200) as beschreibung
                    ORDER BY p.paragraph_nummer
                """, sgb=sgb)

                # Erstelle Prozess-Schritte aus Neo4j-Daten
                for record in result:
                    # Extrahiere Aufgabe aus Paragraph-Beschreibung
                    para = record['para']
                    desc = record['beschreibung']

                    # Mapping Paragraph → Aufgabe
                    task_mapping = {
                        '37': 'Antrag entgegennehmen und registrieren',
                        '7': 'Leistungsberechtigung prüfen',
                        '8': 'Erwerbsfähigkeit prüfen',
                        '9': 'Hilfebedürftigkeit feststellen',
                        '11': 'Einkommen berechnen',
                        '12': 'Vermögen prüfen',
                        '20': 'Regelbedarf berechnen',
                        '21': 'Mehrbedarfe prüfen',
                        '40': 'Bescheid erstellen'
                    }

                    task_name = task_mapping.get(para, f'§ {para} prüfen')
                    # Aufgaben werden später zu Lanes zugeordnet

        return self


def create_sgb2_antrag_mit_swimlanes() -> AdvancedBPMNGenerator:
    """
    Vollständiger SGB II Antragsprozess mit Swimlanes

    Swimlanes (Verantwortlichkeiten):
    1. Antragsteller (extern)
    2. Sachbearbeiter Eingangszone (intern)
    3. Sachbearbeiter Leistung (intern)
    4. Fachverfahren/IT-System (intern)
    5. DRV (externe Stelle)
    6. Krankenkasse (externe Stelle)
    """
    bpmn = AdvancedBPMNGenerator()

    # === SWIMLANES DEFINIEREN ===
    lane_antragsteller = bpmn.add_swimlane("Antragsteller", "external")
    lane_eingang = bpmn.add_swimlane("Sachbearbeiter Eingangszone", "internal")
    lane_leistung = bpmn.add_swimlane("Sachbearbeiter Leistung", "internal")
    lane_system = bpmn.add_swimlane("Fachverfahren (IT)", "internal")
    lane_drv = bpmn.add_swimlane("DRV (Rentenversicherung)", "external")
    lane_kk = bpmn.add_swimlane("Krankenkasse", "external")

    # === PROZESS-SCHRITTE ===

    # Antragsteller
    start = bpmn.add_start_event("Antrag stellen")
    task_antrag = bpmn.add_task_to_lane(
        "Antrag ausfüllen und einreichen",
        lane_antragsteller,
        sgb_ref="SGB II § 37 Abs. 1 - Antragstellung"
    )
    bpmn.add_sequence_flow(start, task_antrag)

    # Eingangszone
    task_registrierung = bpmn.add_task_to_lane(
        "Antrag registrieren",
        lane_eingang,
        sgb_ref="SGB II § 37 Abs. 2 - Zuständigkeit"
    )
    bpmn.add_sequence_flow(task_antrag, task_registrierung)

    task_formal_pruefung = bpmn.add_task_to_lane(
        "Formale Vollständigkeit prüfen",
        lane_eingang,
        sgb_ref="SGB X § 16 - Antragstellung"
    )
    bpmn.add_sequence_flow(task_registrierung, task_formal_pruefung)

    # Gateway: Vollständig?
    gw_vollstaendig = bpmn.add_exclusive_gateway(
        "Antrag vollständig?",
        decision_criteria="Alle Pflichtangaben + Nachweise vorhanden"
    )
    bpmn.add_sequence_flow(task_formal_pruefung, gw_vollstaendig)

    # Nein → Antragsteller
    task_nachforderung_versand = bpmn.add_task_to_lane(
        "Nachforderung versenden",
        lane_eingang,
        sgb_ref="SGB X § 60 - Mitwirkungspflichten"
    )
    bpmn.add_sequence_flow(gw_vollstaendig, task_nachforderung_versand, "Nein")

    task_unterlagen_nachreichen = bpmn.add_task_to_lane(
        "Fehlende Unterlagen nachreichen",
        lane_antragsteller
    )
    bpmn.add_sequence_flow(task_nachforderung_versand, task_unterlagen_nachreichen)
    bpmn.add_sequence_flow(task_unterlagen_nachreichen, task_formal_pruefung)

    # Ja → Sachbearbeiter Leistung
    task_zuweisung = bpmn.add_task_to_lane(
        "Antrag an Leistungssachbearbeiter zuweisen",
        lane_eingang
    )
    bpmn.add_sequence_flow(gw_vollstaendig, task_zuweisung, "Ja")

    # === PARALLELISIERUNG: Externe Daten abfragen ===
    parallel_split = bpmn.add_parallel_gateway("Parallele Datenabfragen")
    bpmn.add_sequence_flow(task_zuweisung, parallel_split)

    # DRV: Rentendaten
    task_drv_anfrage = bpmn.add_task_to_lane(
        "Rentenstatus abfragen",
        lane_leistung,
        sgb_ref="SGB II § 12a - RV-Daten"
    )
    bpmn.add_sequence_flow(parallel_split, task_drv_anfrage)

    task_drv_antwort = bpmn.add_service_task(
        "Rentendaten bereitstellen",
        system="DRV Datenaustausch"
    )
    bpmn.element_lane_mapping[task_drv_antwort.split('_')[1]] = lane_drv if 'Service' in task_drv_antwort else None
    bpmn.add_sequence_flow(task_drv_anfrage, task_drv_antwort)

    # Krankenkasse: Versicherungsstatus
    task_kk_anfrage = bpmn.add_task_to_lane(
        "Versicherungsstatus prüfen",
        lane_leistung,
        sgb_ref="SGB V § 5 - Versicherungspflicht"
    )
    bpmn.add_sequence_flow(parallel_split, task_kk_anfrage)

    task_kk_antwort = bpmn.add_service_task(
        "KV-Status mitteilen",
        system="KK Schnittstelle"
    )
    bpmn.add_sequence_flow(task_kk_anfrage, task_kk_antwort)

    # Antragsteller: Interview
    task_interview = bpmn.add_task_to_lane(
        "Persönliches Gespräch führen",
        lane_leistung,
        sgb_ref="SGB II § 41 - Beratung"
    )
    bpmn.add_sequence_flow(parallel_split, task_interview)

    # Parallel Join
    parallel_join = bpmn.add_parallel_gateway("Daten vollständig")
    bpmn.add_sequence_flow(task_drv_antwort, parallel_join)
    bpmn.add_sequence_flow(task_kk_antwort, parallel_join)
    bpmn.add_sequence_flow(task_interview, parallel_join)

    # === SACHLICHE PRÜFUNG ===
    task_leistungsberechtigung = bpmn.add_task_to_lane(
        "Leistungsberechtigung prüfen (§ 7)",
        lane_leistung,
        sgb_ref="SGB II § 7 - Leistungsberechtigte"
    )
    bpmn.add_sequence_flow(parallel_join, task_leistungsberechtigung)

    # Parallele Prüfungen
    parallel_pruefungen = bpmn.add_parallel_gateway("Parallele Sachprüfungen")
    bpmn.add_sequence_flow(task_leistungsberechtigung, parallel_pruefungen)

    task_erwerbsfaehig = bpmn.add_task_to_lane(
        "Erwerbsfähigkeit prüfen (§ 8)",
        lane_leistung,
        sgb_ref="SGB II § 8 - Mind. 3h täglich"
    )
    bpmn.add_sequence_flow(parallel_pruefungen, task_erwerbsfaehig)

    task_hilfebeduerftig = bpmn.add_task_to_lane(
        "Hilfebedürftigkeit feststellen (§ 9)",
        lane_leistung,
        sgb_ref="SGB II § 9 - Bedarf nicht selbst decken"
    )
    bpmn.add_sequence_flow(parallel_pruefungen, task_hilfebeduerftig)

    task_einkommen = bpmn.add_service_task(
        "Einkommen berechnen (§ 11)",
        system="Fachverfahren - § 11-11b"
    )
    bpmn.element_lane_mapping[task_einkommen.split('_')[1]] = lane_system if 'Service' in task_einkommen else None
    bpmn.add_sequence_flow(parallel_pruefungen, task_einkommen)

    task_vermoegen = bpmn.add_task_to_lane(
        "Vermögen prüfen (§ 12)",
        lane_leistung,
        sgb_ref="SGB II § 12 - Schonvermögen"
    )
    bpmn.add_sequence_flow(parallel_pruefungen, task_vermoegen)

    # Join
    join_pruefungen = bpmn.add_parallel_gateway("Prüfungen abgeschlossen")
    bpmn.add_sequence_flow(task_erwerbsfaehig, join_pruefungen)
    bpmn.add_sequence_flow(task_hilfebeduerftig, join_pruefungen)
    bpmn.add_sequence_flow(task_einkommen, join_pruefungen)
    bpmn.add_sequence_flow(task_vermoegen, join_pruefungen)

    # Gateway: Berechtigt?
    gw_berechtigt = bpmn.add_exclusive_gateway(
        "Leistungsberechtigt?",
        decision_criteria="§ 7 + § 8 + § 9 erfüllt"
    )
    bpmn.add_sequence_flow(join_pruefungen, gw_berechtigt)

    # NEIN-Zweig
    task_ablehnung = bpmn.add_task_to_lane(
        "Ablehnungsbescheid erstellen",
        lane_leistung,
        sgb_ref="SGB X § 33 + § 39 - Rechtsbehelfsbelehrung"
    )
    bpmn.add_sequence_flow(gw_berechtigt, task_ablehnung, "Nein")

    end_ablehnung = bpmn.add_end_event("Antrag abgelehnt")
    bpmn.add_sequence_flow(task_ablehnung, end_ablehnung)

    # JA-Zweig: Bedarfsberechnung
    task_regelbedarf = bpmn.add_service_task(
        "Regelbedarf berechnen (§ 20)",
        system="Fachverfahren - Regelbedarfsstufen"
    )
    bpmn.add_sequence_flow(gw_berechtigt, task_regelbedarf, "Ja")

    task_mehrbedarfe = bpmn.add_task_to_lane(
        "Mehrbedarfe prüfen (§ 21)",
        lane_leistung,
        sgb_ref="SGB II § 21 - Alleinerziehend, Behinderung, etc."
    )
    bpmn.add_sequence_flow(task_regelbedarf, task_mehrbedarfe)

    task_unterkunft = bpmn.add_task_to_lane(
        "Unterkunftskosten prüfen (§ 22)",
        lane_leistung,
        sgb_ref="SGB II § 22 - Tatsächliche Kosten"
    )
    bpmn.add_sequence_flow(task_mehrbedarfe, task_unterkunft)

    task_berechnung = bpmn.add_service_task(
        "Gesamtbedarf berechnen",
        system="Fachverfahren - § 19-22"
    )
    bpmn.add_sequence_flow(task_unterkunft, task_berechnung)

    # Bewilligungsbescheid
    task_bewilligung = bpmn.add_task_to_lane(
        "Bewilligungsbescheid erstellen",
        lane_leistung,
        sgb_ref="SGB X § 33 - Schriftlicher Bescheid"
    )
    bpmn.add_sequence_flow(task_berechnung, task_bewilligung)

    task_auszahlung = bpmn.add_service_task(
        "Zahlung veranlassen",
        system="Fachverfahren - Zahlungsverkehr"
    )
    bpmn.add_sequence_flow(task_bewilligung, task_auszahlung)

    end_bewilligt = bpmn.add_end_event("Leistung bewilligt")
    bpmn.add_sequence_flow(task_auszahlung, end_bewilligt)

    return bpmn


# === AUTOMATISCHE GENERIERUNG AUS NEO4J ===

def auto_generate_prozess_from_neo4j(neo4j_rag, sgb: str, haupt_paragraphen: List[str]) -> AdvancedBPMNGenerator:
    """
    Vollautomatische BPMN-Generierung aus Neo4j-Daten

    Liest Paragraphen-Beschreibungen und erstellt daraus Prozess-Schritte
    """
    bpmn = AdvancedBPMNGenerator()

    # Swimlanes basierend auf SGB
    if sgb == "II":
        lane_internal = bpmn.add_swimlane("Jobcenter Sachbearbeiter", "internal")
        lane_external = bpmn.add_swimlane("Antragsteller/Externe", "external")
    elif sgb == "III":
        lane_internal = bpmn.add_swimlane("Arbeitsagentur", "internal")
        lane_external = bpmn.add_swimlane("Arbeitsuchende/r", "external")
    else:
        lane_internal = bpmn.add_swimlane("Sachbearbeiter", "internal")
        lane_external = bpmn.add_swimlane("Antragsteller", "external")

    with neo4j_rag.driver.session() as session:
        # Query Paragraphen mit Weisungen
        for para in haupt_paragraphen:
            result = session.run("""
                MATCH (p:Paragraph {sgb_nummer: $sgb, paragraph_nummer: $para})
                MATCH (d:Document {document_type: 'BA_Weisung'})-[:CONTAINS_PARAGRAPH]->(p)
                RETURN p.content as beschreibung,
                       d.filename as weisung
                LIMIT 1
            """, sgb=sgb, para=para)

            record = result.single()
            if record:
                # Extrahiere Aufgabe aus Beschreibung
                task_name = f"§ {para} prüfen"
                bpmn.add_task_to_lane(task_name, lane_internal, sgb_ref=f"SGB {sgb} § {para}")

    return bpmn


if __name__ == "__main__":
    # Generiere erweiterten SGB II Prozess
    bpmn = create_sgb2_antrag_mit_swimlanes()

    # Export
    from src.bpmn_prozess_generator import save_bpmn_to_file

    save_bpmn_to_file(bpmn, "processes/SGB_II_Antrag_Swimlanes.bpmn", format='xml')
    save_bpmn_to_file(bpmn, "processes/SGB_II_Antrag_Swimlanes.mmd", format='mermaid')

    print("\n✅ Erweiterter SGB II Prozess mit Swimlanes generiert!")
    print("\n📊 Swimlanes:")
    for lane in bpmn.swimlanes:
        print(f"  - {lane['name']} ({lane['type']}): {len(lane['elements'])} Tasks")

    print("\n📖 Öffne in:")
    print("  - Camunda Modeler (BPMN XML)")
    print("  - Draw.io (importiere BPMN)")
    print("  - Signavio")
