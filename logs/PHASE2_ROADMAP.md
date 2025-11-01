# Phase 2 Roadmap: Datenqualität verbessern

**Start**: Nach Phase 1 Abschluss  
**Priorität**: P1 - HIGH  
**Ziel**: UC14 vollständig funktionsfähig + Datenqualität erhöhen

---

## Status nach Phase 1

### ✅ Erfolge
- Coverage: 17.5% → 46.4% (+29%)
- Orphaned Norms: 2,830 → 9 (-99.7%)
- SGB X verfügbar: 86 Normen, 270 Chunks (68.6% Coverage)
- UC10 produktionsreif (100% Coverage)
- MVP: 13 von 20 Use Cases (65%)

### ⚠️ Verbleibende Lücken

**UC14 (Datenschutz-Compliance)**: 42% Coverage
- ✅ Verfügbar: §§ 78-85 (48 Chunks)
- ❌ Fehlt: §§ 67-76 (Sozialdaten-Grundlagen)

**Analyse**: Paragraphen 67-76 sind **nicht in Neo4j vorhanden**
- Nicht als orphaned Norms
- Nicht als verlinkte Norms
- **Strukturelle Lücke im Datenimport**

---

## Phase 2: Prioritäten

### 2.1 UC14 vervollständigen (P1)

**Problem**: §§ 67-76 fehlen komplett in Datenbank

**Ursache**: 
1. Entweder bei XML-Import übersprungen
2. Oder bei Chunking-Pipeline nicht verarbeitet
3. Oder CONTAINS_NORM Relationship fehlt (unwahrscheinlich, da Normen selbst nicht da sind)

**Lösung**:
1. ✅ **Quelldaten prüfen**
   - `ls Datenquellen/SGB/`
   - XML/JSON für SGB X §§ 67-76 vorhanden?

2. 📥 **Import/Re-Import**
   - Wenn Quelldaten vorhanden: Re-Import für §§ 67-76
   - Wenn fehlen: Gesetzestexte von gesetze-im-internet.de holen

3. 🔗 **Chunking & Linking**
   - Paragraphen in Chunks aufteilen
   - CONTAINS_NORM Relationships erstellen
   - HAS_CHUNK Relationships erstellen

4. ✅ **Validierung**
   - UC14 Test erneut ausführen
   - Erwartung: Coverage 42% → 100%

---

## Phase 2 Aufgaben im Detail

### 2.1.1 Datenquellen prüfen ⏳

**Script**: `scripts/check_sgb_x_sources.py`

```python
#!/usr/bin/env python3
"""
Prüft ob SGB X Quelldaten für §§ 67-76 vorhanden sind
"""
import os
import json
from pathlib import Path

sgb_x_path = Path("Datenquellen/SGB/X")

if sgb_x_path.exists():
    # Prüfe XML/JSON Dateien
    for file in sgb_x_path.glob("*.{xml,json}"):
        print(f"Gefunden: {file}")
        # Parse und prüfe ob §§ 67-76 enthalten
else:
    print(f"❌ Quelldaten-Verzeichnis nicht gefunden: {sgb_x_path}")
```

**Erwartetes Ergebnis**:
- Quelldaten vorhanden → Re-Import
- Quelldaten fehlen → Externe Beschaffung

---

### 2.1.2 Fehlende Paragraphen importieren 📥

**Option A: Re-Import aus vorhandenen Quellen**

Wenn Quelldaten vorhanden:
```bash
# Import-Pipeline neu ausführen für SGB X §§ 67-76
python scripts/import_sgb_norms.py --sgb X --paragraphs 67-76
```

**Option B: Externe Beschaffung**

Falls Quelldaten fehlen:
1. Download von gesetze-im-internet.de
   ```bash
   curl "https://www.gesetze-im-internet.de/sgb_10/index.html" > sgb_x_raw.html
   ```

2. Parsing mit BeautifulSoup
   ```python
   from bs4 import BeautifulSoup
   # Parse HTML → Extract §§ 67-76
   ```

3. Strukturierung als JSON
   ```json
   {
     "sgb": "X",
     "paragraph": "67",
     "titel": "Sozialdaten",
     "text": "(1) Sozialdaten sind Einzelangaben..."
   }
   ```

4. Import in Neo4j
   ```bash
   python scripts/import_external_norms.py --file sgb_x_67-76.json
   ```

---

### 2.1.3 Chunking & Linking 🔗

**Chunking-Pipeline**:
```bash
# Chunks für §§ 67-76 erstellen
python scripts/chunk_norms.py --sgb X --paragraphs 67-76
```

**Erwartete Ausgabe**:
- § 67: ~8 Chunks (Definitionen)
- § 68: ~12 Chunks (Verarbeitung)
- § 69: ~10 Chunks (Geheimnis)
- § 70-76: ~30 Chunks

**Gesamt**: ~60 neue Chunks

**Linking**:
```cypher
// CONTAINS_NORM erstellen
MATCH (doc:LegalDocument {sgb_nummer: 'X'})
MATCH (norm:LegalNorm)
WHERE norm.paragraph_nummer IN ['67', '68', '69', '70', '71', '72', '73', '74', '75', '76']
  AND norm.norm_doknr = 'BJNR114690980'  // SGB X DOKNR
CREATE (doc)-[:CONTAINS_NORM]->(norm)
```

---

### 2.1.4 UC14 Re-Test ✅

**Test-Script**: `scripts/test_uc10_uc14.py`

```bash
python scripts/test_uc10_uc14.py
```

**Erwartetes Ergebnis**:
```
✅ UC14: Datenschutz-Compliance
   - Normen: 8 → 18 (alle §§ 67-85)
   - Chunks: 48 → 110+
   - Coverage: 42% → 95%+
   - Status: PARTIAL → PASS
```

---

## 2.2 Cross-References erstellen (P1)

**Ziel**: UC15 (Schnittstellenanalyse) verbessern

**Aufgabe**: REFERS_TO Relationships zwischen SGBs

```cypher
// Beispiel: SGB II → SGB III Verweis
MATCH (norm_ii:LegalNorm {paragraph_nummer: '16', sgb: 'II'})
MATCH (norm_iii:LegalNorm {paragraph_nummer: '35', sgb: 'III'})
WHERE norm_ii.text CONTAINS 'SGB III § 35'
CREATE (norm_ii)-[:REFERS_TO {context: 'Eingliederung'}]->(norm_iii)
```

**Script**: `scripts/extract_cross_references.py`

**NLP-Ansatz**:
- Regex für "SGB [RÖMISCH] § [NUMMER]"
- Spacy NER für Gesetzesverweise
- Automatische REFERS_TO Erstellung

---

## 2.3 Amendment-Daten erfassen (P2)

**Ziel**: UC19 (Schulungskonzept) ermöglichen

**Aufgabe**: Bürgergeld-Reform 2023 erfassen

**Datenstruktur**:
```json
{
  "amendment_id": "buergergeld_2023",
  "date": "2023-01-01",
  "title": "Bürgergeld-Reform 2023",
  "affected_paragraphs": ["20", "21", "22"],
  "changes": [
    {
      "paragraph": "20",
      "type": "modified",
      "old_text": "...",
      "new_text": "...",
      "summary": "Erhöhung Regelsätze"
    }
  ]
}
```

**Neo4j Schema**:
```cypher
CREATE (amendment:Amendment {
  id: 'buergergeld_2023',
  date: date('2023-01-01'),
  title: 'Bürgergeld-Reform 2023'
})
CREATE (norm:LegalNorm {paragraph_nummer: '20'})-[:AMENDED_BY]->(amendment)
```

---

## 2.4 Metadaten-Qualität verbessern (P2)

**Aufgaben**:
1. **Fehlende Titel ergänzen**
   - Viele Normen haben nur "§ XX" als enbez
   - Vollständige Titel aus Quelldaten extrahieren

2. **Order-Index korrigieren**
   - Manche Normen haben inkonsistente order_index
   - Wichtig für korrekte Sortierung

3. **Metadaten-Validierung**
   ```cypher
   // Normen ohne Titel
   MATCH (n:LegalNorm)
   WHERE n.enbez = '§ ' + n.paragraph_nummer
   RETURN count(n)
   ```

---

## Timeline Phase 2

| Woche | Aufgabe | Priorität | Aufwand |
|-------|---------|-----------|---------|
| 1 | 2.1 UC14 vervollständigen | P1 | 2-3 Tage |
| 2 | 2.2 Cross-References | P1 | 2-3 Tage |
| 3 | 2.3 Amendments (Start) | P2 | 1-2 Tage |
| 4 | 2.4 Metadaten-Qualität | P2 | 1-2 Tage |

**Gesamtdauer**: 3-4 Wochen

---

## Erfolgskriterien Phase 2

| Kriterium | Ziel | Aktuell |
|-----------|------|---------|
| UC14 funktionsfähig | 100% | 42% |
| Coverage gesamt | > 60% | 46.4% |
| Cross-References | > 100 | 0 |
| Amendment-Coverage | > 10% | 0.5% |
| MVP Use Cases | 16/20 | 13/20 |

---

## Quick-Win: UC14 ohne Re-Import

**Alternative**: UC14 mit vorhandenen Daten nutzen

**Aktuell verfügbar**:
- §§ 78-85: Verarbeitung, Rechte, Strafen

**Use Case anpassen**:
- Fokus auf **Datenverarbeitung & Betroffenenrechte**
- Weniger Fokus auf Grundlagen-Definitionen
- **Akzeptable Lösung für MVP**

**Cypher-Query (angepasst)**:
```cypher
// UC14 Partial: Fokus auf verfügbare Paragraphen
MATCH (doc:LegalDocument {sgb_nummer: 'X'})
      -[:CONTAINS_NORM]->(norm:LegalNorm)
WHERE norm.paragraph_nummer IN ['78', '79', '80', '81', '82', '83', '84', '85']
OPTIONAL MATCH (norm)-[:HAS_CHUNK]->(chunk:Chunk)
RETURN norm, collect(chunk) as chunks
```

**Dokumentation**:
```markdown
### UC14: Datenschutz-Compliance (Partial MVP)

**Verfügbar**:
- ✅ Datenverarbeitung (§§ 78-80)
- ✅ Betroffenenrechte (§§ 81-84)
- ✅ Strafvorschriften (§ 85)

**Eingeschränkt**:
- ⚠️ Grundlagen-Definitionen (§§ 67-69) fehlen
- ⚠️ Datenerhebung (§ 76) fehlt

**Empfehlung**: Für MVP akzeptabel, vollständige Version in Phase 2
```

---

## Empfehlung

### Sofort verfügbar (Quick-Win)
1. ✅ **UC14 Partial für MVP freigeben**
   - Dokumentation anpassen
   - Fokus auf verfügbare Paragraphen
   - Status: ⚠️ → ⚠️ (aber nutzbar!)

### Phase 2 (vollständige Lösung)
2. 📥 **Quelldaten prüfen & importieren**
   - §§ 67-76 beschaffen
   - Re-Import durchführen
   - UC14 vollständig funktionsfähig

3. 🔗 **Cross-References erstellen**
   - UC15 verbessern
   - REFERS_TO Relationships

4. 📝 **Amendment-Daten erfassen**
   - UC19 ermöglichen
   - Bürgergeld-Reform 2023

---

## Nächster Schritt

**Empfehlung**: Quick-Win nutzen

1. UC14 Partial dokumentieren
2. In MVP aufnehmen (14 Use Cases!)
3. Phase 2 für vollständige Version planen

**Oder**: Phase 2.1 sofort starten
- Quelldaten prüfen
- §§ 67-76 importieren
- UC14 vollständig funktionsfähig machen

**Entscheidung**: Quick-Win oder vollständige Lösung?

---

**Status**: ⏳ Bereit für Phase 2  
**Nächste Action**: Quelldaten-Prüfung oder Quick-Win-Dokumentation  
**Timeline**: 3-4 Wochen für vollständige Phase 2
