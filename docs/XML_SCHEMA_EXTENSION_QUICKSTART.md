# XML Schema Extension - Quick Start

> **Full Planning Document**: [`GITHUB_ISSUE_XML_SCHEMA_EXTENSION.md`](../GITHUB_ISSUE_XML_SCHEMA_EXTENSION.md)

## 🎯 Project Goal

Replace PDF-based extraction with structured XML processing from gesetze-im-internet.de using neo4j-graphrag-python.

## 📊 Key Improvements

| Aspect | Current (PDF) | Target (XML) |
|--------|--------------|--------------|
| Trust Score | 95% | **100%** (official source) |
| Structure | Paragraph-aware chunks | **Full legal hierarchy** |
| Accuracy | OCR-dependent | **No parsing errors** |
| Queries | Text search | **Structure-aware navigation** |
| Updates | Manual PDF download | **Automated XML polling** |

## 🏗️ New Schema Overview

```
LegalDocument (SGB II)
  └─ StructuralUnit (Kapitel 1)
      └─ LegalNorm (§ 1)
          ├─ TextUnit (Absatz 1, 2, ...)
          │   └─ ListItem (1., 2., ...)
          └─ Amendment (2025-02-24)
```

## 🛠️ 7-Week Implementation

### Week 1-2: XML Infrastructure
- Download/parse XML from gesetze-im-internet.de
- Integrate neo4j-graphrag-python
- Test with SGB II

**Key Files**:
- `src/xml_downloader.py`
- `src/xml_legal_parser.py`
- `src/graphrag_legal_extractor.py`

### Week 3: Schema Migration
- Create new node types (LegalDocument, LegalNorm, etc.)
- Maintain compatibility with old schema
- Migration script for existing data

**Key Files**:
- `cypher/xml_schema.cypher`
- `scripts/migrate_to_xml_schema.py`
- `src/compatibility_adapter.py`

### Week 4-5: Data Ingestion
- Import all SGB I-XIV XML
- Generate vector embeddings
- Validate structure

**Key Files**:
- `scripts/import_all_sgb_xml.py`
- `cypher/validation_queries.cypher`
- `tests/test_xml_import.py`

### Week 6: Enhanced RAG
- Structure-aware queries
- Citation resolution
- Amendment tracking

**Key Files**:
- `src/xml_aware_rag.py`
- `src/citation_resolver.py`
- `cypher/advanced_queries.cypher`

### Week 7: Testing & Docs
- Integration tests
- Performance benchmarks
- User documentation

**Key Files**:
- `tests/test_xml_rag_integration.py`
- `docs/XML_SCHEMA_GUIDE.md`
- `scripts/benchmark_xml_rag.py`

## 🔗 Quick Links

### Data Sources
- **XML TOC**: https://www.gesetze-im-internet.de/gii-toc.xml
- **SGB II Example**: https://www.gesetze-im-internet.de/sgb_2/xml.zip

### Neo4j GraphRAG
- **GitHub**: https://github.com/neo4j/neo4j-graphrag-python
- **Docs**: https://neo4j.com/docs/neo4j-graphrag-python/current/

### XML Structure Sample
```xml
<norm>
  <metadaten>
    <jurabk>SGB 2</jurabk>
    <enbez>§ 20</enbez>
    <titel>Regelbedarf zur Sicherung des Lebensunterhalts</titel>
  </metadaten>
  <textdaten>
    <text><Content>
      <P>(1) Der Regelbedarf...</P>
      <P>(2) Als Regelbedarf wird monatlich für Personen...</P>
    </Content></text>
  </textdaten>
</norm>
```

## 🚀 Getting Started

```bash
# 1. Add lxml to requirements
echo "lxml==5.3.0" >> requirements.txt
pip install -r requirements.txt

# 2. Download sample XML
curl -o /tmp/sgb2.xml.zip https://www.gesetze-im-internet.de/sgb_2/xml.zip
unzip /tmp/sgb2.xml.zip -d /tmp/

# 3. Explore structure
head -200 /tmp/BJNR295500003.xml

# 4. Start implementing Phase 1
# See GITHUB_ISSUE_XML_SCHEMA_EXTENSION.md for detailed tasks
```

## 📈 Success Criteria

- [ ] All 13 SGB laws imported from XML
- [ ] Query latency < 500ms for paragraph lookups
- [ ] 15%+ accuracy improvement vs PDF approach
- [ ] 95%+ test coverage
- [ ] Complete documentation with examples

## 💡 Key Design Decisions

### 1. Parallel Schema (not replacement)
Run old and new schemas side-by-side during migration

### 2. Chunk Retention
Keep existing RAG chunks for vector search, link to new LegalNorm nodes

### 3. Optional LLM Use
neo4j-graphrag can use LLM for entity extraction, but not required - rule-based also works

### 4. Citation Graph
Phase 4 includes automatic detection of "§ X references § Y" relationships

---

**Questions?** See full document or open GitHub issue
