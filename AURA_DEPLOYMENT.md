# Neo4j Aura Cloud Deployment

**Anleitung für Upload zu Neo4j Aura Cloud-Instanz**

---

## 🚀 Quick Start

### 1. Aura Credentials konfigurieren

```bash
# .env Datei erstellen
cp .env.example .env

# Fülle deine Aura-Credentials ein:
NEO4J_URI=neo4j+s://YOUR-INSTANCE-ID.databases.neo4j.io
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your-aura-password
```

### 2. Konfiguration testen

```bash
python config/aura_config.py

# Output sollte sein:
# ✅ Configuration valid!
# Type: Aura Cloud
```

### 3. Daten hochladen

```bash
# Aktiviere venv
source venv/bin/activate

# Upload zu Aura (nutzt .env Credentials automatisch)
python scripts/upload_sozialrecht_to_neo4j.py

# Geschätzte Zeit: 15-20 Minuten (Cloud ist langsamer als lokal)
# Ergebnis: ~1500-2000 Chunks in Aura
```

---

## 📊 Aura vs. Local

| Feature | Local (Docker) | Aura Cloud |
|---------|----------------|------------|
| URI | `bolt://localhost:7687` | `neo4j+s://xxxxx.databases.neo4j.io` |
| Setup | `docker-compose up -d` | Bereits läuft |
| Upload Speed | ~10 min | ~15-20 min |
| Browser | http://localhost:7474 | https://console.neo4j.io |
| GDS Support | ✅ Selbst installiert | ⚠️ Nur in Enterprise |
| APOC | ✅ Selbst installiert | ⚠️ Nur Core Functions |
| Kosten | Kostenlos (lokal) | Free Tier: 200k nodes |

---

## ⚠️ Aura Einschränkungen

### 1. GDS (Graph Data Science) nicht verfügbar
**Problem**: `gds.similarity.cosine()` in Free Tier nicht verfügbar

**Lösung**: Code verwendet Fallback zu NumPy cosine similarity
```python
# In sozialrecht_neo4j_rag.py bereits implementiert
similarity = np.dot(query_embedding, chunk_embedding) / (
    np.linalg.norm(query_embedding) * np.linalg.norm(chunk_embedding)
)
```

### 2. APOC Eingeschränkt
**Verfügbar**: Core APOC functions
**Nicht verfügbar**: Custom procedures, advanced algorithms

**Unser Code**: Nutzt nur Core APOC → ✅ Kompatibel

### 3. Speicherlimit (Free Tier)
- **Nodes**: 200,000 (wir brauchen ~2,000) ✅
- **Relationships**: 400,000 ✅
- **Properties**: Unlimited ✅

**Unser Bedarf**: Weit unter Limits!

---

## 🔧 Anpassungen für Aura

### Code ist bereits Aura-kompatibel!

`SozialrechtNeo4jRAG.__init__()` erkennt automatisch:
- Liest .env für Credentials
- Erkennt Aura via `neo4j+s://` Protokoll
- Nutzt korrekte Connection-Parameter

**Keine Code-Änderungen nötig!**

---

## 📋 Upload-Prozess zu Aura

### Schritt-für-Schritt

```bash
# 1. Prüfe Aura-Verbindung
python -c "
from config.aura_config import AuraConfig
from src.sozialrecht_neo4j_rag import SozialrechtNeo4jRAG

config = AuraConfig()
print(config)
config.validate()

# Test connection
rag = SozialrechtNeo4jRAG()
stats = rag.get_stats()
print(f'Connected! Documents: {stats[\"documents\"]}')
rag.close()
"

# 2. Upload starten
python scripts/upload_sozialrecht_to_neo4j.py

# 3. Fortschritt überwachen
# - Script zeigt Progress Bar
# - Nach jedem Batch: Chunks-Count steigt
# - Total: 50 Dokumente → ~1500-2000 Chunks

# 4. Validierung
python -c "
from src.sozialrecht_neo4j_rag import SozialrechtNeo4jRAG
rag = SozialrechtNeo4jRAG()
stats = rag.get_stats()
print(f'📊 Aura Database:')
print(f'  Documents: {stats[\"documents\"]}')
print(f'  Chunks: {stats[\"chunks\"]}')
print(f'  Paragraphen: {stats.get(\"paragraphs\", 0)}')
print(f'  SGBs: {stats.get(\"sgbs_covered\", [])}')
rag.close()
"
```

---

## 🔍 Aura Console

**URL**: https://console.neo4j.io

### Query Examples (in Aura Browser)

```cypher
// 1. Quick Stats
MATCH (d:Document)
OPTIONAL MATCH (d)-[:HAS_CHUNK]->(c:Chunk)
RETURN COUNT(DISTINCT d) as Dokumente,
       COUNT(c) as Chunks,
       d.sgb_nummer as SGB
ORDER BY SGB

// 2. Vertrauenswürdigkeit pro Quelle
MATCH (d:Document)
RETURN d.source_domain as Quelle,
       AVG(d.trust_score) as Durchschnitt_Trust,
       COUNT(d) as Anzahl
ORDER BY Durchschnitt_Trust DESC

// 3. SGB II Übersicht
MATCH (d:Document {sgb_nummer: "II"})
RETURN d.filename, d.document_type, d.trust_score, d.stand_datum
ORDER BY d.type_priority

// 4. Finde Regelbedarfe (§ 20)
MATCH (d:Document {sgb_nummer: "II"})-[:CONTAINS_PARAGRAPH]->(p:Paragraph {paragraph_nummer: "20"})
RETURN d.document_type, d.filename, SUBSTRING(p.content, 0, 500) as Inhalt
ORDER BY d.type_priority
```

---

## 🎯 Performance-Optimierung für Aura

### 1. Batch-Upload optimiert
- Upload in Batches von 10 Dokumenten
- Reduziert Cloud-Roundtrips
- `batch_add_documents(docs, batch_size=10)`

### 2. Connection Pooling
- `max_connection_pool_size=10`
- `connection_timeout=30s`
- Wiederverwendet Connections

### 3. Query Caching
- Häufige Queries gecacht (100 Einträge)
- Reduziert Cloud-Queries
- `_query_cache` in `SozialrechtNeo4jRAG`

---

## 📥 Alternative: Bulk Import

Für **sehr große Datenmengen** (>1000 PDFs):

### Option 1: Neo4j Admin Import

```bash
# 1. Exportiere zu CSV
python scripts/export_to_csv.py

# 2. Upload CSV zu Aura via neo4j-admin
# (Nur in Enterprise/Professional Tier)
```

### Option 2: APOC Load CSV

```cypher
// In Aura Browser
LOAD CSV WITH HEADERS FROM 'https://your-server.com/documents.csv' AS row
CREATE (d:Document {
  id: row.id,
  sgb_nummer: row.sgb,
  trust_score: toInteger(row.trust_score)
  // ...
})
```

---

## 🔐 Sicherheit

### Credentials Protection

```bash
# .env wird NICHT committed (.gitignore)
echo ".env" >> .gitignore

# Verwende Umgebungsvariablen in Production
export NEO4J_URI="neo4j+s://xxxxx.databases.neo4j.io"
export NEO4J_PASSWORD="xxx"

# Oder Azure Key Vault (siehe ms-agentf-neo4j Integration)
```

### Connection Encryption

Aura erzwingt TLS: `neo4j+s://` (secure)
- Zertifikats-Validierung automatisch
- Verschlüsselte Verbindung

---

## 📊 Monitoring & Analytics

### Aura Console Metrics

**Verfügbar in Console**:
- Query performance
- Storage usage
- Connection count
- Slow queries

### Custom Analytics

```cypher
// Chunk-Größen-Verteilung
MATCH (c:Chunk)
RETURN LENGTH(c.text) as size, COUNT(*) as count
ORDER BY size

// Dokumente pro Typ
MATCH (d:Document)
RETURN d.document_type, COUNT(*) as anzahl
ORDER BY anzahl DESC

// Paragraph-Abdeckung
MATCH (p:Paragraph)
RETURN p.sgb_nummer, COUNT(*) as paragraphen
ORDER BY paragraphen DESC
```

---

## 🚨 Bekannte Probleme

### 1. GDS Funktionen fehlen
**Symptom**: `gds.similarity.cosine()` Fehler
**Lösung**: ✅ Code nutzt bereits NumPy Fallback

### 2. Langsamer Upload
**Symptom**: 20+ Minuten für 50 PDFs
**Lösung**: Batch-Size erhöhen (bereits optimiert)

### 3. Connection Timeouts
**Symptom**: `ConnectionError` bei großen Embeddings
**Lösung**: `connection_timeout=30s` (bereits gesetzt)

---

## ✅ Validierung

Nach Upload zu Aura:

```bash
# Test Hybrid Search
python -c "
from src.sozialrecht_neo4j_rag import SozialrechtNeo4jRAG

rag = SozialrechtNeo4jRAG()

# Test query
response = rag.get_hybrid_answer('Was ist der Regelbedarf für Alleinstehende?')
print(response['answer'])

rag.close()
"
```

**Erwartetes Ergebnis**:
- Gesetz-Quelle: SGB II § 20 (563€)
- Weisungs-Quelle: FW § 20 (Verfahren)
- Trust-Scores angezeigt
- Disclaimer enthalten

---

## 📞 Support

**Neo4j Aura**:
- Console: https://console.neo4j.io
- Docs: https://neo4j.com/docs/aura/
- Support: https://neo4j.com/support/

**Dieses Projekt**:
- GitHub: https://github.com/ma3u/Sozialrecht_RAG
- Issues: https://github.com/ma3u/Sozialrecht_RAG/issues

---

**Erstellt**: 2025-10-10
**Author**: ma3u
**Neo4j Version**: 2025.09.0 (compatible with Aura)
