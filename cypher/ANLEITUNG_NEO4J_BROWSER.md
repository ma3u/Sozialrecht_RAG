# Neo4j Browser - Saved Queries Anleitung

**Schritt-für-Schritt: Cypher-Queries als Favorites/Scripts speichern**

Basierend auf deinem Screenshot mit "Local scripts" → "NEO4J RAG scripts"

---

## 📋 Voraussetzungen

✅ Neo4j Browser geöffnet (http://localhost:7474)
✅ Eingeloggt (neo4j/password)
✅ Cypher-Dateien in `cypher/*.cypher` vorhanden

---

## 🚀 Schritt-für-Schritt Anleitung

### **Methode 1: Via Favorites (wie in deinem Screenshot)**

#### 1. **Favorites-Panel öffnen**
- Linke Sidebar: Klicke auf **⭐ Stern-Symbol** (Favorites)
- Du siehst: "Local scripts" und "Sample Scripts"

#### 2. **Neuen Ordner erstellen** (falls nicht vorhanden)
- Unter "Local scripts": Klicke **📁 + Icon**
- Erstelle Ordner: **"Sozialgesetze"** oder **"Sozialrecht RAG"**

#### 3. **Neue Query hinzufügen**
- Im Ordner "Sozialgesetze": Klicke **+ Add empty favorite**
- Oder: Rechtsklick → **"New favorite"**

#### 4. **Query kopieren und einfügen**
```
Öffne: cypher/01_graph_statistics.cypher (im Editor)
Kopiere: Query #1 (von // 1. bis zum ;)
```

**Beispiel - Query #1**:
```cypher
// 1. Gesamt-Übersicht
MATCH (d:Document)
OPTIONAL MATCH (d)-[:HAS_CHUNK]->(c:Chunk)
OPTIONAL MATCH (d)-[:CONTAINS_PARAGRAPH]->(p:Paragraph)
RETURN
  COUNT(DISTINCT d) as Dokumente,
  COUNT(DISTINCT c) as Chunks,
  COUNT(DISTINCT p) as Paragraphen,
  AVG(SIZE(c.embedding)) as Embedding_Dimension
;
```

#### 5. **Query benennen und speichern**
- Name: **"01. Gesamt-Übersicht"** oder **"Quick Stats"**
- Klicke **Save** oder **Speichern**

#### 6. **Wiederholen für alle Queries**
- Query #2: "02. Dokumente pro SGB"
- Query #3: "03. Chunks pro SGB"
- Etc.

---

### **Methode 2: Direkt in Query-Feld**

#### 1. **Query-Feld nutzen** (oben: `neo4j$`)
- Kopiere Query aus .cypher Datei
- Füge direkt ins Feld ein
- Klicke **▶️ Run** (blauer Play-Button)

#### 2. **Als Favorite speichern**
- Nach erfolgreichem Run: Klicke **⭐ Stern-Icon** rechts oben
- Benenne Query
- Wähle Ordner: "Sozialgesetze"
- **Save**

---

## 📂 Empfohlene Ordner-Struktur

Basierend auf deinem Screenshot-Stil:

```
📁 NEO4J RAG scripts
  📁 Sozialgesetze
    📊 01. Statistiken
      ⭐ Quick Stats
      ⭐ Dokumente pro SGB
      ⭐ Chunks pro SGB
      ⭐ Vertrauenswürdigkeit
    📋 02. Beziehungen
      ⭐ Weisungen zu Paragraph
      ⭐ Hybrid-Strategie
      ⭐ Fehlende Weisungen
    👤 03. Sachbearbeiter
      ⭐ Regelbedarfe (§ 20)
      ⭐ Leistungsberechtigung
      ⭐ Checkliste Antragsprüfung
    🎨 04. Visualisierungen
      ⭐ Gesetz-Weisungen Netzwerk
      ⭐ Trust-Score Graph
      ⭐ Paragraph-Cluster
```

---

## 💡 Tipps

### **Query-Auswahl per Klick**
- Klicke auf gespeicherte Query in Favorites
- Query erscheint automatisch im Eingabefeld
- **▶️ Run** klicken

### **Ergebnis-Ansichten**
- **Table** 📊: Tabellarische Daten
- **Graph** 🕸️: Visualisierung (für MATCH/RETURN d, p, c)
- **Text**: Rohe JSON-Ausgabe
- **Code**: Cypher Code der Query

### **Queries bearbeiten**
- Rechtsklick auf Favorite → **Edit**
- Query anpassen
- **Update** speichern

### **Queries teilen**
- Rechtsklick → **Export**
- Als .cypher Datei speichern
- Teilen mit Kollegen

---

## 🎯 Empfohlene Starter-Queries

### **Für Quick-Check:**

```cypher
// Gesamt-Übersicht (speichern als "Quick Stats")
MATCH (d:Document)
OPTIONAL MATCH (d)-[:HAS_CHUNK]->(c:Chunk)
RETURN COUNT(DISTINCT d) as Dokumente, COUNT(c) as Chunks
;
```

### **Für SGB II Sachbearbeiter:**

```cypher
// Regelbedarfe § 20 (speichern als "Regelbedarfe")
MATCH (d:Document {sgb_nummer: 'II'})-[:CONTAINS_PARAGRAPH]->
      (p:Paragraph {paragraph_nummer: '20'})
RETURN d.document_type, d.filename, d.trust_score
ORDER BY d.type_priority
;
```

### **Für Graph-Visualisierung:**

```cypher
// SGB II Netzwerk (speichern als "SGB II Graph")
MATCH (d:Document {sgb_nummer: 'II'})
OPTIONAL MATCH (d)-[:HAS_CHUNK]->(c:Chunk)
OPTIONAL MATCH (d)-[:CONTAINS_PARAGRAPH]->(p:Paragraph)
RETURN d, c, p
LIMIT 100
;
```

---

## 🔧 Troubleshooting

### **Fehler: "expected Path but was..."**
**Problem**: ORDER BY nach COLLECT ohne WITH
**Lösung**: Füge `WITH ... ` vor COLLECT hinzu (bereits in korrigierten Queries)

### **Query zu langsam**
**Problem**: Zu viele Nodes
**Lösung**: Füge `LIMIT 50` oder `LIMIT 100` hinzu

### **Keine Ergebnisse**
**Problem**: Daten noch nicht hochgeladen
**Lösung**: Prüfe mit `MATCH (d:Document) RETURN COUNT(d)`

---

## 📖 Weitere Ressourcen

**Neo4j Cypher-Dokumentation**: https://neo4j.com/docs/cypher-manual/
**Query-Optimierung**: https://neo4j.com/docs/cypher-manual/current/query-tuning/

---

**Erstellt**: 2025-10-11
**Für**: Neo4j Browser (lokal + Aura)
**Queries**: 34 verfügbar in cypher/*.cypher
