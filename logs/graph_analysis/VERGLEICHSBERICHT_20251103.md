# 📊 VERGLEICHSBERICHT: Graph-Qualität Analyse

**Vergleich:** 01.11.2025 vs 03.11.2025  
**Erstellt:** 2025-11-03 09:05:00

---

## 🎯 Executive Summary

### Hauptveränderungen

| Metrik | 01.11.2025 | 03.11.2025 | Änderung |
|--------|------------|------------|----------|
| **Gesamte Rechtsnormen** | 4,213 | 4,223 | +10 (+0.2%) ✅ |
| **RAG Chunks** | 41,747 | 41,781 | +34 (+0.08%) ✅ |
| **Orphaned Nodes** | ? | 9 | Stabil 📊 |
| **Embeddings** | 0 | 10 | +10 ⚠️ |
| **SGB Bücher** | 13 | 13 | Stabil ✅ |
| **PDF Dokumente** | 50 | 50 | Stabil ✅ |

---

## 📈 Detaillierte Analyse

### 1. Graph-Struktur

#### Node-Typen (aktueller Stand)
```
Chunk                     41,781
TextUnit                  11,145
Paragraph                  4,254
LegalNorm                  4,223
StructuralUnit               458
Document                      50
Amendment                     21
LegalDocument                 13
```

#### Relationship-Typen
```
HAS_CHUNK                 41,781
HAS_CONTENT               11,145
CONTAINS_PARAGRAPH         5,050
CONTAINS_NORM              5,008
HAS_STRUCTURE                717
HAS_AMENDMENT                 21
```

**Bewertung:** ✅ Graph-Struktur stabil und vollständig

---

### 2. Verwaiste Knoten (Orphans)

#### Aktuelle Orphans (03.11.2025)
- **Total:** 9 Nodes
- **Pattern:** Alle gehören zu DOKNR `BJNR104600001`
- **Typen:** 
  - 7x Document (orphans)
  - 1x LegalNorm (orphan)
  - 1x weitere verwaiste Nodes

#### Details zu BJNR104600001
```
Eingangsformel
Inhaltsübersicht
Art 1, Art 63, Art 64 (Rückkehr zum einheitlichen Verordnungsrang)
Art 65 (Neubekanntmachung)
Art 66, Art 67 (Übergangsvorschriften)
Art 68 (Inkrafttreten)
```

**Analyse:**  
- BJNR104600001 = Unbekanntes Gesetz (noch nicht gemappt)
- Artikel-Struktur deutet auf Änderungsgesetz hin
- Niedrige Priorität (9 Chunks von 41.781 = 0.02%)

**Empfehlung:**
- ⚠️ **PRIORITY: HIGH** - DOKNR Mapping recherchieren
- 💡 Alternativ: Als Referenz-Normen markieren und separaten Index erstellen

---

### 3. RAG-Abdeckung pro SGB

#### Problematische SGBs (mehr fehlende Chunks am 03.11.)

| SGB | Fehlende Chunks (01.11) | Fehlende Chunks (03.11) | Änderung |
|-----|------------------------|------------------------|----------|
| **SGB III** | 300 | 444 | +144 ⚠️ |
| **SGB V** | 283 | 422 | +139 ⚠️ |
| **SGB VI** | 223 | 364 | +141 ⚠️ |
| **SGB VII** | 228 | 312 | +84 ⚠️ |
| **SGB XI** | 202 | 268 | +66 ⚠️ |

**Analyse:**  
Die Anzahl der **Normen ohne Chunks ist gestiegen**, was bedeutet:
- Neue Rechtsnormen wurden importiert (+10 Normen)
- Aber: Chunk-Verlinkung ist **nicht automatisch** erfolgt
- Graph-Struktur wurde erweitert, aber RAG-Pfade fehlen teilweise

**Kritischer Punkt:** 
Die Diskrepanz zeigt, dass neue Normen importiert wurden, aber die Chunk-Generierung oder -Verlinkung nicht nachgezogen hat.

---

### 4. Embedding-Status

#### Embedding-Abdeckung
```
Gesamt Chunks:        41,781
Mit Embeddings:           10  (0.02%)
Fehlende Embeddings:  41,771  (99.98%)
```

**Status:** 🔴 **KRITISCH**

**Impact auf RAG:**
- Vector Search funktioniert nur für 10 von 41.781 Chunks
- Semantische Suche ist praktisch nicht nutzbar
- Query-Ergebnisse sind stark eingeschränkt

**Lösung in Arbeit:**
```bash
python scripts/generate_embeddings_azure.py --execute --batch --limit 50000
```

**Geschätzte Zeit:** ~60 Minuten für alle 41.781 Chunks  
**Kosten:** ~€0.75 (Azure OpenAI text-embedding-3-large)

---

### 5. Graph-Qualität Metriken

#### Durchschnittliche Konnektivität
```
Document:             548.00 Verbindungen/Node ✅
LegalDocument:        385.23 Verbindungen/Node ✅
LegalNorm:              8.43 Verbindungen/Node ✅
StructuralUnit:         3.13 Verbindungen/Node ✅
Paragraph:              1.19 Verbindungen/Node ⚠️
Chunk:                  1.00 Verbindungen/Node ⚠️
TextUnit:               1.00 Verbindungen/Node ⚠️
```

**Bewertung:**
- ✅ Obere Ebenen (Document, LegalDocument) gut vernetzt
- ⚠️ Untere Ebenen (Paragraph, Chunk) haben minimale Konnektivität
  - **Grund:** Chunks sind "Leaf Nodes" (Endpunkte im Graph)
  - **Erwartungskonform** für diese Architektur

#### Relationship-Dichte
```
Nodes:          61,945
Relationships:  63,722
Durchschnitt:    1.03 Relationships/Node
```

**Bewertung:** ⚠️ Niedrige Dichte, aber **architekturbedingt korrekt**
- Viele Leaf-Nodes (Chunks, TextUnits) haben nur 1 eingehende Beziehung
- Higher-Level Nodes sind stark vernetzt

---

## 🚨 Kritische Befunde

### 1. Embedding-Abdeckung (HÖCHSTE PRIORITÄT)
**Problem:** Nur 0.02% der Chunks haben Embeddings  
**Impact:** RAG-System faktisch nicht nutzbar  
**Lösung:** Vollständige Embedding-Generierung  
**ETA:** 60 Minuten

### 2. Chunk-Verlinkung für neue Normen
**Problem:** +144 bis +141 neue "Norms without Chunks" in verschiedenen SGBs  
**Impact:** Neue Rechtsnormen nicht im RAG-System verfügbar  
**Lösung:** Prüfen ob:
- Chunks existieren aber nicht verlinkt sind
- Chunks noch nicht generiert wurden

### 3. DOKNR Orphans
**Problem:** 9 Nodes ohne Graph-Verbindung (BJNR104600001)  
**Impact:** Minimal (0.02% der Chunks)  
**Lösung:** DOKNR Mapping oder als Referenz-Normen markieren

---

## ✅ Positive Entwicklungen

1. **+10 neue Rechtsnormen** importiert
2. **+34 neue Chunks** verfügbar
3. **Graph-Struktur stabil** (alle 13 SGBs vorhanden)
4. **Orphan-Anzahl niedrig** (9 von 61.945 Nodes = 0.01%)
5. **Konnektivität der oberen Ebenen exzellent** (385-548 Connections/Node)

---

## 📋 Action Items (Priorisiert)

### 🔴 PRIORITÄT 1: Embedding-Generierung
```bash
python scripts/generate_embeddings_azure.py --execute --batch --limit 50000
```
**Zeitaufwand:** 60 Minuten  
**Resultat:** Vollständig funktionsfähiges RAG-System

### 🟡 PRIORITÄT 2: Chunk-Verlinkung prüfen
```bash
# Prüfe ob Chunks existieren aber nicht verlinkt sind
python scripts/analyze_chunk_linking.py --sgb III,V,VI,VII,XI
```

### 🟢 PRIORITÄT 3: DOKNR Mapping
```bash
# Recherchiere BJNR104600001
# Erstelle Mapping oder markiere als Referenz-Norm
```

---

## 📊 Vergleichstabelle: Sachbearbeiter-Sicht

### Workflow-Abdeckung

| Use Case | 01.11.2025 | 03.11.2025 | Status |
|----------|------------|------------|--------|
| **UC1: Regelbedarfe (§ 20 SGB II)** | ✅ Path: 1, Chunks: 96 | ✅ Path: 1, Chunks: 96 | Stabil |
| **Leistungsberechtigung** | Total: 39 Norms, 274 Chunks | Total: 39 Norms, 274 Chunks | Stabil |

### SGB-Abdeckung Trend

**Problematik:** Alle 13 SGBs zeigen "Complete Path = ❌"

**Grund:** Chunks sind mit Normen verbunden, aber der Sachbearbeiter-Report zeigt "0 Chunks" in der Tabelle.

**Mögliche Ursache:**
- Report-Query zählt nur Chunks die **direkt** über `LegalDocument` → `Norm` → `Chunk` verlinkt sind
- Tatsächliche Chunks existieren aber über `Document` → `Chunk` Pfad

**Empfehlung:** Report-Query anpassen um beide Pfade zu berücksichtigen

---

## 🎯 Fazit

### Graph-Qualität: **7/10** ⭐⭐⭐⭐⭐⭐⭐

**Stärken:**
- ✅ Vollständige Datenstruktur (13 SGBs, 4.223 Normen)
- ✅ Hohe Konnektivität auf Document/LegalDocument-Ebene
- ✅ Minimale Orphan-Rate (0.01%)
- ✅ Stabile Graph-Architektur

**Schwächen:**
- 🔴 Keine Embeddings → RAG funktionsunfähig (99.98% missing)
- 🟡 Chunk-Verlinkung inkonsistent für neue Normen
- 🟢 9 Orphan-Nodes (niedrige Priorität)

### Empfehlung
**Sofort:** Embedding-Generierung starten (60 Min)  
**Dann:** Chunk-Verlinkung für neue Normen prüfen  
**Optional:** DOKNR Mapping vervollständigen

### Erwartetes Ergebnis nach Embedding-Generierung
**Graph-Qualität: 9/10** ⭐⭐⭐⭐⭐⭐⭐⭐⭐

---

**Autor:** Graph Analysis System  
**Timestamp:** 2025-11-03T09:05:00Z  
**Nächste Analyse:** Nach Embedding-Generierung
