# Aktionsplan nach Sachbearbeiter- und Prozessberater-Analyse

**Erstellt**: 2025-01-XX  
**Basis**: Graph-Analyse und SGB-Coverage-Report  
**Status nach Reparatur**: 16,922 Chunks zugänglich (40.5%)

---

## Executive Summary

Nach der erfolgreichen Reparatur der orphaned Norms sind nun **7 SGBs vollständig funktionsfähig** (II, III, IV, V, VI, VIII, XI) mit insgesamt 16,922 Chunks für RAG-basierte Abfragen. Die folgenden Maßnahmen adressieren verbleibende Datenlücken, Qualitätsverbesserungen und Produktionsreife.

---

## Phase 1: Datenvollständigkeit herstellen (Priorität: P0)

### 1.1 Fehlende SGB-Chunks importieren
**Status**: ❌ 5 SGBs ohne Chunks (I, VII, IX, X, XII)

**Maßnahmen**:
```bash
# Prüfen, ob Quelldaten vorhanden sind
ls -la data/raw_xml/SGB_I/
ls -la data/raw_xml/SGB_VII/
ls -la data/raw_xml/SGB_IX/
ls -la data/raw_xml/SGB_X/
ls -la data/raw_xml/SGB_XII/

# Chunking-Pipeline für fehlende SGBs ausführen
python scripts/chunk_legal_texts.py --sgb I --force-rechunk
python scripts/chunk_legal_texts.py --sgb VII --force-rechunk
python scripts/chunk_legal_texts.py --sgb IX --force-rechunk
python scripts/chunk_legal_texts.py --sgb X --force-rechunk
python scripts/chunk_legal_texts.py --sgb XII --force-rechunk
```

**Erwartetes Ergebnis**:
- Alle 12 SGBs haben Chunks
- Coverage steigt von 40.5% auf ~70-80%

**Verantwortlich**: Data Engineering  
**Deadline**: KW 5/2025

---

### 1.2 Verbleibende orphaned Chunks analysieren
**Status**: ⚠️ 603 Norms mit 2,475 orphaned Chunks

**Maßnahmen**:
```bash
# Analyseskript für verbleibende Orphans
python scripts/analyze_remaining_orphans.py --output logs/orphan_analysis.json

# Prüfen, ob weitere doknr-Mappings möglich sind
python scripts/find_doknr_patterns.py --unmapped-only
```

**Mögliche Ursachen**:
1. Normen aus Durchführungsverordnungen ohne eigenes LegalDocument
2. Historische Fassungen ohne aktuelles Dokument
3. Referenzen auf externe Gesetze (z.B. BGB, StGB)

**Lösung**:
- Entweder neue LegalDocument-Knoten anlegen
- Oder Orphans als "Referenznormen" markieren und separater Index

**Verantwortlich**: Data Engineering + Fachbereich  
**Deadline**: KW 6/2025

---

## Phase 2: Datenqualität verbessern (Priorität: P1)

### 2.1 Amendment-Abdeckung erhöhen
**Status**: ⚠️ Nur 0.5% Amendment-Coverage

**Ist-Zustand**:
```cypher
MATCH (a:Amendment)
RETURN count(a) as amendments  // Aktuell: ~50-100
```

**Maßnahmen**:
1. **Automatisiertes Amendment-Parsing**
   ```bash
   # XML-Metadaten nach Änderungsgesetzen durchsuchen
   python scripts/extract_amendments.py --source data/raw_xml/
   ```

2. **Manuelle Erfassung wichtiger Änderungen**
   - Bürgergeld-Reform 2023 (SGB II)
   - Pflegereform 2021 (SGB XI)
   - Teilhabestärkungsgesetz 2021 (SGB IX)

3. **Zeitliche Gültigkeitsbereiche hinzufügen**
   ```cypher
   MATCH (n:LegalNorm)
   SET n.gueltig_von = date('2023-01-01'),
       n.gueltig_bis = null  // null = aktuell gültig
   ```

**Erwartetes Ergebnis**:
- Amendment-Coverage: 20-30%
- Zeitliche Navigation möglich
- Historische Abfragen unterstützt

**Verantwortlich**: Juristische Fachredaktion + Data Engineering  
**Deadline**: KW 8/2025

---

### 2.2 Metadaten-Qualität prüfen und anreichern

**Maßnahmen**:
```cypher
// 1. Fehlende Titel ergänzen
MATCH (n:LegalNorm)
WHERE n.titel IS NULL OR n.titel = ''
WITH n
MATCH (n)<-[:CONTAINS_NORM]-(doc:LegalDocument)
SET n.titel = 'Norm aus ' + doc.name

// 2. Paragraph-Nummern normalisieren
MATCH (n:LegalNorm)
WHERE n.paragraph_nummer =~ '§.*'
SET n.paragraph_nummer_normalized = toInteger(replace(n.paragraph_nummer, '§', ''))

// 3. Chunk-Metadaten anreichern
MATCH (doc:LegalDocument)-[:CONTAINS_NORM]->(norm:LegalNorm)-[:HAS_CHUNK]->(c:Chunk)
SET c.sgb_nummer = doc.sgb_nummer,
    c.norm_paragraph = norm.paragraph_nummer
```

**Verantwortlich**: Data Engineering  
**Deadline**: KW 6/2025

---

### 2.3 Cross-References zwischen Normen herstellen

**Ist-Zustand**: Keine REFERS_TO-Beziehungen vorhanden

**Maßnahmen**:
```bash
# 1. Referenzen im Text extrahieren (z.B. "gemäß § 7 SGB II")
python scripts/extract_cross_references.py --source neo4j

# 2. REFERS_TO Relationships erstellen
python scripts/create_cross_reference_relationships.py
```

**Erwartete Beziehungen**:
```cypher
(:LegalNorm {paragraph: '§ 11 SGB II'})-[:REFERS_TO]->(:LegalNorm {paragraph: '§ 7 SGB II'})
```

**Nutzen für Sachbearbeiter**:
- Navigation zwischen verbundenen Normen
- "Welche Normen verweisen auf § 7?" → Zeigt Kontext
- Graph-basierte Rechtsauslegung

**Verantwortlich**: NLP Engineering + Juristische QA  
**Deadline**: KW 10/2025

---

## Phase 3: Performance-Optimierung (Priorität: P2)

### 3.1 Compound Indexes anlegen

```cypher
// Index für häufige Sachbearbeiter-Queries
CREATE INDEX legal_norm_sgb_paragraph IF NOT EXISTS
FOR (n:LegalNorm)
ON (n.sgb_nummer, n.paragraph_nummer);

// Index für Chunk-Suche
CREATE INDEX chunk_sgb_embedding IF NOT EXISTS
FOR (c:Chunk)
ON (c.sgb_nummer);

// Full-text Index für Content-Suche
CREATE FULLTEXT INDEX norm_content_fulltext IF NOT EXISTS
FOR (n:LegalNorm)
ON EACH [n.content_text, n.titel];
```

**Verantwortlich**: Database Administrator  
**Deadline**: KW 7/2025

---

### 3.2 Direkte Document→Norm Links (Optional)

**Ziel**: Query-Performance für häufige Abfragen verbessern

```cypher
// Aktuell: Document → Structure → Norm (2 Hops)
// Neu: Document → Norm (1 Hop, zusätzlich)
MATCH (doc:LegalDocument)-[:HAS_STRUCTURE]->(s:StructuralUnit)-[:CONTAINS_NORM]->(n:LegalNorm)
MERGE (doc)-[:CONTAINS_NORM_DIRECT]->(n)
```

**Trade-off**:
- ✅ Schnellere Queries
- ❌ Mehr Relationships (höherer Speicherbedarf)
- ❌ Wartungsaufwand bei Updates

**Entscheidung**: Erst nach Load-Tests in Produktion

**Verantwortlich**: Performance Engineering  
**Deadline**: KW 12/2025 (nach Prod-Launch)

---

## Phase 4: Use Case Validation & Testing (Priorität: P0)

### 4.1 Use Case Testing gegen reale Daten

**Prozess**:
1. **Use Cases aus Cypher-Scripts extrahieren**
   ```bash
   ls tests/cypher_queries/UC*.cypher
   ```

2. **Automatisierte Tests schreiben**
   ```python
   # tests/test_use_cases.py
   def test_uc01_regelbedarfe_sgb_ii():
       result = session.run(open('tests/cypher_queries/UC01.cypher').read())
       assert len(result) > 0, "UC01 returned no results"
   ```

3. **Coverage-Report generieren**
   ```bash
   pytest tests/test_use_cases.py --html=reports/use_case_coverage.html
   ```

**Siehe separate Datei**: `USE_CASE_VALIDATION.md` (wird unten erstellt)

**Verantwortlich**: QA + Product  
**Deadline**: KW 7/2025

---

### 4.2 End-to-End User Journeys testen

**Testszenarien** (siehe `BENUTZER_JOURNEYS_DE.md`):
1. Sachbearbeiter: Regelbedarfsermittlung
2. Sachbearbeiter: Sanktionsprüfung
3. Prozessberater: Prozessoptimierung Antragsprüfung
4. Prozessberater: Compliance-Audit

**Testwerkzeuge**:
- Selenium für UI-Tests
- API-Tests für Backend
- Neo4j-Queries für Datenvalidierung

**Verantwortlich**: QA  
**Deadline**: KW 8/2025

---

## Phase 5: Produktionsreife (Priorität: P0)

### 5.1 Monitoring & Alerting einrichten

**Metriken**:
```python
# Täglich zu überwachende KPIs
- Anzahl zugänglicher Chunks pro SGB
- Query Response Time (p95, p99)
- Orphaned Norms Count
- Vector Index Health
- Embedding API Verfügbarkeit
```

**Alerting-Regeln**:
- Wenn Chunk-Zugriff < 35% → Critical Alert
- Wenn Query Latency > 2s → Warning
- Wenn Orphaned Norms > 1000 → Warning

**Tools**: Prometheus + Grafana + Neo4j OpsManager

**Verantwortlich**: DevOps  
**Deadline**: KW 9/2025

---

### 5.2 Backup & Recovery Strategy

```bash
# Tägliche Backups
neo4j-admin database dump neo4j --to-path=/backups/$(date +%Y%m%d)

# Wöchentliche Full Backups mit Langzeitarchivierung
# Monatliche Disaster Recovery Tests
```

**Verantwortlich**: DevOps  
**Deadline**: Vor Prod-Launch (KW 9/2025)

---

### 5.3 Dokumentation & Training

**Dokumentation**:
- ✅ SGB Coverage Analysis (fertig)
- ✅ Aktionsplan (dieses Dokument)
- ⏳ API-Dokumentation (OpenAPI/Swagger)
- ⏳ Admin-Handbuch (Neo4j Wartung)
- ⏳ User-Handbuch (Sachbearbeiter/Prozessberater)

**Training**:
1. **Entwickler-Onboarding** (2 Tage)
   - Graph-Datenmodell
   - Cypher-Queries
   - RAG-Pipeline

2. **Sachbearbeiter-Schulung** (1 Tag)
   - Systemnutzung
   - Suchstrategien
   - Feedback geben

3. **Admin-Training** (1 Tag)
   - Neo4j Wartung
   - Daten-Import
   - Troubleshooting

**Verantwortlich**: Product + Engineering  
**Deadline**: KW 8-9/2025

---

## Phase 6: Continuous Improvement (Priorität: P2)

### 6.1 Feedback-Loop etablieren

**Prozess**:
1. Sachbearbeiter loggen problematische Queries
2. Wöchentliches Review-Meeting
3. Priorisierung & Sprint-Planung
4. Datenqualität verbessern oder Features anpassen

**Tool**: Feedback-Button in UI + Jira-Integration

**Verantwortlich**: Product Owner  
**Start**: Mit Prod-Launch

---

### 6.2 Automatisierte Daten-Updates

**Ziel**: Gesetzesänderungen automatisch erfassen

**Ansatz**:
1. Web-Scraping von gesetze-im-internet.de
2. Diff-Detection gegen aktuellen Graph
3. Amendment-Knoten automatisch anlegen
4. Manuelle Review vor Veröffentlichung

**Frequenz**: Wöchentlich

**Verantwortlich**: Data Engineering  
**Start**: Q2 2025

---

## Zusammenfassung: Roadmap

| Phase | Priorität | Deadline | Status |
|-------|-----------|----------|--------|
| **Phase 1: Datenvollständigkeit** | P0 | KW 6/2025 | 🟡 In Arbeit |
| **Phase 2: Datenqualität** | P1 | KW 10/2025 | 🔴 Offen |
| **Phase 3: Performance** | P2 | KW 12/2025 | 🔴 Offen |
| **Phase 4: Use Case Validation** | P0 | KW 8/2025 | 🟡 Teilweise |
| **Phase 5: Produktionsreife** | P0 | KW 9/2025 | 🔴 Offen |
| **Phase 6: Continuous Improvement** | P2 | Q2 2025 | 🔴 Offen |

---

## Erfolgskriterien

### Minimum Viable Product (MVP)
- ✅ 7 SGBs mit Chunks funktionsfähig (II, III, IV, V, VI, VIII, XI)
- ✅ 40.5% Chunk-Coverage
- ⏳ 10 Use Cases erfolgreich getestet
- ⏳ Response Time < 2s (p95)
- ⏳ Admin-Dokumentation vorhanden

### Production Ready
- ⏳ 12 SGBs mit Chunks (alle)
- ⏳ 70-80% Chunk-Coverage
- ⏳ 20 Use Cases erfolgreich getestet
- ⏳ Amendment-Coverage > 20%
- ⏳ Monitoring & Alerting aktiv
- ⏳ Backup & Recovery getestet
- ⏳ User-Training durchgeführt

### Long-term Excellence
- ⏳ 90%+ Chunk-Coverage
- ⏳ Cross-References vollständig
- ⏳ Automatisierte Daten-Updates
- ⏳ < 100 orphaned Norms
- ⏳ User Satisfaction Score > 4/5

---

**Nächste Schritte (diese Woche)**:
1. ✅ Orphaned Norms repariert
2. Fehlende SGB-Chunks identifizieren und Import planen
3. Use Case Validation Script schreiben
4. Team-Meeting zur Roadmap-Abstimmung
