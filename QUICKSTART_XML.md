# XML Schema Extension - Quick Start

## Overview

Phase 1-2 is complete! You can now import structured XML from gesetze-im-internet.de into Neo4j with 100% trust score.

## Quick Start (5 Minutes)

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Start Neo4j

```bash
docker-compose up -d
```

### 3. Run Schema Migration

```bash
python scripts/migrate_to_xml_schema.py
```

### 4. Test with SGB II

```bash
python scripts/test_xml_phase1.py
```

This will:
- Download SGB II XML (cached after first run)
- Parse 86 legal norms with full structure
- Build knowledge graph in Neo4j
- Generate embeddings for RAG
- Run validation queries

**Expected time:** 3-5 minutes (first run with embeddings)

## What You Get

### Structured Data in Neo4j

```
LegalDocument (SGB II) [100% trust]
  ├── 11 StructuralUnits (Chapters)
  ├── 86 LegalNorms (§ paragraphs)
  ├── 200+ TextUnits (Absätze)
  ├── 50+ Amendments (history)
  └── 150+ Chunks (with embeddings for RAG)
```

### Sample Query

```cypher
// Find § 20 SGB II with full context
MATCH (d:LegalDocument {sgb_nummer: 'II'})
  -[:HAS_STRUCTURE]->(s:StructuralUnit)
  -[:CONTAINS_NORM]->(n:LegalNorm {paragraph_nummer: '20'})
RETURN n.enbez, n.titel, n.content_text
```

## Next Steps

### Import More SGBs

Modify `scripts/test_xml_phase1.py` to loop through all SGBs:

```python
for sgb_num in ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X", "XI", "XII", "XIV"]:
    xml_path = downloader.download_law_xml(sgb_num)
    document = parser.parse_dokument(xml_path)
    kg_builder.build_from_xml(document)
```

### Use in RAG Queries

```python
from src.graphrag_legal_extractor import LegalKnowledgeGraphBuilder
from neo4j import GraphDatabase

driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "password"))

# Query with structural context
with driver.session() as session:
    result = session.run("""
        MATCH (n:LegalNorm {paragraph_nummer: '20'})
          -[:HAS_CHUNK]->(c:Chunk)
        RETURN n.enbez, n.titel, c.text
        LIMIT 5
    """)
    for record in result:
        print(f"{record['enbez']}: {record['titel']}")
        print(f"  {record['text'][:100]}...")
```

## Files Created

- `src/xml_downloader.py` - Downloads XML from gesetze-im-internet.de
- `src/xml_legal_parser.py` - Parses XML structure
- `src/graphrag_legal_extractor.py` - Builds Neo4j knowledge graph
- `cypher/xml_schema.cypher` - Neo4j schema definition
- `scripts/migrate_to_xml_schema.py` - Schema migration
- `scripts/test_xml_phase1.py` - Comprehensive test
- `docs/PHASE1_2_IMPLEMENTATION.md` - Complete documentation

## Troubleshooting

### Neo4j Not Running

```bash
docker-compose up -d
docker ps | grep neo4j
```

### Dependencies Missing

```bash
pip install --upgrade -r requirements.txt
```

### Test Fails

Check logs:
```bash
python scripts/test_xml_phase1.py 2>&1 | tee test_output.log
```

## Documentation

- **Full Implementation Guide**: `docs/PHASE1_2_IMPLEMENTATION.md`
- **Issue #2**: [XML Schema Extension](https://github.com/ma3u/Sozialrecht_RAG/issues/2)
- **Planning Document**: `GITHUB_ISSUE_XML_SCHEMA_EXTENSION.md`

## Status

✅ **Phase 1**: XML Processing Infrastructure  
✅ **Phase 2**: Neo4j Schema Migration  
⏳ **Phase 3**: Data Ingestion (all SGBs)  
⏳ **Phase 4**: Enhanced RAG Integration  
⏳ **Phase 5**: Testing & Documentation

---

**Questions?** Open an issue on GitHub or check the full documentation.
