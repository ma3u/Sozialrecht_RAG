"""
Neo4j Prozess-Integration
Verknüpft BPMN Prozess-Schritte mit Sozialrecht-Dokumenten

Ermöglicht: Click auf Prozess-Schritt → Zeigt relevante Gesetze/Weisungen
"""

from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)


class Neo4jProzessIntegration:
    """
    Integriert BPMN Prozesse mit Sozialrecht-Dokumenten in Neo4j
    Ermöglicht kontextsensitive Handlungsempfehlungen
    """

    def __init__(self, neo4j_driver):
        self.driver = neo4j_driver

    def create_process_schema(self):
        """Erstelle Prozess-spezifisches Schema"""
        with self.driver.session() as session:
            # Process Template Nodes
            session.run("""
                CREATE CONSTRAINT IF NOT EXISTS FOR (pt:ProcessTemplate) REQUIRE pt.id IS UNIQUE
            """)

            # Process Step Nodes
            session.run("""
                CREATE CONSTRAINT IF NOT EXISTS FOR (ps:ProcessStep) REQUIRE ps.id IS UNIQUE
            """)

            # Decision Node
            session.run("""
                CREATE INDEX IF NOT EXISTS FOR (d:Decision) ON (d.criteria)
            """)

            logger.info("✅ Prozess-Schema erstellt")

    def add_process_template(self,
                            process_id: str,
                            name: str,
                            sgb: str,
                            steps: List[Dict]) -> str:
        """Füge Prozess-Template zu Neo4j hinzu

        Args:
            process_id: Eindeutige ID (z.B. "SGB_II_Antragstellung")
            name: Prozessname
            sgb: SGB-Nummer
            steps: Liste von Prozess-Schritten

        Returns:
            Process Template ID
        """
        with self.driver.session() as session:
            # Create Process Template
            session.run("""
                CREATE (pt:ProcessTemplate {
                    id: $process_id,
                    name: $name,
                    sgb: $sgb,
                    created: datetime(),
                    step_count: $step_count
                })
            """, process_id=process_id, name=name, sgb=sgb, step_count=len(steps))

            # Create Steps and link to documents
            for i, step in enumerate(steps):
                self._add_process_step(session, process_id, step, i)

        logger.info(f"✅ Prozess-Template '{name}' mit {len(steps)} Schritten hinzugefügt")
        return process_id

    def _add_process_step(self, session, process_id: str, step: Dict, order: int):
        """Füge einzelnen Prozess-Schritt hinzu"""

        # Create Step Node
        step_id = f"{process_id}_Step_{order}"

        session.run("""
            MATCH (pt:ProcessTemplate {id: $process_id})
            CREATE (ps:ProcessStep {
                id: $step_id,
                name: $name,
                type: $type,
                order: $order,
                rechtliche_grundlage: $rechtliche_grundlage,
                assignee_role: $assignee,
                estimated_minutes: $estimated_minutes
            })
            CREATE (pt)-[:HAS_STEP {order: $order}]->(ps)
        """, {
            'process_id': process_id,
            'step_id': step_id,
            'name': step.get('name', ''),
            'type': step.get('type', 'Task'),
            'order': order,
            'rechtliche_grundlage': step.get('sgb_ref', ''),
            'assignee': step.get('assignee', ''),
            'estimated_minutes': step.get('estimated_minutes', 30)
        })

        # Link to relevant Documents/Paragraphs
        if 'sgb_ref' in step:
            self._link_step_to_documents(session, step_id, step['sgb_ref'])

    def _link_step_to_documents(self, session, step_id: str, sgb_ref: str):
        """Verknüpfe Prozess-Schritt mit relevanten Dokumenten

        Args:
            step_id: ID des Prozess-Schritts
            sgb_ref: Rechtliche Grundlage (z.B. "SGB II § 20", "§ 11-12")
        """
        # Parse SGB reference
        import re

        # Extract SGB number
        sgb_match = re.search(r'SGB\s*([IVX]+)', sgb_ref)
        sgb_nummer = sgb_match.group(1) if sgb_match else None

        # Extract paragraph numbers
        para_matches = re.findall(r'§\s*(\d+[a-z]?)', sgb_ref)

        if not sgb_nummer or not para_matches:
            return  # Can't link without specific references

        # Link to Gesetz
        session.run("""
            MATCH (ps:ProcessStep {id: $step_id})
            MATCH (d:Document {sgb_nummer: $sgb, document_type: 'Gesetz'})
            MERGE (ps)-[:RECHTLICHE_GRUNDLAGE {
                type: 'Gesetz',
                priority: 1
            }]->(d)
        """, step_id=step_id, sgb=sgb_nummer)

        # Link to Paragraphs
        for para_num in para_matches:
            session.run("""
                MATCH (ps:ProcessStep {id: $step_id})
                MATCH (p:Paragraph {sgb_nummer: $sgb, paragraph_nummer: $para})
                MERGE (ps)-[:VERWEIST_AUF {
                    paragraph: $para
                }]->(p)
            """, step_id=step_id, sgb=sgb_nummer, para=para_num)

            # Link to Fachliche Weisungen for this paragraph
            session.run("""
                MATCH (ps:ProcessStep {id: $step_id})
                MATCH (d:Document {
                    sgb_nummer: $sgb,
                    document_type: 'BA_Weisung'
                })-[:CONTAINS_PARAGRAPH]->(p:Paragraph {paragraph_nummer: $para})
                MERGE (ps)-[:HANDLUNGSEMPFEHLUNG {
                    type: 'Fachliche_Weisung',
                    priority: 2,
                    paragraph: $para
                }]->(d)
            """, step_id=step_id, sgb=sgb_nummer, para=para_num)

    def get_recommendations_for_step(self, step_id: str) -> Dict:
        """Hole Handlungsempfehlungen für Prozess-Schritt

        Args:
            step_id: Prozess-Schritt ID

        Returns:
            Dictionary mit Gesetz, Weisungen, BMAS Rundschreiben
        """
        with self.driver.session() as session:
            result = session.run("""
                MATCH (ps:ProcessStep {id: $step_id})

                // Get Gesetz
                OPTIONAL MATCH (ps)-[rg:RECHTLICHE_GRUNDLAGE]->(gesetz:Document {document_type: 'Gesetz'})

                // Get Weisungen
                OPTIONAL MATCH (ps)-[hw:HANDLUNGSEMPFEHLUNG]->(weisung:Document)
                WHERE weisung.document_type IN ['BA_Weisung', 'Harald_Thome']

                // Get BMAS Rundschreiben
                OPTIONAL MATCH (ps)-[hr:HANDLUNGSEMPFEHLUNG]->(bmas:Document {document_type: 'BMAS_Rundschreiben'})

                // Get related Paragraphs
                OPTIONAL MATCH (ps)-[vp:VERWEIST_AUF]->(para:Paragraph)

                RETURN ps.name as step_name,
                       ps.rechtliche_grundlage as rechtliche_grundlage,
                       COLLECT(DISTINCT {
                           type: 'Gesetz',
                           filename: gesetz.filename,
                           sgb: gesetz.sgb_nummer,
                           trust: gesetz.trust_score
                       }) as gesetz_docs,
                       COLLECT(DISTINCT {
                           type: weisung.document_type,
                           filename: weisung.filename,
                           stand: weisung.stand_datum,
                           trust: weisung.trust_score,
                           paragraph: hw.paragraph
                       }) as weisungen,
                       COLLECT(DISTINCT {
                           paragraph: para.paragraph_nummer,
                           content_preview: SUBSTRING(para.content, 0, 200)
                       }) as paragraphen
            """, step_id=step_id)

            record = result.single()

            if not record:
                return {'error': f'Prozess-Schritt {step_id} nicht gefunden'}

            return {
                'step_name': record['step_name'],
                'rechtliche_grundlage': record['rechtliche_grundlage'],
                'gesetz': [g for g in record['gesetz_docs'] if g['filename']],
                'weisungen': [w for w in record['weisungen'] if w['filename']],
                'paragraphen': record['paragraphen']
            }

    def get_full_process_with_docs(self, process_id: str) -> Dict:
        """Hole kompletten Prozess mit allen verknüpften Dokumenten

        Args:
            process_id: Process Template ID

        Returns:
            Vollständiger Prozess mit allen Schritten und Dokumenten
        """
        with self.driver.session() as session:
            result = session.run("""
                MATCH (pt:ProcessTemplate {id: $process_id})
                MATCH (pt)-[hs:HAS_STEP]->(ps:ProcessStep)
                OPTIONAL MATCH (ps)-[:RECHTLICHE_GRUNDLAGE]->(gesetz:Document {document_type: 'Gesetz'})
                OPTIONAL MATCH (ps)-[:HANDLUNGSEMPFEHLUNG]->(weisung:Document)

                RETURN pt.name as process_name,
                       pt.sgb as sgb,
                       COLLECT({
                           order: hs.order,
                           step_name: ps.name,
                           step_type: ps.type,
                           rechtliche_grundlage: ps.rechtliche_grundlage,
                           assignee: ps.assignee_role,
                           gesetz_file: gesetz.filename,
                           weisungen: COLLECT(DISTINCT weisung.filename)
                       }) as steps
                ORDER BY hs.order
            """, process_id=process_id)

            record = result.single()

            if not record:
                return {'error': f'Prozess {process_id} nicht gefunden'}

            return {
                'process_name': record['process_name'],
                'sgb': record['sgb'],
                'steps': record['steps']
            }

    def create_case_instance(self,
                           process_template_id: str,
                           case_data: Dict) -> str:
        """Erstelle Prozess-Instanz für konkreten Fall

        Args:
            process_template_id: Template ID
            case_data: Fall-spezifische Daten (Antragsteller, Einkommen, etc.)

        Returns:
            Case Instance ID
        """
        import uuid
        case_id = str(uuid.uuid4())

        with self.driver.session() as session:
            session.run("""
                MATCH (pt:ProcessTemplate {id: $template_id})
                CREATE (ci:CaseInstance {
                    id: $case_id,
                    created: datetime(),
                    status: 'In Bearbeitung',
                    antragsteller: $antragsteller,
                    current_step: 0
                })
                CREATE (ci)-[:BASED_ON]->(pt)
            """, {
                'template_id': process_template_id,
                'case_id': case_id,
                'antragsteller': case_data.get('antragsteller', 'Unbekannt')
            })

            # Add case-specific data
            for key, value in case_data.items():
                if key != 'antragsteller':
                    session.run("""
                        MATCH (ci:CaseInstance {id: $case_id})
                        SET ci[$key] = $value
                    """, case_id=case_id, key=key, value=value)

        logger.info(f"✅ Fall-Instanz erstellt: {case_id}")
        return case_id

    def advance_case_to_step(self, case_id: str, step_order: int, decision_data: Optional[Dict] = None):
        """Bewege Fall zu nächstem Schritt

        Args:
            case_id: Case Instance ID
            step_order: Schritt-Nummer
            decision_data: Entscheidungsdaten (für Gateways)
        """
        with self.driver.session() as session:
            # Update case status
            session.run("""
                MATCH (ci:CaseInstance {id: $case_id})
                SET ci.current_step = $step,
                    ci.last_updated = datetime()
            """, case_id=case_id, step=step_order)

            # Log decision if provided
            if decision_data:
                session.run("""
                    MATCH (ci:CaseInstance {id: $case_id})
                    CREATE (d:Decision {
                        step: $step,
                        decision: $decision,
                        reason: $reason,
                        decided_by: $user,
                        timestamp: datetime()
                    })
                    CREATE (ci)-[:HAD_DECISION]->(d)
                """, {
                    'case_id': case_id,
                    'step': step_order,
                    'decision': decision_data.get('decision', ''),
                    'reason': decision_data.get('reason', ''),
                    'user': decision_data.get('user', 'System')
                })

    def get_current_step_recommendations(self, case_id: str) -> Dict:
        """Hole Empfehlungen für aktuellen Prozess-Schritt

        Returns:
            - Relevante Gesetze
            - Fachliche Weisungen
            - Vorherige Entscheidungen in ähnlichen Fällen
        """
        with self.driver.session() as session:
            result = session.run("""
                // Get current case and step
                MATCH (ci:CaseInstance {id: $case_id})
                MATCH (ci)-[:BASED_ON]->(pt:ProcessTemplate)
                MATCH (pt)-[hs:HAS_STEP]->(ps:ProcessStep)
                WHERE hs.order = ci.current_step

                // Get linked documents
                OPTIONAL MATCH (ps)-[:RECHTLICHE_GRUNDLAGE]->(gesetz:Document {document_type: 'Gesetz'})
                OPTIONAL MATCH (ps)-[:HANDLUNGSEMPFEHLUNG]->(weisung:Document)
                OPTIONAL MATCH (ps)-[:VERWEIST_AUF]->(para:Paragraph)

                // Get relevant chunks for this step
                OPTIONAL MATCH (gesetz)-[:HAS_CHUNK]->(gc:Chunk)
                WHERE gc.paragraph_nummer IN [para.paragraph_nummer]

                OPTIONAL MATCH (weisung)-[:HAS_CHUNK]->(wc:Chunk)
                WHERE wc.paragraph_nummer IN [para.paragraph_nummer]

                RETURN ps.name as step_name,
                       ps.type as step_type,
                       ps.rechtliche_grundlage as rechtliche_grundlage,
                       ps.assignee_role as assignee,

                       // Gesetz
                       gesetz.filename as gesetz_file,
                       COLLECT(DISTINCT gc.text)[0..3] as gesetz_chunks,

                       // Weisungen (sortiert nach Trust-Score)
                       COLLECT(DISTINCT {
                           filename: weisung.filename,
                           type: weisung.document_type,
                           trust: weisung.trust_score,
                           stand: weisung.stand_datum,
                           chunks: COLLECT(DISTINCT wc.text)[0..2]
                       }) as weisungen,

                       // Paragraphen
                       COLLECT(DISTINCT {
                           nummer: para.paragraph_nummer,
                           sgb: para.sgb_nummer,
                           content: para.content
                       }) as paragraphen
            """, case_id=case_id)

            record = result.single()

            if not record:
                return {'error': 'Aktueller Schritt nicht gefunden'}

            return {
                'step': {
                    'name': record['step_name'],
                    'type': record['step_type'],
                    'rechtliche_grundlage': record['rechtliche_grundlage'],
                    'assignee': record['assignee']
                },
                'gesetz': {
                    'filename': record['gesetz_file'],
                    'relevant_text': record['gesetz_chunks']
                },
                'weisungen': record['weisungen'],
                'paragraphen': record['paragraphen']
            }


# === BEISPIEL-PROZESS INSTANZIIERUNG ===

def create_sgb2_antrag_with_docs(prozess_integration: Neo4jProzessIntegration):
    """Erstelle SGB II Antragsprozess mit Dokument-Verknüpfungen"""

    steps = [
        {
            'name': 'Antrag formal prüfen',
            'type': 'UserTask',
            'sgb_ref': 'SGB II § 37',
            'assignee': 'Sachbearbeiter Eingangszone',
            'estimated_minutes': 15
        },
        {
            'name': 'Leistungsberechtigung prüfen',
            'type': 'UserTask',
            'sgb_ref': 'SGB II § 7',
            'assignee': 'Sachbearbeiter Leistung',
            'estimated_minutes': 30
        },
        {
            'name': 'Erwerbsfähigkeit prüfen',
            'type': 'UserTask',
            'sgb_ref': 'SGB II § 8',
            'assignee': 'Sachbearbeiter Leistung',
            'estimated_minutes': 20
        },
        {
            'name': 'Hilfebedürftigkeit prüfen',
            'type': 'UserTask',
            'sgb_ref': 'SGB II § 9',
            'assignee': 'Sachbearbeiter Leistung',
            'estimated_minutes': 25
        },
        {
            'name': 'Einkommen berechnen',
            'type': 'UserTask',
            'sgb_ref': 'SGB II § 11',
            'assignee': 'Sachbearbeiter Leistung',
            'estimated_minutes': 40
        },
        {
            'name': 'Vermögen prüfen',
            'type': 'UserTask',
            'sgb_ref': 'SGB II § 12',
            'assignee': 'Sachbearbeiter Leistung',
            'estimated_minutes': 30
        },
        {
            'name': 'Regelbedarf berechnen',
            'type': 'ServiceTask',
            'sgb_ref': 'SGB II § 20',
            'assignee': 'Fachverfahren',
            'estimated_minutes': 5
        },
        {
            'name': 'Mehrbedarfe prüfen',
            'type': 'UserTask',
            'sgb_ref': 'SGB II § 21',
            'assignee': 'Sachbearbeiter Leistung',
            'estimated_minutes': 20
        },
        {
            'name': 'Bescheid erstellen',
            'type': 'UserTask',
            'sgb_ref': 'SGB X § 33',
            'assignee': 'Sachbearbeiter Leistung',
            'estimated_minutes': 30
        }
    ]

    return prozess_integration.add_process_template(
        process_id='SGB_II_Antragstellung_Vollständig',
        name='SGB II Antragstellung (Vollständiger Prozess)',
        sgb='II',
        steps=steps
    )


# === QUERY-BEISPIELE ===

def example_queries():
    """Beispiel-Cypher-Queries für Prozess-Abfragen"""

    queries = {
        'Prozess mit allen Schritten': """
            MATCH (pt:ProcessTemplate {id: 'SGB_II_Antragstellung_Vollständig'})
            MATCH (pt)-[hs:HAS_STEP]->(ps:ProcessStep)
            OPTIONAL MATCH (ps)-[:RECHTLICHE_GRUNDLAGE]->(d:Document)
            RETURN ps.name as Schritt,
                   ps.rechtliche_grundlage as Rechtsgrundlage,
                   ps.assignee_role as Zuständig,
                   ps.estimated_minutes as Dauer_Min,
                   d.filename as Gesetz
            ORDER BY hs.order
        """,

        'Handlungsempfehlungen für Schritt': """
            MATCH (ps:ProcessStep {id: 'SGB_II_Antragstellung_Vollständig_Step_4'})
            MATCH (ps)-[:HANDLUNGSEMPFEHLUNG]->(w:Document)
            MATCH (w)-[:HAS_CHUNK]->(c:Chunk)
            WHERE c.paragraph_nummer = '9'
            RETURN w.filename,
                   w.trust_score,
                   w.stand_datum,
                   COLLECT(c.text)[0..3] as Relevante_Textausschnitte
        """,

        'Alle Prozesse für SGB II': """
            MATCH (pt:ProcessTemplate {sgb: 'II'})
            RETURN pt.id, pt.name, pt.step_count
        """,

        'Prozess-Statistik': """
            MATCH (pt:ProcessTemplate)
            MATCH (pt)-[:HAS_STEP]->(ps)
            RETURN pt.name,
                   COUNT(ps) as Schritte,
                   SUM(ps.estimated_minutes) as Geschätzte_Dauer_Min
        """
    }

    return queries


if __name__ == "__main__":
    from src.sozialrecht_neo4j_rag import SozialrechtNeo4jRAG

    # Initialize
    rag = SozialrechtNeo4jRAG()
    prozess_int = Neo4jProzessIntegration(rag.driver)

    # Create schema
    prozess_int.create_process_schema()

    # Add process with document links
    process_id = create_sgb2_antrag_with_docs(prozess_int)

    print(f"\n✅ Prozess erstellt: {process_id}")

    # Create example case
    case_id = prozess_int.create_case_instance(
        process_template_id=process_id,
        case_data={
            'antragsteller': 'Max Mustermann',
            'geburtsdatum': '1985-05-15',
            'familienstand': 'alleinerziehend',
            'kinder_anzahl': 2
        }
    )

    print(f"✅ Fall-Instanz erstellt: {case_id}")

    # Get recommendations for current step
    recommendations = prozess_int.get_current_step_recommendations(
        f"{process_id}_Step_0"
    )

    print(f"\n📋 Handlungsempfehlungen für '{recommendations['step_name']}':")
    print(f"   Rechtsgrundlage: {recommendations['rechtliche_grundlage']}")
    print(f"   Gesetz: {recommendations['gesetz']}")
    print(f"   Weisungen: {len(recommendations['weisungen'])} Dokumente")

    rag.close()
