# Cypher Queries für Sozialrecht Graph-Analysen

**Vorgefertigte Cypher-Queries für Neo4j Aura Console**

---

## 📂 Verfügbare Query-Sammlungen

### 1. `01_graph_statistics.cypher`
**Statistiken & Übersichten**

- Gesamt-Übersicht (Dokumente, Chunks, Paragraphen)
- Dokumente pro SGB
- Chunks pro SGB
- Vertrauenswürdigkeit pro Quelle
- Paragraph-Abdeckung
- Dokument-Typ Verteilung
- Aktualitäts-Check
- Top 10 größte Dokumente

### 2. `02_gesetze_weisungen_beziehungen.cypher`
**Beziehungs-Analysen zwischen Gesetzen und Weisungen**

- Weisungen zu Gesetz-Paragraph finden
- Hybrid-Strategie Analyse (Gesetz + Weisung Paare)
- Fehlende Weisungen identifizieren
- Quellen-Hierarchie für Paragraph
- Chunk-Qualität Analyse
- Cross-SGB Paragraph-Verweise
- Vertrauenswürdigkeit vs. Aktualität
- Vollständigkeits-Check

### 3. `03_sachbearbeiter_workflows.cypher`
**Praktische Queries für Fallbearbeitung**

- Regelbedarfe-Abfrage (Hybrid)
- Leistungsberechtigung komplett
- Einkommen/Vermögen - Alle Quellen
- Sachbearbeiter-Checkliste
- Sanktions-Prüfung
- Aktualitäts-Warnung
- Verfahrens-Schritte
- Quick-Search: Stichwortsuche

---

## 🚀 Verwendung in Aura Console

### Direkt kopieren & ausführen:

1. **Öffne Aura Console**: https://console.neo4j.io
2. **Query Tab** oder **Explore** öffnen
3. **Kopiere Query** aus .cypher Datei
4. **Run** klicken
5. **Ergebnisse** als Tabelle oder Graph ansehen

### Beispiel-Workflow:

```cypher
// 1. Schneller Überblick
MATCH (d:Document)
RETURN COUNT(d) as Dokumente,
       COLLECT(DISTINCT d.sgb_nummer) as SGBs
;

// 2. SGB II Regelbedarfe (Hybrid)
MATCH (gesetz:Document {sgb_nummer: 'II', document_type: 'Gesetz'})
      -[:CONTAINS_PARAGRAPH]->(p:Paragraph {paragraph_nummer: '20'})
OPTIONAL MATCH (weisung:Document {document_type: 'BA_Weisung'})
               -[:CONTAINS_PARAGRAPH]->(p)
RETURN gesetz.filename, weisung.filename,
       weisung.stand_datum, p.content
;

// 3. Volltext-Suche
CALL db.index.fulltext.queryNodes('sozialrecht_fulltext', 'Alleinerziehende')
YIELD node, score
MATCH (d:Document)-[:HAS_CHUNK]->(node)
RETURN d.filename, node.paragraph_nummer, score
ORDER BY score DESC
LIMIT 5
;
```

---

## 📊 Graph-Visualisierungen

### In Aura "Explore" Tab:

**Dokument-Netzwerk**:
```cypher
MATCH (d:Document {sgb_nummer: 'II'})-[:HAS_CHUNK]->(c:Chunk)
MATCH (d)-[:CONTAINS_PARAGRAPH]->(p:Paragraph)
RETURN d, c, p
LIMIT 50
```

**Quellen-Hierarchie**:
```cypher
MATCH (p:Paragraph {sgb_nummer: 'II', paragraph_nummer: '20'})
MATCH (d:Document)-[:CONTAINS_PARAGRAPH]->(p)
RETURN p, d
```

---

## 🎯 Use Cases

### Für Sachbearbeiter:

**Szenario**: Bürgergeld-Antrag prüfen

```cypher
// Schritt 1: Erwerbsfähigkeit (§ 8)
MATCH (d:Document)-[:CONTAINS_PARAGRAPH]->(p:Paragraph {sgb_nummer: 'II', paragraph_nummer: '8'})
RETURN d.document_type, d.filename, d.trust_score,
       SUBSTRING(p.content, 0, 300) as Prüfkriterien
ORDER BY d.type_priority
;

// Schritt 2: Einkommen berechnen (§ 11)
MATCH (d:Document)-[:CONTAINS_PARAGRAPH]->(p:Paragraph {paragraph_nummer: '11'})
WHERE d.sgb_nummer = 'II'
RETURN d.filename, d.stand_datum, p.content
ORDER BY d.trust_score DESC
;
```

### Für Qualitätssicherung:

```cypher
// Finde Dokumente ohne Weisungen
MATCH (gesetz:Document {document_type: 'Gesetz'})-[:CONTAINS_PARAGRAPH]->(p)
WHERE NOT EXISTS {
  MATCH (weisung:Document {document_type: 'BA_Weisung'})-[:CONTAINS_PARAGRAPH]->(p)
}
RETURN gesetz.sgb_nummer,
       COUNT(DISTINCT p) as Paragraphen_ohne_Weisung
ORDER BY Paragraphen_ohne_Weisung DESC
;
```

---

## 📥 Queries in Aura ausführen

### Option 1: Copy & Paste

Einfach Query kopieren → Aura Console → Einfügen → Run

### Option 2: Via Python

```python
from src.sozialrecht_neo4j_rag import SozialrechtNeo4jRAG

rag = SozialrechtNeo4jRAG()

with rag.driver.session() as session:
    result = session.run("""
        MATCH (d:Document {sgb_nummer: 'II'})
        RETURN COUNT(d) as count
    """)
    print(result.single()['count'])

rag.close()
```

### Option 3: Cypher Shell CLI (wenn installiert)

```bash
cypher-shell -a neo4j+s://c748b32e.databases.neo4j.io \
             -u neo4j -p [password] \
             -f cypher/01_graph_statistics.cypher
```

---

## 🔍 Nützliche Analysen

### Performance-Check:

```cypher
// Größte Chunks finden (könnten zu groß sein)
MATCH (c:Chunk)
WHERE LENGTH(c.text) > 1000
RETURN LENGTH(c.text) as Größe, c.text[0..100] as Preview
ORDER BY Größe DESC
LIMIT 10
;
```

### Qualitäts-Check:

```cypher
// Chunks ohne Paragraph-Nummer
MATCH (c:Chunk)
WHERE c.paragraph_nummer IS NULL
RETURN COUNT(c) as Chunks_ohne_Paragraph
;
```

### Abdeckungs-Analyse:

```cypher
// Welche Paragraphen haben die meisten Quellen?
MATCH (p:Paragraph)
MATCH (d:Document)-[:CONTAINS_PARAGRAPH]->(p)
RETURN p.sgb_nummer, p.paragraph_nummer,
       COUNT(DISTINCT d) as Anzahl_Quellen,
       COLLECT(DISTINCT d.document_type) as Quelltypen
ORDER BY Anzahl_Quellen DESC
LIMIT 20
;
```

---

**Erstellt**: 2025-10-11
**Für**: Neo4j Aura Instance (c748b32e)
**Daten**: 43 Dokumente, 24,128 Chunks, 4,254 Paragraphen
