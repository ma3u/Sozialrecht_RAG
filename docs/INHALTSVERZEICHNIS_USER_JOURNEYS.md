# Inhaltsverzeichnis: Benutzer-Journeys

**Dokument**: [BENUTZER_JOURNEYS_DE.md](BENUTZER_JOURNEYS_DE.md)  
**Status**: 12/20 produktionsreif ✅

---

## Schnellnavigation

### Nach Status
- [✅ Produktionsreife Journeys (12)](#produktionsreife-journeys)
- [⚠️ Eingeschränkte Journeys (5)](#eingeschränkte-journeys)
- [❌ Nicht verfügbare Journeys (3)](#nicht-verfügbare-journeys)

### Nach Zielgruppe
- [👔 Sachbearbeiter-Journeys (1-12)](#sachbearbeiter-journeys-1-12)
- [📊 Prozessberater-Journeys (13-20)](#prozessberater-journeys-13-20)

### Nach SGB
- [SGB II Journeys](#sgb-ii-schwerpunkt)
- [Cross-SGB Journeys](#cross-sgb-journeys)
- [SGB X Journeys](#sgb-x-verfahrensrecht)

---

## Produktionsreife Journeys

### ✅ MVP-Ready: Sofort einsetzbar (12 Journeys)

#### Regelbedarfe & Leistungen
1. **[UC01: Regelbedarfsermittlung für Familie](#uc01-regelbedarfsermittlung)** ⭐⭐⭐⭐⭐
   - **Status**: Vollständig funktionsfähig
   - **SGB**: II (§§ 20-23)
   - **Daten**: 50 Normen, 436 Chunks
   - **Use Case**: Alleinerziehende Mutter mit 8-jährigem Kind
   - **Tool**: Neo4j Browser + Cypher

3. **[UC03: Einkommensanrechnung komplexer Fall](#uc03-einkommensanrechnung)** ⭐⭐⭐⭐⭐
   - **Status**: Vollständig funktionsfähig
   - **SGB**: II (§§ 11, 11b)
   - **Daten**: 14 Normen, 104 Chunks
   - **Use Case**: Minijob + Kindergeld + Unterhalt
   - **Tool**: Neo4j Browser + Python Berechnungsmodul

5. **[UC05: Umzugskostenübernahme](#uc05-umzugskosten)** ⭐⭐⭐⭐
   - **Status**: Vollständig funktionsfähig
   - **SGB**: II (§ 22)
   - **Daten**: 15 Normen, 120 Chunks
   - **Tool**: Neo4j Browser

6. **[UC06: Bedarfsgemeinschaft vs. Haushaltsgemeinschaft](#uc06-bedarfsgemeinschaft)** ⭐⭐⭐⭐⭐
   - **Status**: Vollständig funktionsfähig
   - **SGB**: II (§ 7)
   - **Daten**: 25 Normen, 180 Chunks (zentrale Norm!)
   - **Tool**: Neo4j Browser + Graph Visualisierung

7. **[UC07: Eingliederungsvereinbarung erstellen](#uc07-eingliederungsvereinbarung)** ⭐⭐⭐⭐
   - **Status**: Vollständig funktionsfähig
   - **SGB**: II (§ 15)
   - **Daten**: 12 Normen, 88 Chunks
   - **Tool**: Neo4j Browser

8. **[UC08: Darlehen für Erstausstattung](#uc08-erstausstattung)** ⭐⭐⭐⭐⭐
   - **Status**: Vollständig funktionsfähig
   - **SGB**: II (§ 24)
   - **Daten**: 18 Normen, 144 Chunks
   - **Tool**: Neo4j Browser

#### Sanktionen & Rückforderungen
2. **[UC02: Sanktionsprüfung bei Meldeversäumnis](#uc02-sanktionsprüfung)** ⭐⭐⭐⭐
   - **Status**: Vollständig funktionsfähig
   - **SGB**: II (§ 32)
   - **Daten**: 13 Normen, 58 Chunks
   - **Use Case**: Drittes Meldeversäumnis
   - **Tool**: Neo4j Browser

4. **[UC04: Erstattungsanspruch bei Vermögen](#uc04-erstattung)** ⭐⭐⭐⭐
   - **Status**: Vollständig funktionsfähig (SGB II)
   - **SGB**: II (§§ 12, 50)
   - **Daten**: 14 Normen, 104 Chunks
   - **Tool**: Neo4j Browser

#### Verwaltungsverfahren
11. **[UC11: Weiterbewilligungsantrag nach 1 Jahr](#uc11-weiterbewilligung)** ⭐⭐⭐⭐
    - **Status**: Vollständig funktionsfähig
    - **SGB**: II (§ 41)
    - **Daten**: 8 Normen, 64 Chunks
    - **Tool**: Neo4j Browser

12. **[UC12: Hausbesuch - Wohnsituation prüfen](#uc12-hausbesuch)** ⭐⭐⭐
    - **Status**: Funktionsfähig für SGB II
    - **SGB**: II (§§ 60-62)
    - **Tool**: Neo4j Browser

#### Prozessberater: Analyse & Optimierung
13. **[UC13: Prozessanalyse Durchlaufzeiten](#uc13-prozessanalyse)** ⭐⭐⭐⭐
    - **Status**: Vollständig funktionsfähig
    - **SGB**: II (§§ 37, 41, 44)
    - **Daten**: Fristen und Zeiträume vollständig
    - **Tool**: Neo4j Browser + Python Analytics

16. **[UC16: Qualitätssicherung Fehlerquellen](#uc16-qualitätssicherung)** ⭐⭐⭐⭐
    - **Status**: Vollständig funktionsfähig
    - **SGB**: II (Komplexitätsanalyse)
    - **Tool**: Neo4j Browser + Cypher Analytics

17. **[UC17: Benchmark-Analyse Ablehnungsgründe](#uc17-benchmark)** ⭐⭐⭐⭐
    - **Status**: Vollständig funktionsfähig
    - **SGB**: II (§§ 7, 9, 11, 12)
    - **Tool**: Neo4j Browser + BI-Dashboard

18. **[UC18: Prozessmodellierung Ideal-Prozess](#uc18-prozessmodellierung)** ⭐⭐⭐⭐⭐
    - **Status**: Vollständig funktionsfähig
    - **SGB**: II (§§ 7, 11, 11b, 12, 37, 33)
    - **Tool**: Neo4j Browser + BPMN Modeler

---

## Eingeschränkte Journeys

### ⚠️ Teilweise funktionsfähig (5 Journeys)

9. **[UC09: Krankenversicherung bei Leistungsbezug](#uc09-krankenversicherung)** ⭐⭐⭐
   - **Status**: Nur SGB II-Seite funktionsfähig
   - **SGB**: II ✅ + V ❌ (§ 5 fehlt)
   - **Problem**: SGB V Chunks fehlen
   - **Tool**: Neo4j Browser (eingeschränkt)
   - **Fix**: SGB V Chunks importieren

10. **[UC10: Widerspruch bearbeiten](#uc10-widerspruch)** ⭐
    - **Status**: Nicht funktionsfähig
    - **SGB**: X ❌ (§§ 79, 80, 84, 85 fehlen komplett)
    - **Problem**: SGB X komplett ohne Chunks
    - **Priorität**: **P0 - CRITICAL**
    - **Tool**: -
    - **Fix**: SGB X Import zwingend erforderlich

14. **[UC14: Compliance-Check Datenschutz](#uc14-compliance)** ⭐
    - **Status**: Nicht funktionsfähig
    - **SGB**: X ❌ (§§ 67-85 fehlen)
    - **Problem**: Sozialdatenschutz nicht abgedeckt
    - **Priorität**: **P1 - HIGH**
    - **Tool**: -
    - **Fix**: SGB X Import

15. **[UC15: Schnittstellenanalyse SGB II ↔ III](#uc15-schnittstellen)** ⭐⭐⭐
    - **Status**: Manuelle Analyse möglich
    - **SGB**: II ✅ + III ✅
    - **Problem**: Keine automatischen Cross-References
    - **Tool**: Neo4j Browser + Manual Search
    - **Fix**: REFERS_TO-Relationships erstellen

20. **[UC20: Risikomanagement Rückforderungen](#uc20-risikomanagement)** ⭐⭐⭐
    - **Status**: Nur SGB II-Seite
    - **SGB**: II ✅ + X ❌ (Verfahrensrecht fehlt)
    - **Tool**: Neo4j Browser (eingeschränkt)
    - **Fix**: SGB X Import

---

## Nicht verfügbare Journeys

### ❌ Erfordern zusätzliche Daten (3 Journeys)

19. **[UC19: Schulungskonzept Gesetzesänderungen](#uc19-schulungskonzept)** ⭐
    - **Status**: Nicht funktionsfähig
    - **SGB**: II (Amendment-Daten fehlen)
    - **Problem**: Nur 0.5% Amendment-Coverage
    - **Priorität**: **P1 - HIGH**
    - **Tool**: -
    - **Fix**: Amendment-Import + Bürgergeld-Reform 2023 erfassen

**Verbleibende Journeys**: Siehe [USE_CASE_VALIDATION.md](USE_CASE_VALIDATION.md) für Details

---

## Sachbearbeiter-Journeys (1-12)

| # | Journey | SGB | Status | Daten |
|---|---------|-----|--------|-------|
| 1 | [Regelbedarfsermittlung](#uc01-regelbedarfsermittlung) | II | ✅ | 50N / 436C |
| 2 | [Sanktionsprüfung](#uc02-sanktionsprüfung) | II | ✅ | 13N / 58C |
| 3 | [Einkommensanrechnung](#uc03-einkommensanrechnung) | II | ✅ | 14N / 104C |
| 4 | [Erstattungsanspruch](#uc04-erstattung) | II | ✅ | 14N / 104C |
| 5 | [Umzugskostenübernahme](#uc05-umzugskosten) | II | ✅ | 15N / 120C |
| 6 | [Bedarfsgemeinschaft](#uc06-bedarfsgemeinschaft) | II | ✅ | 25N / 180C |
| 7 | [Eingliederungsvereinbarung](#uc07-eingliederungsvereinbarung) | II | ✅ | 12N / 88C |
| 8 | [Erstausstattung](#uc08-erstausstattung) | II | ✅ | 18N / 144C |
| 9 | [Krankenversicherung](#uc09-krankenversicherung) | II+V | ⚠️ | 13N / 92C |
| 10 | [Widerspruch](#uc10-widerspruch) | X | ❌ | 0N / 0C |
| 11 | [Weiterbewilligung](#uc11-weiterbewilligung) | II | ✅ | 8N / 64C |
| 12 | [Hausbesuch](#uc12-hausbesuch) | II | ✅ | Vorhanden |

**Legende**: N = Normen, C = Chunks

---

## Prozessberater-Journeys (13-20)

| # | Journey | SGB | Status | Tool |
|---|---------|-----|--------|------|
| 13 | [Prozessanalyse Durchlaufzeiten](#uc13-prozessanalyse) | II | ✅ | Analytics |
| 14 | [Compliance Datenschutz](#uc14-compliance) | X | ❌ | - |
| 15 | [Schnittstellenanalyse II↔III](#uc15-schnittstellen) | II+III | ⚠️ | Manual |
| 16 | [Qualitätssicherung Fehlerquellen](#uc16-qualitätssicherung) | II | ✅ | Analytics |
| 17 | [Benchmark Ablehnungsgründe](#uc17-benchmark) | II | ✅ | BI |
| 18 | [Prozessmodellierung Ideal-Prozess](#uc18-prozessmodellierung) | II | ✅ | BPMN |
| 19 | [Schulungskonzept Änderungen](#uc19-schulungskonzept) | II | ❌ | - |
| 20 | [Risikomanagement](#uc20-risikomanagement) | II+X | ⚠️ | Partial |

---

## Nach SGB-Schwerpunkt

### SGB II Schwerpunkt
✅ **Vollständig funktionsfähig** (7,854 Chunks):
- UC01-UC08, UC11-UC13, UC16-UC18

### Cross-SGB Journeys
⚠️ **Teilweise funktionsfähig**:
- UC09 (II + V): SGB V fehlt
- UC15 (II + III): Cross-References fehlen
- UC20 (II + X): SGB X fehlt

### SGB X Verfahrensrecht
❌ **Nicht funktionsfähig** (0 Chunks):
- UC10: Widerspruchsverfahren
- UC14: Datenschutz-Compliance
- **Priorität P0**: Blocking für Produktion!

---

## Empfohlene Reihenfolge für MVP-Start

### Phase 1: Core Sachbearbeiter-Workflows (Woche 1-2)
1. ✅ UC01: Regelbedarfsermittlung ⭐⭐⭐⭐⭐
2. ✅ UC06: Bedarfsgemeinschaft ⭐⭐⭐⭐⭐
3. ✅ UC03: Einkommensanrechnung ⭐⭐⭐⭐⭐
4. ✅ UC08: Erstausstattung ⭐⭐⭐⭐⭐

→ **4 Use Cases mit höchster Datenqualität**

### Phase 2: Erweiterte Workflows (Woche 3-4)
5. ✅ UC02: Sanktionen
6. ✅ UC05: Umzug
7. ✅ UC07: Eingliederungsvereinbarung
8. ✅ UC04: Erstattung

→ **8 Use Cases = Kompletter Sachbearbeiter-MVP**

### Phase 3: Prozessberater-Tools (Woche 5-6)
9. ✅ UC18: Prozessmodellierung ⭐⭐⭐⭐⭐
10. ✅ UC16: Qualitätssicherung
11. ✅ UC13: Prozessanalyse
12. ✅ UC17: Benchmark

→ **12 Use Cases = Vollständiger MVP**

---

## Tooling-Empfehlungen pro Use Case

| Tool | Use Cases | Zweck |
|------|-----------|-------|
| **Neo4j Browser** | UC01-UC12, UC13-UC18 | Interaktive Queries & Visualisierung |
| **Neo4j Bloom** | UC06, UC15, UC18 | Graph-Exploration & Beziehungsanalyse |
| **Python + Pandas** | UC03, UC13, UC16, UC17 | Datenanalyse & Berechnungen |
| **Jupyter Notebook** | UC13, UC16, UC17 | Explorative Analyse & Reporting |
| **Streamlit/Dash** | UC18, UC20 | Dashboards für Prozessberater |
| **BPMN Modeler** | UC18 | Prozessmodellierung |
| **Grafana** | UC13, UC17 | Monitoring & KPI-Dashboards |

---

## Nächste Schritte

### 1. MVP mit 12 produktionsreifen Use Cases starten ✅
**Empfehlung**: Beginnen mit UC01, UC03, UC06, UC08
- Cypher-Queries testen
- Python-Integration aufbauen
- UI-Prototyp entwickeln

### 2. SGB X Chunks importieren 🔴 P0
**Blocking für**:
- UC10: Widerspruchsverfahren
- UC14: Datenschutz-Compliance
- UC20: Risikomanagement (vollständig)

**Action**: Siehe [AKTIONSPLAN_NACH_ANALYSE.md](AKTIONSPLAN_NACH_ANALYSE.md) Phase 1.1

### 3. Amendment-Daten für Schulungen erfassen 🟡 P1
**Erforderlich für**:
- UC19: Schulungskonzept
- Historische Navigation
- Änderungsdokumentation

**Action**: Siehe [AKTIONSPLAN_NACH_ANALYSE.md](AKTIONSPLAN_NACH_ANALYSE.md) Phase 2.1

---

## Detaillierte Use Case Dokumentation

Für vollständige Beschreibungen mit BPMN-Diagrammen, Cypher-Queries und Erfolgskriterien siehe:

📖 **[BENUTZER_JOURNEYS_DE.md](BENUTZER_JOURNEYS_DE.md)**

Für Datenvalidierung und Qualitätsbewertung siehe:

📊 **[USE_CASE_VALIDATION.md](USE_CASE_VALIDATION.md)**

Für Implementierungs-Roadmap siehe:

🗺️ **[AKTIONSPLAN_NACH_ANALYSE.md](AKTIONSPLAN_NACH_ANALYSE.md)**

---

**Letzte Aktualisierung**: Januar 2025  
**Status**: 12/20 Use Cases produktionsreif ✅
