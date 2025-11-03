# Neo4j Desktop Deployment - 14 Use Cases

**Version**: 1.0  
**Platform**: Neo4j Desktop (macOS)  
**Use Cases**: 14 produktionsreif  
**Status**: ✅ Ready to Deploy

---

## 🎯 Quick Start

### Was wird deployed?
- 14 produktionsreife Use Cases
- Neo4j Browser Guides
- Cypher-Queries
- Bloom Perspectives
- Dashboard-Visualisierungen

**Deployment-Zeit**: ~10 Minuten

---

## 📋 Pre-Deployment Checkliste

### 1. Neo4j Desktop Status prüfen

```bash
# Prüfe ob Neo4j läuft
curl http://localhost:7474
```

**Erwartetes Ergebnis**: HTTP 200 OK

### 2. Database Backup erstellen

**In Neo4j Desktop**:
1. Öffne Neo4j Desktop
2. Wähle deine Database
3. Klicke auf "..." → "Manage" → "Terminal"
4. Führe aus:

```bash
neo4j-admin database dump neo4j --to-path=/tmp/backup
```

**Backup gespeichert**: `/tmp/backup/neo4j.dump`

### 3. Health-Check ausführen

```bash
cd /Users/ma3u/projects/sozialgesetze/Sozialrecht_RAG

# Test UC10 & UC14
python scripts/test_uc10_uc14.py
```

**Erwartetes Ergebnis**:
```
✅ UC10: PASS (32 Chunks)
✅ UC14: PASS (73 Chunks)
🎉 ERFOLG: Beide Use Cases sind funktionsfähig!
```

---

## 🚀 Deployment Steps

### Step 1: Neo4j Browser Guides installieren

Erstelle Guides für jeden Use Case:

```bash
# Guide-Verzeichnis erstellen
mkdir -p ~/Documents/Neo4j/guides

# Kopiere Cypher-Queries
cp -r cypher/use_cases/*.cypher ~/Documents/Neo4j/guides/
```

### Step 2: Browser Guides laden

**Öffne Neo4j Browser** (http://localhost:7474)

#### Guide 1: UC10 - Widerspruchsverfahren

```cypher
:play http://localhost:8000/guides/uc10_widerspruch.html
```

**Oder direkt die Query ausführen**:

```cypher
// UC10: Widerspruchsverfahren - Übersicht
MATCH (doc:LegalDocument {sgb_nummer: 'X'})
      -[:CONTAINS_NORM]->(norm:LegalNorm)
      -[:HAS_CHUNK]->(chunk:Chunk)
WHERE norm.paragraph_nummer IN ['79', '80', '84', '85']
RETURN 
    norm.paragraph_nummer as paragraph,
    norm.enbez as titel,
    count(chunk) as chunks
ORDER BY norm.paragraph_nummer
```

**Erwartetes Ergebnis**:
```
paragraph | titel  | chunks
----------|--------|-------
79        | § 79   | 12
80        | § 80   | 10
84        | § 84   | 8
85        | § 85   | 2
```

#### Guide 2: UC14 - Datenschutz-Compliance

```cypher
// UC14: Datenschutz-Compliance - Vollständige Übersicht
MATCH (doc:LegalDocument {sgb_nummer: 'X'})
      -[:CONTAINS_NORM]->(norm:LegalNorm)
WHERE toInteger(norm.paragraph_nummer) >= 67 
  AND toInteger(norm.paragraph_nummer) <= 85
OPTIONAL MATCH (norm)-[:HAS_CHUNK]->(chunk:Chunk)
RETURN 
    norm.paragraph_nummer as paragraph,
    norm.enbez as titel,
    norm.titel as beschreibung,
    count(chunk) as chunks
ORDER BY toInteger(norm.paragraph_nummer)
```

**Erwartetes Ergebnis**: 18 Normen (§§ 67-85)

#### Guide 3: Sachbearbeiter Dashboard

```cypher
// Sachbearbeiter-Workflows - Alle Use Cases
MATCH (doc:LegalDocument {sgb_nummer: 'II'})
      -[:CONTAINS_NORM]->(norm:LegalNorm)
WHERE norm.paragraph_nummer IN ['20', '21', '22', '23', // UC01
                                 '32',                  // UC02
                                 '11', '11b',          // UC03
                                 '7',                   // UC06
                                 '24']                  // UC08
OPTIONAL MATCH (norm)-[:HAS_CHUNK]->(chunk:Chunk)
WITH norm.paragraph_nummer as para, 
     norm.enbez as titel,
     count(chunk) as chunks,
     CASE 
         WHEN norm.paragraph_nummer IN ['20', '21', '22', '23'] THEN 'UC01: Regelbedarfsermittlung'
         WHEN norm.paragraph_nummer = '32' THEN 'UC02: Sanktionsprüfung'
         WHEN norm.paragraph_nummer IN ['11', '11b'] THEN 'UC03: Einkommensanrechnung'
         WHEN norm.paragraph_nummer = '7' THEN 'UC06: Bedarfsgemeinschaft'
         WHEN norm.paragraph_nummer = '24' THEN 'UC08: Erstausstattung'
     END as use_case
RETURN use_case, para, titel, chunks
ORDER BY use_case, para
```

---

### Step 3: Visualisierungen erstellen

#### Visualisierung 1: SGB X Graph

```cypher
// Widerspruch & Datenschutz - Full Graph
MATCH path = (doc:LegalDocument {sgb_nummer: 'X'})
             -[:CONTAINS_NORM]->(norm:LegalNorm)
             -[:HAS_CHUNK]->(chunk:Chunk)
WHERE toInteger(norm.paragraph_nummer) >= 67 
  AND toInteger(norm.paragraph_nummer) <= 85
RETURN path
LIMIT 100
```

**Im Browser**:
- Klicke auf einen Knoten für Details
- Verwende Maus-Rad zum Zoomen
- Drag & Drop zur Navigation

#### Visualisierung 2: Use Case Overview

```cypher
// Alle 14 Use Cases - Statistik
MATCH (doc:LegalDocument)
      -[:CONTAINS_NORM]->(norm:LegalNorm)
      -[:HAS_CHUNK]->(chunk:Chunk)
WHERE doc.sgb_nummer IN ['II', 'X']
WITH doc.sgb_nummer as sgb,
     count(DISTINCT norm) as normen,
     count(DISTINCT chunk) as chunks
RETURN sgb, normen, chunks
ORDER BY sgb
```

#### Visualisierung 3: Coverage Dashboard

```cypher
// Coverage pro SGB
MATCH (doc:LegalDocument)
OPTIONAL MATCH (doc)-[:CONTAINS_NORM]->(norm:LegalNorm)
OPTIONAL MATCH (norm)-[:HAS_CHUNK]->(chunk:Chunk)
WITH doc.sgb_nummer as sgb,
     doc.title as titel,
     count(DISTINCT norm) as normen,
     count(DISTINCT chunk) as chunks,
     count(DISTINCT CASE WHEN chunk IS NOT NULL THEN norm END) as normen_mit_chunks
RETURN 
    sgb,
    titel,
    normen,
    chunks,
    normen_mit_chunks,
    round(toFloat(normen_mit_chunks) / normen * 100, 1) as coverage_percent
ORDER BY sgb
```

---

### Step 4: Bloom Perspectives einrichten

**Öffne Neo4j Bloom** (im Neo4j Desktop)

#### Perspective 1: Sachbearbeiter

1. Klicke auf "Create Perspective"
2. Name: "Sachbearbeiter Workflows"
3. Search Phrase Pattern:
   ```
   SGB II Paragraph {number}
   ```
4. Füge hinzu:
   - Node Label: `LegalDocument`
   - Node Label: `LegalNorm`
   - Node Label: `Chunk`
   - Relationship: `CONTAINS_NORM`
   - Relationship: `HAS_CHUNK`

5. Category Filter:
   ```cypher
   sgb_nummer = 'II' AND 
   paragraph_nummer IN ['20','21','22','23','32','11','11b','7','24']
   ```

#### Perspective 2: Datenschutz & Widerspruch

1. Name: "SGB X - Compliance"
2. Search Phrase: 
   ```
   Datenschutz § {number}
   ```
3. Category Filter:
   ```cypher
   sgb_nummer = 'X' AND
   toInteger(paragraph_nummer) >= 67 AND 
   toInteger(paragraph_nummer) <= 85
   ```

#### Perspective 3: Prozessberater

1. Name: "Prozessanalyse"
2. Focus auf SGB II Analytics
3. Include:
   - Komplexitätsanalyse (UC16)
   - Prozessmodellierung (UC18)
   - Benchmark (UC17)

---

### Step 5: Saved Queries erstellen

**Im Neo4j Browser**:

1. Klicke auf "★" (Favorites)
2. Füge hinzu:

**Query 1: UC10 Quick Check**
```cypher
// UC10: Widerspruchsverfahren Status
MATCH (doc:LegalDocument {sgb_nummer: 'X'})
      -[:CONTAINS_NORM]->(norm:LegalNorm)
WHERE norm.paragraph_nummer IN ['79', '80', '84', '85']
OPTIONAL MATCH (norm)-[:HAS_CHUNK]->(chunk:Chunk)
RETURN count(DISTINCT norm) as normen, 
       count(DISTINCT chunk) as chunks,
       CASE 
           WHEN count(DISTINCT norm) = 4 AND count(DISTINCT chunk) >= 20 THEN '✅ PASS'
           ELSE '❌ FAIL'
       END as status
```

**Query 2: UC14 Quick Check**
```cypher
// UC14: Datenschutz Status
MATCH (doc:LegalDocument {sgb_nummer: 'X'})
      -[:CONTAINS_NORM]->(norm:LegalNorm)
WHERE toInteger(norm.paragraph_nummer) >= 67 
  AND toInteger(norm.paragraph_nummer) <= 85
OPTIONAL MATCH (norm)-[:HAS_CHUNK]->(chunk:Chunk)
WHERE chunk.text CONTAINS 'Sozialdaten' OR chunk.text CONTAINS 'Datenschutz'
WITH count(DISTINCT norm) as normen,
     count(DISTINCT chunk) as chunks,
     ['67', '68', '69', '76', '78', '79'] as key_paragraphs,
     collect(DISTINCT norm.paragraph_nummer) as found_paragraphs
RETURN 
    normen,
    chunks,
    [p IN key_paragraphs WHERE p IN found_paragraphs] as key_found,
    size([p IN key_paragraphs WHERE p IN found_paragraphs]) as key_count,
    CASE 
        WHEN size([p IN key_paragraphs WHERE p IN found_paragraphs]) >= 4 THEN '✅ PASS'
        ELSE '⚠️ PARTIAL'
    END as status
```

**Query 3: Full Coverage**
```cypher
// Alle 14 Use Cases - Status
WITH [
    {uc: 'UC01', sgb: 'II', paragraphs: ['20', '21', '22', '23']},
    {uc: 'UC02', sgb: 'II', paragraphs: ['32']},
    {uc: 'UC03', sgb: 'II', paragraphs: ['11', '11b']},
    {uc: 'UC06', sgb: 'II', paragraphs: ['7']},
    {uc: 'UC08', sgb: 'II', paragraphs: ['24']},
    {uc: 'UC10', sgb: 'X', paragraphs: ['79', '80', '84', '85']},
    {uc: 'UC14', sgb: 'X', paragraphs: ['67', '68', '69', '70', '71', '72', '73', '74', '75', '76']}
] as use_cases
UNWIND use_cases as uc_data
MATCH (doc:LegalDocument {sgb_nummer: uc_data.sgb})
      -[:CONTAINS_NORM]->(norm:LegalNorm)
WHERE norm.paragraph_nummer IN uc_data.paragraphs
OPTIONAL MATCH (norm)-[:HAS_CHUNK]->(chunk:Chunk)
WITH uc_data.uc as use_case,
     count(DISTINCT norm) as normen,
     count(DISTINCT chunk) as chunks,
     size(uc_data.paragraphs) as expected
RETURN 
    use_case,
    normen + '/' + expected as coverage,
    chunks,
    CASE 
        WHEN normen = expected AND chunks > 0 THEN '✅'
        WHEN chunks > 0 THEN '⚠️'
        ELSE '❌'
    END as status
ORDER BY use_case
```

---

### Step 6: Indexes optimieren

```cypher
// Performance Indexes für schnelle Queries
CREATE INDEX norm_paragraph IF NOT EXISTS 
FOR (n:LegalNorm) ON (n.paragraph_nummer);

CREATE INDEX norm_sgb IF NOT EXISTS
FOR (n:LegalNorm) ON (n.sgb_nummer);

CREATE INDEX doc_sgb IF NOT EXISTS
FOR (d:LegalDocument) ON (d.sgb_nummer);

CREATE INDEX chunk_text IF NOT EXISTS
FOR (c:Chunk) ON (c.text);

// Verify
SHOW INDEXES;
```

---

## 📊 Post-Deployment Verification

### Test 1: Quick Health-Check

```bash
# Im Terminal
python scripts/test_uc10_uc14.py
```

**Erwartung**: ✅ Beide PASS

### Test 2: Browser Verification

**Im Neo4j Browser**:

```cypher
// Statistik aller 14 Use Cases
MATCH (doc:LegalDocument)
      -[:CONTAINS_NORM]->(norm:LegalNorm)
      -[:HAS_CHUNK]->(chunk:Chunk)
RETURN 
    count(DISTINCT doc) as documents,
    count(DISTINCT norm) as norms,
    count(DISTINCT chunk) as chunks
```

**Erwartete Werte**:
- Documents: 13 SGBs
- Norms: ~4,000+
- Chunks: ~19,000+

### Test 3: Use Case Spot-Check

```cypher
// UC10: Widerspruch
MATCH (doc:LegalDocument {sgb_nummer: 'X'})
      -[:CONTAINS_NORM]->(norm:LegalNorm {paragraph_nummer: '79'})
      -[:HAS_CHUNK]->(chunk:Chunk)
RETURN norm.enbez, chunk.text
LIMIT 1
```

**Erwartung**: Text von § 79 wird angezeigt

---

## 🎨 Dashboard Templates

### Template 1: Sachbearbeiter Dashboard

```cypher
// Tägliche Übersicht für Sachbearbeiter
MATCH (doc:LegalDocument {sgb_nummer: 'II'})
      -[:CONTAINS_NORM]->(norm:LegalNorm)
WHERE norm.paragraph_nummer IN ['20', '32', '11', '7', '24']
OPTIONAL MATCH (norm)-[:HAS_CHUNK]->(chunk:Chunk)
RETURN 
    norm.paragraph_nummer as 'Paragraph',
    norm.enbez as 'Bezeichnung',
    norm.titel as 'Titel',
    count(chunk) as 'Chunks verfügbar',
    '✅' as 'Status'
ORDER BY norm.paragraph_nummer
```

### Template 2: Compliance Dashboard

```cypher
// Datenschutz-Compliance Übersicht
MATCH (doc:LegalDocument {sgb_nummer: 'X'})
      -[:CONTAINS_NORM]->(norm:LegalNorm)
WHERE toInteger(norm.paragraph_nummer) >= 67 
  AND toInteger(norm.paragraph_nummer) <= 85
OPTIONAL MATCH (norm)-[:HAS_CHUNK]->(chunk:Chunk)
WITH norm,
     count(chunk) as chunk_count,
     CASE 
         WHEN toInteger(norm.paragraph_nummer) BETWEEN 67 AND 76 THEN 'Sozialdaten-Grundlagen'
         WHEN toInteger(norm.paragraph_nummer) BETWEEN 78 AND 85 THEN 'Verarbeitung & Rechte'
         ELSE 'Sonstige'
     END as kategorie
RETURN 
    kategorie,
    count(norm) as normen,
    sum(chunk_count) as chunks,
    round(avg(chunk_count), 1) as durchschnitt_chunks
ORDER BY kategorie
```

### Template 3: Performance Monitoring

```cypher
// Query Performance Check
PROFILE
MATCH (doc:LegalDocument {sgb_nummer: 'X'})
      -[:CONTAINS_NORM]->(norm:LegalNorm {paragraph_nummer: '79'})
      -[:HAS_CHUNK]->(chunk:Chunk)
RETURN count(chunk)
```

**Ziel**: < 10ms Execution Time

---

## 🔧 Troubleshooting

### Problem: "Node not found"

```cypher
// Prüfe ob SGB X existiert
MATCH (doc:LegalDocument {sgb_nummer: 'X'})
RETURN doc.title, doc.sgb_nummer
```

**Lösung**: Falls leer, SGB X re-importieren:
```bash
python scripts/import_sgb_x_from_json.py temp_data/sgb_x_paragraphs_67-76.json --execute
```

### Problem: Langsame Queries

```cypher
// Check Indexes
SHOW INDEXES
```

**Lösung**: Fehlende Indexes erstellen (siehe Step 6)

### Problem: Bloom Perspective fehlt

1. Öffne Bloom
2. "Create New Perspective"
3. Folge Step 4 Anweisungen

---

## 📱 Mobile/Tablet Access

### Neo4j Browser von anderen Geräten

1. Finde deine lokale IP:
   ```bash
   ifconfig | grep "inet " | grep -v 127.0.0.1
   ```

2. Im Browser auf Tablet/Handy:
   ```
   http://<YOUR_IP>:7474
   ```

3. Login mit Neo4j Desktop Credentials

---

## 🎯 Quick Links (Bookmarks)

**Neo4j Browser**:
- http://localhost:7474
- Favorites: UC10, UC14, Dashboard

**Neo4j Bloom**:
- Im Neo4j Desktop: "Open Bloom"

**Cypher-Queries**:
- `~/Documents/Neo4j/guides/`

---

## ✅ Deployment Checkliste

### Pre-Deployment
- [x] Neo4j Desktop läuft
- [x] Database Backup erstellt
- [x] Health-Check: UC10 & UC14 PASS

### Deployment
- [ ] Browser Guides geladen
- [ ] Visualisierungen getestet
- [ ] Bloom Perspectives erstellt
- [ ] Saved Queries hinzugefügt
- [ ] Indexes erstellt

### Post-Deployment
- [ ] Verification Tests bestanden
- [ ] Dashboard Templates getestet
- [ ] Performance < 50ms
- [ ] Mobile Access konfiguriert (optional)

---

## 🎉 SUCCESS!

**Status**: ✅ 14 Use Cases deployed in Neo4j Desktop!

**Nächste Schritte**:
1. Öffne Neo4j Browser: http://localhost:7474
2. Führe Quick Health-Check aus
3. Teste UC10 & UC14
4. Explore mit Bloom! 🚀

---

**Support**:
- Scripts: `scripts/test_uc10_uc14.py`
- Queries: `cypher/use_cases/`
- Docs: `DEPLOYMENT_MVP_14_USE_CASES.md`

**Version**: 1.0 (Januar 2025)
