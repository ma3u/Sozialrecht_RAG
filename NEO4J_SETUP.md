# Neo4j RAG Setup für Sozialrecht-Datenbank

**Anleitung zur Einrichtung der Neo4j Graph-Datenbank mit Docling PDF-Extraktion**

---

## 🚀 Quick Start

```bash
# 1. Neo4j starten
docker-compose up -d

# 2. Dependencies installieren
pip install -r requirements.txt

# 3. Alle PDFs zu Neo4j hochladen
python scripts/upload_sozialrecht_to_neo4j.py

# 4. Test-Suche durchführen
python scripts/test_sozialrecht_rag.py
```

**Neo4j Browser**: http://localhost:7474
**Credentials**: neo4j / password

---

## 📊 Graph-Schema

### Node Types

**Document** - Hauptdokument
```cypher
(:Document {
  id: string,               // Unique hash
  sgb_nummer: string,       // "I", "II", "III", etc.
  document_type: string,    // "Gesetz", "BA_Weisung", etc.
  source_url: string,
  source_domain: string,
  trust_score: int,         // 70-100%
  type_priority: int,       // 1-99 (1=highest)
  filename: string,
  file_size_mb: float,
  stand_datum: date,        // "2025-01-01" (wenn vorhanden)
  created: datetime,
  chunk_count: int
})
```

**Chunk** - Text-Segmente mit Embeddings
```cypher
(:Chunk {
  text: string,
  embedding: list<float>,   // 768-dim vector
  chunk_index: int,
  paragraph_nummer: string, // "20", "11a", etc.
  paragraph_context: string // First 200 chars
})
```

**Paragraph** - Juristische Paragraphen
```cypher
(:Paragraph {
  id: string,               // "II_20", "VI_43", etc.
  paragraph_nummer: string,
  sgb_nummer: string,
  content: string,
  chunk_count: int
})
```

### Relationships

```cypher
(:Document)-[:HAS_CHUNK]->(:Chunk)
(:Document)-[:CONTAINS_PARAGRAPH]->(:Paragraph)
```

---

## 🔍 Beispiel-Queries

### 1. Alle Dokumente zu SGB II anzeigen
```cypher
MATCH (d:Document {sgb_nummer: "II"})
RETURN d.filename, d.document_type, d.trust_score, d.stand_datum
ORDER BY d.type_priority ASC, d.trust_score DESC
```

### 2. Finde Paragraph § 20 SGB II (Regelbedarfe)
```cypher
MATCH (d:Document {sgb_nummer: "II"})-[:CONTAINS_PARAGRAPH]->(p:Paragraph {paragraph_nummer: "20"})
RETURN d.document_type, d.filename, d.trust_score, p.content
ORDER BY d.type_priority ASC
```

### 3. Vector Search nach "Regelbedarf Alleinstehende"
```cypher
// Benötigt query embedding (wird von Python generiert)
MATCH (d:Document)-[:HAS_CHUNK]->(c:Chunk)
WHERE c.paragraph_nummer = "20"
RETURN c.text, d.filename, d.trust_score
LIMIT 5
```

### 4. Statistiken anzeigen
```cypher
MATCH (d:Document)
OPTIONAL MATCH (d)-[:HAS_CHUNK]->(c:Chunk)
OPTIONAL MATCH (d)-[:CONTAINS_PARAGRAPH]->(p:Paragraph)
RETURN d.sgb_nummer,
       COUNT(DISTINCT d) as dokumente,
       COUNT(DISTINCT c) as chunks,
       COUNT(DISTINCT p) as paragraphen
ORDER BY d.sgb_nummer
```

### 5. Quellen-Vertrauenswürdigkeit analysieren
```cypher
MATCH (d:Document)
RETURN d.source_domain,
       AVG(d.trust_score) as avg_trust,
       COUNT(d) as count
ORDER BY avg_trust DESC
```

---

## 🎯 Hybrid-Strategie Implementierung

### Problem: BA aktualisiert Beträge nicht in Weisungen

**Lösung**: Gesetz für Beträge + Weisung für Verfahren

```python
from src.sozialrecht_neo4j_rag import SozialrechtNeo4jRAG

rag = SozialrechtNeo4jRAG()

# Automatische Hybrid-Suche
response = rag.get_hybrid_answer("Was ist der Regelbedarf für Alleinstehende?")

print(response['answer'])
# Output:
# Rechtliche Grundlage (Gesetz): § 20 Abs. 2 SGB II: 563 Euro
# Quelle: SGB_02_Buergergeld.pdf (Vertrauenswürdigkeit: 100%)
#
# Anwendungshinweise (Weisung): Berechnungsverfahren...
# Quelle: FW_SGB_II_Par_20_Regelbedarfe_2023.pdf (Stand: 27.11.2023)
# Vertrauenswürdigkeit: 95%
```

---

## 📋 Upload-Workflow

### Schritt 1: Neo4j starten
```bash
docker-compose up -d
```

**Warten bis gesund**:
```bash
docker-compose ps
# Sollte "healthy" zeigen
```

### Schritt 2: Dry-Run (Überprüfung)
```bash
python scripts/upload_sozialrecht_to_neo4j.py --dry-run
```

Output zeigt:
- Alle gefundenen PDFs
- Kategorisierung
- Geschätzte Größe

### Schritt 3: Upload (alle Kategorien)
```bash
# Alle 50 PDFs hochladen
python scripts/upload_sozialrecht_to_neo4j.py

# Oder spezifische Kategorien:
python scripts/upload_sozialrecht_to_neo4j.py --categories Gesetze
python scripts/upload_sozialrecht_to_neo4j.py --categories Fachliche_Weisungen
python scripts/upload_sozialrecht_to_neo4j.py --categories Rundschreiben_BMAS
```

### Schritt 4: Validierung
```bash
# Browser öffnen
open http://localhost:7474

# Statistiken abrufen
python scripts/test_sozialrecht_rag.py --stats
```

---

## 🔧 Konfiguration

### Umgebungsvariablen (.env)

```bash
# Neo4j Connection
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=password

# Optional: Azure Cloud (wenn nicht lokal)
# NEO4J_URI=neo4j+s://xxxxx.databases.neo4j.io
# NEO4J_USERNAME=neo4j
# NEO4J_PASSWORD=your-aura-password
```

---

## 📊 Erwartete Ergebnisse nach Upload

### Gesamt
- **Dokumente**: 50 Nodes
- **Chunks**: ~1500-2000 Nodes (abhängig von Chunk-Strategie)
- **Paragraphen**: ~150-200 Nodes
- **Embeddings**: ~1500 x 768-dim Vektoren
- **Speicherplatz**: ~500 MB (Neo4j Datenbank)

### Pro SGB
- **SGB II**: ~500 Chunks (umfangreichste Sammlung)
- **SGB V, VI**: ~200-300 Chunks
- **Andere**: ~50-150 Chunks pro SGB

### Performance
- **Upload Zeit**: ~10-15 Minuten (alle 50 PDFs)
- **Query Zeit**: <100ms (mit Caching)
- **Vector Search**: <200ms

---

## 🧪 Testing

### Test-Script ausführen
```bash
python scripts/test_sozialrecht_rag.py
```

**Beispiel-Fragen**:
- "Was ist der Regelbedarf für Alleinstehende?"
- "Wer ist leistungsberechtigt nach SGB II?"
- "Welche Mehrbedarfe gibt es?"
- "Was ist Erwerbsfähigkeit nach § 8 SGB II?"

---

## 📈 Monitoring

### Neo4j Browser Queries

**Dokument-Übersicht**:
```cypher
MATCH (d:Document)
RETURN d.sgb_nummer, d.document_type, d.filename, d.trust_score
ORDER BY d.sgb_nummer, d.type_priority
```

**Chunk-Verteilung**:
```cypher
MATCH (d:Document)-[:HAS_CHUNK]->(c)
RETURN d.sgb_nummer, COUNT(c) as chunks
ORDER BY chunks DESC
```

**Paragraph-Abdeckung**:
```cypher
MATCH (p:Paragraph)
RETURN p.sgb_nummer, COUNT(p) as paragraphen
ORDER BY paragraphen DESC
```

---

## ⚠️ Bekannte Einschränkungen

1. **Beträge in Weisungen veraltet**:
   - § 19, 20 SGB II (Stand 2023)
   - Lösung: Hybrid-Strategie (Gesetz + Weisung)

2. **BMAS Rundschreiben begrenzt**:
   - Nur 1/7 verfügbar
   - Weitere benötigen manuelle Beschaffung

3. **Embedding-Modell**:
   - `paraphrase-multilingual-mpnet-base-v2` ist generisch
   - Für bessere Ergebnisse: Legal-spezifisches Modell trainieren

4. **Chunking-Strategie**:
   - 800 Zeichen können Paragraphen trennen
   - Improvement: Paragraph-Grenzen erkennen

---

## 🚀 Next Steps

1. **Upload durchführen**: Alle 50 PDFs zu Neo4j
2. **Testing**: Beispiel-Queries testen
3. **RAG-Pipeline**: Frontend/API entwickeln
4. **Monitoring**: Update-Strategie für November 2025

---

**Erstellt**: 2025-10-10
**Autor**: ma3u
**Basiert auf**: ms-agentf-neo4j Docling-System
