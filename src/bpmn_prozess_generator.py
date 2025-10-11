"""
BPMN 2.0 Prozess-Generator für Sozialrecht-Sachbearbeitung
Erstellt Prozessvisualisierungen für komplexe Sozialrechts-Fälle

Integriert mit Neo4j für regelbasierte Prozessgenerierung
"""

import xml.etree.ElementTree as ET
from typing import List, Dict, Optional
from dataclasses import dataclass
from enum import Enum
import json


class BPMNElementType(Enum):
    """BPMN 2.0 Element-Typen"""
    START_EVENT = "startEvent"
    END_EVENT = "endEvent"
    TASK = "task"
    USER_TASK = "userTask"
    SERVICE_TASK = "serviceTask"
    GATEWAY_EXCLUSIVE = "exclusiveGateway"
    GATEWAY_PARALLEL = "parallelGateway"
    SEQUENCE_FLOW = "sequenceFlow"


@dataclass
class BPMNElement:
    """BPMN Element"""
    id: str
    name: str
    element_type: BPMNElementType
    properties: Dict = None


class SozialrechtBPMNGenerator:
    """
    Generator für BPMN 2.0 Prozess-Diagramme
    Spezialisiert für Sozialrechts-Sachbearbeitung
    """

    def __init__(self):
        self.elements = []
        self.flows = []
        self.element_counter = 0

    def _generate_id(self, prefix: str = "Element") -> str:
        """Generate unique element ID"""
        self.element_counter += 1
        return f"{prefix}_{self.element_counter}"

    def add_start_event(self, name: str = "Antrag eingegangen") -> str:
        """Add BPMN Start Event"""
        elem_id = self._generate_id("Start")
        self.elements.append(BPMNElement(
            id=elem_id,
            name=name,
            element_type=BPMNElementType.START_EVENT
        ))
        return elem_id

    def add_end_event(self, name: str = "Bescheid erteilt") -> str:
        """Add BPMN End Event"""
        elem_id = self._generate_id("End")
        self.elements.append(BPMNElement(
            id=elem_id,
            name=name,
            element_type=BPMNElementType.END_EVENT
        ))
        return elem_id

    def add_user_task(self, name: str, assignee: str = None, sgb_ref: str = None) -> str:
        """Add User Task (Sachbearbeiter-Aufgabe)

        Args:
            name: Task name (z.B. "Antrag prüfen")
            assignee: Zuständige Rolle (z.B. "Sachbearbeiter SGB II")
            sgb_ref: Rechtliche Grundlage (z.B. "SGB II § 37")
        """
        elem_id = self._generate_id("Task")
        props = {}
        if assignee:
            props['assignee'] = assignee
        if sgb_ref:
            props['rechtliche_grundlage'] = sgb_ref

        self.elements.append(BPMNElement(
            id=elem_id,
            name=name,
            element_type=BPMNElementType.USER_TASK,
            properties=props
        ))
        return elem_id

    def add_service_task(self, name: str, system: str = None) -> str:
        """Add Service Task (Automatisierte Aufgabe)"""
        elem_id = self._generate_id("Service")
        props = {}
        if system:
            props['system'] = system

        self.elements.append(BPMNElement(
            id=elem_id,
            name=name,
            element_type=BPMNElementType.SERVICE_TASK,
            properties=props
        ))
        return elem_id

    def add_exclusive_gateway(self, name: str, decision_criteria: str = None) -> str:
        """Add Exclusive Gateway (XOR - Entscheidung)

        Args:
            name: Gateway name (z.B. "Erwerbsfähig?")
            decision_criteria: Entscheidungskriterium (z.B. "SGB II § 8")
        """
        elem_id = self._generate_id("Gateway")
        props = {}
        if decision_criteria:
            props['decision_criteria'] = decision_criteria

        self.elements.append(BPMNElement(
            id=elem_id,
            name=name,
            element_type=BPMNElementType.GATEWAY_EXCLUSIVE,
            properties=props
        ))
        return elem_id

    def add_parallel_gateway(self, name: str = "Parallel") -> str:
        """Add Parallel Gateway (AND - Parallelisierung)"""
        elem_id = self._generate_id("ParallelGW")
        self.elements.append(BPMNElement(
            id=elem_id,
            name=name,
            element_type=BPMNElementType.GATEWAY_PARALLEL
        ))
        return elem_id

    def add_sequence_flow(self, from_id: str, to_id: str, condition: str = None) -> str:
        """Add Sequence Flow (Verbindung)

        Args:
            from_id: Source element ID
            to_id: Target element ID
            condition: Condition label (z.B. "Ja", "Nein", "Erwerbsfähig")
        """
        flow_id = self._generate_id("Flow")
        self.flows.append({
            'id': flow_id,
            'from': from_id,
            'to': to_id,
            'condition': condition
        })
        return flow_id

    def generate_bpmn_xml(self, process_name: str = "Sozialrecht Prozess") -> str:
        """Generate BPMN 2.0 XML"""

        # Create root element
        root = ET.Element('definitions', {
            'xmlns': 'http://www.omg.org/spec/BPMN/20100524/MODEL',
            'xmlns:bpmndi': 'http://www.omg.org/spec/BPMN/20100524/DI',
            'xmlns:dc': 'http://www.omg.org/spec/DD/20100524/DC',
            'xmlns:di': 'http://www.omg.org/spec/DD/20100524/DI',
            'id': 'Definitions_1',
            'targetNamespace': 'http://bpmn.io/schema/bpmn'
        })

        # Create process
        process = ET.SubElement(root, 'process', {
            'id': 'Process_1',
            'name': process_name,
            'isExecutable': 'false'
        })

        # Add all elements
        for element in self.elements:
            elem_attribs = {'id': element.id, 'name': element.name}

            if element.properties:
                # Add properties as documentation
                doc = ET.SubElement(
                    ET.SubElement(process, element.element_type.value, elem_attribs),
                    'documentation'
                )
                doc.text = json.dumps(element.properties, ensure_ascii=False)
            else:
                ET.SubElement(process, element.element_type.value, elem_attribs)

        # Add all flows
        for flow in self.flows:
            flow_attribs = {
                'id': flow['id'],
                'sourceRef': flow['from'],
                'targetRef': flow['to']
            }
            if flow['condition']:
                flow_attribs['name'] = flow['condition']

            ET.SubElement(process, 'sequenceFlow', flow_attribs)

        # Generate XML string
        return ET.tostring(root, encoding='unicode', method='xml')

    def generate_mermaid(self) -> str:
        """Generate Mermaid.js flowchart (leichter zu visualisieren)"""
        lines = ["graph TD"]

        # Add elements
        for element in self.elements:
            shape_start, shape_end = self._get_mermaid_shape(element.element_type)
            lines.append(f"    {element.id}{shape_start}{element.name}{shape_end}")

        # Add flows
        for flow in self.flows:
            condition_label = f"|{flow['condition']}|" if flow['condition'] else ""
            lines.append(f"    {flow['from']} -->{condition_label} {flow['to']}")

        return "\n".join(lines)

    def _get_mermaid_shape(self, element_type: BPMNElementType) -> tuple:
        """Get Mermaid shape notation"""
        shapes = {
            BPMNElementType.START_EVENT: ("([", "])"),
            BPMNElementType.END_EVENT: ("([", "])"),
            BPMNElementType.TASK: ("[", "]"),
            BPMNElementType.USER_TASK: ("[", "]"),
            BPMNElementType.SERVICE_TASK: ("[[", "]]"),
            BPMNElementType.GATEWAY_EXCLUSIVE: ("{", "}"),
            BPMNElementType.GATEWAY_PARALLEL: ("{", "}")
        }
        return shapes.get(element_type, ("[", "]"))


# === VORDEFINIERTE PROZESS-TEMPLATES ===

def create_sgb2_antrag_prozess() -> SozialrechtBPMNGenerator:
    """
    BPMN Prozess: SGB II Antragstellung und Bewilligung
    Typischer Ablauf im Jobcenter
    """
    bpmn = SozialrechtBPMNGenerator()

    # Start
    start = bpmn.add_start_event("Antrag auf Bürgergeld eingegangen")

    # Schritt 1: Formale Prüfung
    task1 = bpmn.add_user_task(
        "Antrag formal prüfen",
        assignee="Sachbearbeiter Eingangszone",
        sgb_ref="SGB II § 37, SGB X § 16"
    )
    bpmn.add_sequence_flow(start, task1)

    # Gateway: Formal vollständig?
    gw1 = bpmn.add_exclusive_gateway(
        "Antrag vollständig?",
        decision_criteria="SGB X § 60 Mitwirkungspflichten"
    )
    bpmn.add_sequence_flow(task1, gw1)

    # Nein-Zweig: Nachforderung
    task_nachforderung = bpmn.add_user_task(
        "Unterlagen nachfordern",
        sgb_ref="SGB X § 60"
    )
    bpmn.add_sequence_flow(gw1, task_nachforderung, "Nein - Unvollständig")
    bpmn.add_sequence_flow(task_nachforderung, task1, "Unterlagen eingegangen")

    # Ja-Zweig: Sachliche Prüfung
    task2 = bpmn.add_user_task(
        "Leistungsberechtigung prüfen",
        assignee="Sachbearbeiter Leistung",
        sgb_ref="SGB II § 7, § 8, § 9"
    )
    bpmn.add_sequence_flow(gw1, task2, "Ja - Vollständig")

    # Parallel Gateway: Mehrere Prüfungen gleichzeitig
    parallel_split = bpmn.add_parallel_gateway("Parallele Prüfungen")
    bpmn.add_sequence_flow(task2, parallel_split)

    # Prüfung 1: Erwerbsfähigkeit
    task_erwerbsfaehig = bpmn.add_user_task(
        "Erwerbsfähigkeit prüfen",
        sgb_ref="SGB II § 8"
    )
    bpmn.add_sequence_flow(parallel_split, task_erwerbsfaehig)

    # Prüfung 2: Hilfebedürftigkeit
    task_hilfebeduerftig = bpmn.add_user_task(
        "Hilfebedürftigkeit prüfen",
        sgb_ref="SGB II § 9"
    )
    bpmn.add_sequence_flow(parallel_split, task_hilfebeduerftig)

    # Prüfung 3: Einkommen/Vermögen
    task_einkommen = bpmn.add_service_task(
        "Einkommen/Vermögen berechnen",
        system="Fachverfahren (§ 11, § 12)"
    )
    bpmn.add_sequence_flow(parallel_split, task_einkommen)

    # Parallel Join
    parallel_join = bpmn.add_parallel_gateway("Prüfungen abgeschlossen")
    bpmn.add_sequence_flow(task_erwerbsfaehig, parallel_join)
    bpmn.add_sequence_flow(task_hilfebeduerftig, parallel_join)
    bpmn.add_sequence_flow(task_einkommen, parallel_join)

    # Gateway: Leistungsberechtigt?
    gw2 = bpmn.add_exclusive_gateway(
        "Leistungsberechtigt?",
        decision_criteria="SGB II § 7 ff."
    )
    bpmn.add_sequence_flow(parallel_join, gw2)

    # Ja-Zweig: Bewilligung
    task_bewilligung = bpmn.add_user_task(
        "Leistung berechnen und bewilligen",
        sgb_ref="SGB II § 19-22"
    )
    bpmn.add_sequence_flow(gw2, task_bewilligung, "Ja - Berechtigt")

    task_bescheid_positiv = bpmn.add_user_task(
        "Bewilligungsbescheid erstellen",
        sgb_ref="SGB X § 33"
    )
    bpmn.add_sequence_flow(task_bewilligung, task_bescheid_positiv)

    # Nein-Zweig: Ablehnung
    task_bescheid_negativ = bpmn.add_user_task(
        "Ablehnungsbescheid erstellen",
        sgb_ref="SGB X § 33, § 39"
    )
    bpmn.add_sequence_flow(gw2, task_bescheid_negativ, "Nein - Nicht berechtigt")

    # Zusammenführung
    end = bpmn.add_end_event("Bescheid versandt")
    bpmn.add_sequence_flow(task_bescheid_positiv, end)
    bpmn.add_sequence_flow(task_bescheid_negativ, end)

    return bpmn


def create_sgb2_sanktion_prozess() -> SozialrechtBPMNGenerator:
    """
    BPMN Prozess: SGB II Sanktionsverfahren
    Nach § 31-32 SGB II
    """
    bpmn = SozialrechtBPMNGenerator()

    # Start
    start = bpmn.add_start_event("Pflichtverletzung festgestellt")

    # Anhörung
    task1 = bpmn.add_user_task(
        "Anhörung durchführen",
        sgb_ref="SGB X § 24 - Rechtliches Gehör"
    )
    bpmn.add_sequence_flow(start, task1)

    # Gateway: Triftiger Grund?
    gw1 = bpmn.add_exclusive_gateway(
        "Triftiger Grund vorhanden?",
        decision_criteria="SGB II § 31 Abs. 2"
    )
    bpmn.add_sequence_flow(task1, gw1)

    # Ja: Keine Sanktion
    end_kein_grund = bpmn.add_end_event("Keine Sanktion - Triftiger Grund")
    bpmn.add_sequence_flow(gw1, end_kein_grund, "Ja")

    # Nein: Sanktion
    task_sanktion = bpmn.add_user_task(
        "Sanktionshöhe berechnen",
        sgb_ref="SGB II § 31a, § 31b"
    )
    bpmn.add_sequence_flow(gw1, task_sanktion, "Nein")

    # Gateway: Wiederholte Pflichtverletzung?
    gw2 = bpmn.add_exclusive_gateway(
        "Wiederholte Pflichtverletzung?",
        decision_criteria="SGB II § 31b"
    )
    bpmn.add_sequence_flow(task_sanktion, gw2)

    # Erst-Sanktion
    task_erst = bpmn.add_service_task(
        "Erstmalige Minderung festsetzen",
        system="30% Minderung (§ 31a Abs. 1)"
    )
    bpmn.add_sequence_flow(gw2, task_erst, "Erstmalig")

    # Wiederholungs-Sanktion
    task_wiederholt = bpmn.add_service_task(
        "Verschärfte Minderung festsetzen",
        system="60-100% Minderung (§ 31b)"
    )
    bpmn.add_sequence_flow(gw2, task_wiederholt, "Wiederholt")

    # Bescheid erstellen
    task_bescheid = bpmn.add_user_task(
        "Sanktionsbescheid erlassen",
        sgb_ref="SGB X § 33, § 39 Rechtsbehelfsbelehrung"
    )
    bpmn.add_sequence_flow(task_erst, task_bescheid)
    bpmn.add_sequence_flow(task_wiederholt, task_bescheid)

    # End
    end = bpmn.add_end_event("Sanktion verhängt")
    bpmn.add_sequence_flow(task_bescheid, end)

    return bpmn


def create_sgb12_grundsicherung_alter_prozess() -> SozialrechtBPMNGenerator:
    """
    BPMN Prozess: SGB XII Grundsicherung im Alter
    Sozialhilfe für Rentner
    """
    bpmn = SozialrechtBPMNGenerator()

    start = bpmn.add_start_event("Antrag auf Grundsicherung im Alter")

    # Altersgrenze prüfen
    gw_alter = bpmn.add_exclusive_gateway(
        "Mindestalter erreicht?",
        decision_criteria="SGB XII § 41 (67 Jahre oder Erwerbsminderung)"
    )
    bpmn.add_sequence_flow(start, gw_alter)

    # Zu jung: Verweis auf SGB II
    task_verweis = bpmn.add_user_task(
        "Verweis auf SGB II (Bürgergeld)",
        sgb_ref="SGB XII § 5 Abs. 2"
    )
    end_verweis = bpmn.add_end_event("Antrag abgegeben an Jobcenter")
    bpmn.add_sequence_flow(gw_alter, task_verweis, "Nein - Unter 67")
    bpmn.add_sequence_flow(task_verweis, end_verweis)

    # Altersgrenze erreicht
    task_bedarfsermittlung = bpmn.add_user_task(
        "Bedarfsermittlung durchführen",
        sgb_ref="SGB XII § 27-29, § 42"
    )
    bpmn.add_sequence_flow(gw_alter, task_bedarfsermittlung, "Ja - Über 67")

    # Parallel: Einkommen + Vermögen
    parallel = bpmn.add_parallel_gateway("Parallel prüfen")
    bpmn.add_sequence_flow(task_bedarfsermittlung, parallel)

    task_rente = bpmn.add_service_task(
        "Renteneinkommen abfragen",
        system="DRV-Schnittstelle"
    )
    bpmn.add_sequence_flow(parallel, task_rente)

    task_vermoegen = bpmn.add_user_task(
        "Vermögen prüfen",
        sgb_ref="SGB XII § 90"
    )
    bpmn.add_sequence_flow(parallel, task_vermoegen)

    parallel_join = bpmn.add_parallel_gateway("Prüfungen abgeschlossen")
    bpmn.add_sequence_flow(task_rente, parallel_join)
    bpmn.add_sequence_flow(task_vermoegen, parallel_join)

    # Bedarfsberechnung
    task_berechnung = bpmn.add_service_task(
        "Grundsicherung berechnen",
        system="Fachverfahren SGB XII"
    )
    bpmn.add_sequence_flow(parallel_join, task_berechnung)

    # Bescheid
    task_bescheid = bpmn.add_user_task(
        "Bescheid erstellen und versenden",
        sgb_ref="SGB X § 33"
    )
    bpmn.add_sequence_flow(task_berechnung, task_bescheid)

    end = bpmn.add_end_event("Grundsicherung bewilligt")
    bpmn.add_sequence_flow(task_bescheid, end)

    return bpmn


def create_sgb3_vermittlung_prozess() -> SozialrechtBPMNGenerator:
    """
    BPMN Prozess: SGB III Vermittlung in Arbeit
    Arbeitsförderung durch Arbeitsagentur
    """
    bpmn = SozialrechtBPMNGenerator()

    start = bpmn.add_start_event("Arbeitslos gemeldet")

    # Profiling
    task_profiling = bpmn.add_user_task(
        "Profiling / Kompetenzfeststellung",
        assignee="Arbeitsvermittler",
        sgb_ref="SGB III § 37 Vermittlung"
    )
    bpmn.add_sequence_flow(start, task_profiling)

    # Gateway: Vermittlungshemmnisse?
    gw_hemmnisse = bpmn.add_exclusive_gateway(
        "Vermittlungshemmnisse?",
        decision_criteria="SGB III § 44 ff. Förderung"
    )
    bpmn.add_sequence_flow(task_profiling, gw_hemmnisse)

    # Ja: Förderung notwendig
    task_foerderung = bpmn.add_user_task(
        "Fördermaßnahme auswählen",
        sgb_ref="SGB III § 45 MAG, § 81 FbW"
    )
    bpmn.add_sequence_flow(gw_hemmnisse, task_foerderung, "Ja - Hemmnisse vorhanden")

    task_eingliederung = bpmn.add_user_task(
        "Eingliederungsvereinbarung abschließen",
        sgb_ref="SGB II § 15 (analog)"
    )
    bpmn.add_sequence_flow(task_foerderung, task_eingliederung)

    # Nein: Direkte Vermittlung
    task_vermittlung = bpmn.add_user_task(
        "Stellenangebote vermitteln",
        assignee="Arbeitsvermittler"
    )
    bpmn.add_sequence_flow(gw_hemmnisse, task_vermittlung, "Nein - Vermittelbar")
    bpmn.add_sequence_flow(task_eingliederung, task_vermittlung)

    # Gateway: Vermittlung erfolgreich?
    gw_erfolg = bpmn.add_exclusive_gateway("Vermittelt?")
    bpmn.add_sequence_flow(task_vermittlung, gw_erfolg)

    # Erfolg
    end_erfolg = bpmn.add_end_event("Arbeitsverhältnis aufgenommen")
    bpmn.add_sequence_flow(gw_erfolg, end_erfolg, "Ja - Vermittelt")

    # Kein Erfolg: Zurück zu Profiling
    bpmn.add_sequence_flow(gw_erfolg, task_profiling, "Nein - Weiter suchen")

    return bpmn


# === EXPORT FUNCTIONS ===

def save_bpmn_to_file(bpmn: SozialrechtBPMNGenerator, filename: str, format: str = 'xml'):
    """Save BPMN to file

    Args:
        bpmn: Generator instance
        filename: Output filename
        format: 'xml' or 'mermaid'
    """
    if format == 'xml':
        content = bpmn.generate_bpmn_xml()
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(content)
    elif format == 'mermaid':
        content = bpmn.generate_mermaid()
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(content)
    else:
        raise ValueError(f"Unknown format: {format}")

    print(f"✅ BPMN saved to: {filename}")


if __name__ == "__main__":
    # Generate all process templates
    processes = {
        'SGB_II_Antragstellung': create_sgb2_antrag_prozess(),
        'SGB_II_Sanktionsverfahren': create_sgb2_sanktion_prozess(),
        'SGB_XII_Grundsicherung_Alter': create_sgb12_grundsicherung_alter_prozess(),
        'SGB_III_Arbeitsvermittlung': create_sgb3_vermittlung_prozess()
    }

    # Export all processes
    for name, bpmn_obj in processes.items():
        # BPMN 2.0 XML (für Camunda, Signavio, etc.)
        save_bpmn_to_file(bpmn_obj, f"processes/{name}.bpmn", format='xml')

        # Mermaid (für Markdown/Dokumentation)
        save_bpmn_to_file(bpmn_obj, f"processes/{name}.mmd", format='mermaid')

    print(f"\n✨ {len(processes)} Prozesse generiert!")
    print("\n📖 Verwendung:")
    print("  - BPMN XML: In Camunda Modeler öffnen")
    print("  - Mermaid: In README.md einbinden oder mit Mermaid Live Editor")
