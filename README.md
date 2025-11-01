# Sozialrecht RAG - German Social Law Knowledge Graph

**Status:** ⚠️ MVP Ready (Production requires SGB X import)  
**Version:** 2.1  
**Last Updated:** January 2025

Comprehensive Knowledge Graph and RAG (Retrieval-Augmented Generation) system for German Social Law (Sozialgesetzbuch I-XIV) with over 61,000 nodes and 60,000 relationships.

🎉 **Latest Achievement:** Orphaned norms repaired! Chunk coverage increased from 17.5% to 40.5% (16,922 chunks now accessible).

---

## 🎯 Project Overview

This system provides intelligent access to German social law for:
- **Sachbearbeiter (Case Workers):** Fast, accurate legal information for benefit decisions
- **Prozessberater (Process Consultants):** Process optimization and workflow design

### Key Features

✅ **Complete SGB Structure:** All 13 social law books (SGB I-XIV) with 4,213 legal norms  
✅ **RAG-Optimized:** 41,747 text chunks with embeddings for semantic search  
✅ **7 SGBs with Chunks:** II, III, IV, V, VI, VIII, XI (16,922 chunks accessible, 40.5%)  
⚠️ **5 SGBs need Chunks:** I, VII, IX, X, XII (structural data only)  
✅ **Amendment Tracking:** 21 amendments with historical dates (0.5% coverage)  
✅ **Fachliche Weisungen:** 36 PDF guidelines integrated  
✅ **Graph Database:** Neo4j with hierarchical legal structure  
✅ **60% Use Case Coverage:** 12/20 user journeys production-ready

---

## 📊 Current Statistics (January 2025)

### Database Content

| Component | Count | Status |
|-----------|-------|--------|
| **Legal Norms** | 4,213 | ✅ Complete |
| **Chunks (Total)** | 41,747 | ✅ Imported |
| **Chunks (Accessible)** | 16,922 (40.5%) | ⚠️ Partial |
| **Orphaned Chunks** | 24,825 (59.5%) | ⚠️ Need import/linking |
| **TextUnits** | 11,145 | ✅ Complete |
| **SGB Books** | 13 | ✅ Structure complete |
| **SGBs with Chunks** | 7 (II, III, IV, V, VI, VIII, XI) | ✅ Production-ready |
| **SGBs without Chunks** | 5 (I, VII, IX, X, XII) | ❌ Import needed |
| **Structural Units** | 458 | ✅ Complete |
| **PDF Documents** | 50 | ✅ Complete |
| **Amendments** | 21 (0.5% coverage) | ⚠️ Very partial |
| **Total Nodes** | 61,901 | - |
| **Total Relationships** | 60,511 | - |

### Recent Changes (January 2025)

🔧 **Orphaned Norms Repair** (✅ Completed):
- **Fixed**: 2,227 orphaned LegalNorm nodes
- **Result**: +9,604 chunks now accessible (23% of total)
- **Coverage**: Increased from 17.5% to 40.5%
- **Script**: `scripts/link_orphaned_norms.py`

### Graph Architecture

```
LegalDocument (13 SGBs)
├── HAS_STRUCTURE ───> StructuralUnit (458)
│                       └── CONTAINS_NORM ───> LegalNorm (4,213)
│                                               ├── HAS_CONTENT ──> TextUnit (11,145)
│                                               ├── HAS_CHUNK ───> Chunk (41,747)
│                                               └── HAS_AMENDMENT ───> Amendment (21)
└── CONTAINS_NORM (direct) ───> LegalNorm (optimization)
```

---

## 🚀 Quick Start

### Prerequisites

```bash
# Required
- Neo4j 5.x (Community or Enterprise)
- Python 3.11+
- 8GB RAM minimum

# Optional
- OpenAI API key (for PDF processing)
```

### Installation

```bash
# 1. Clone repository
git clone https://github.com/ma3u/Sozialrecht_RAG.git
cd Sozialrecht_RAG

# 2. Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Edit .env with your Neo4j credentials

# 5. Start Neo4j
# Via Docker:
docker-compose up -d
# Or local installation: neo4j start
```

### Import Data

```bash
# Full import (all SGBs + PDFs + amendments)
python scripts/complete_knowledge_graph_import.py

# This will:
# - Extract XML files from xml_cache/*.zip
# - Import 13 SGB books with chunks and embeddings
# - Import 36 Fachliche Weisungen PDFs
# - Create amendment relationships
# - Generate comprehensive report
# Duration: ~15 minutes
```

### Verify Installation

```bash
# Run test suite
python scripts/evaluate_sachbearbeiter_use_cases.py

# Expected: 12/20 use cases passing (60%)
# See logs/sachbearbeiter_evaluation.json for details
```

---

## 📚 Documentation

### Core Documents

1. **[docs/SGB_COVERAGE_ANALYSIS.md](docs/SGB_COVERAGE_ANALYSIS.md)** ⭐ - Comprehensive SGB coverage report & repair strategy
2. **[docs/BENUTZER_JOURNEYS_DE.md](docs/BENUTZER_JOURNEYS_DE.md)** ⭐ - 20 German user journeys with BPMN diagrams
3. **[docs/USE_CASE_VALIDATION.md](docs/USE_CASE_VALIDATION.md)** ⭐ - Use case validation against data quality
4. **[docs/AKTIONSPLAN_NACH_ANALYSE.md](docs/AKTIONSPLAN_NACH_ANALYSE.md)** ⭐ - Action plan & roadmap
5. **[COMPLETE_IMPORT_SUMMARY.md](COMPLETE_IMPORT_SUMMARY.md)** - Original import report
6. **[USER_JOURNEYS.md](USER_JOURNEYS.md)** - English user journeys (older version)
7. **[QUICKSTART.md](QUICKSTART.md)** - Quick start guide
8. **logs/graph_analysis/** - Analysis reports (Sachbearbeiter & Prozessberater)

### Repair & Maintenance Scripts

- **`scripts/link_orphaned_norms.py`** - Fix orphaned norms (✅ executed successfully)
- **`scripts/fix_sgb_coverage.py`** - Alternative repair via StructuralUnits
- **`scripts/analyze_graph_relationships.py`** - Comprehensive graph analysis

### Cypher Query Collections

All queries are in `cypher/` directory:

- `01_graph_statistics.cypher` - Database statistics and metrics
- `02_gesetze_weisungen_beziehungen.cypher` - Law-guideline relationships
- `03_sachbearbeiter_workflows.cypher` - Case worker workflows
- `04_graph_visualisierung.cypher` - Graph visualizations
- `05_rag_sachbearbeiter_queries.cypher` - RAG queries for case workers

---

## 🧪 Test Scripts

### 1. Evaluation Tests

```bash
# Run 20 Sachbearbeiter use case tests
python scripts/evaluate_sachbearbeiter_use_cases.py

# Output: logs/sachbearbeiter_evaluation.json
# Metrics:
# - Pass rate: 60% (12/20)
# - Avg query time: 21.91ms
# - Quality score: 60%
```

**Current Test Results:**

✅ **Passing (12):**
- UC01: Regelbedarf ermitteln (§ 20)
- UC02: Leistungsberechtigung (§§ 7-9)
- UC03: Einkommen berechnen (§ 11)
- UC04: Vermögen prüfen (§ 12)
- UC05: Mehrbedarf (§ 21)
- UC06: Kosten der Unterkunft (§ 22)
- UC07: Sanktionen (§§ 31-32)
- UC08: Eingliederungsvereinbarung (§ 15)
- UC10: Zuständigkeit (§§ 37, 40)
- UC16: Vollständiger Antrag
- UC18: Semantische Suche
- UC19: Fachliche Weisungen

❌ **Failing (8):** Mostly cross-SGB queries (fixable with query updates)

### 2. Graph Analysis

```bash
# Comprehensive relationship analysis
python scripts/analyze_graph_relationships.py

# Generates:
# - logs/graph_analysis/sachbearbeiter_report_*.md
# - logs/graph_analysis/prozessberater_report_*.md
# - logs/graph_analysis/improvement_suggestions_*.json
# - logs/graph_analysis/analysis_data_*.json
```

### 3. Cypher Script Runner

```bash
# Run all Cypher queries from files
python -c "
from pathlib import Path
from neo4j import GraphDatabase
import os

driver = GraphDatabase.driver(
    os.getenv('NEO4J_URI'),
    auth=(os.getenv('NEO4J_USERNAME'), os.getenv('NEO4J_PASSWORD'))
)

for cypher_file in Path('cypher').glob('*.cypher'):
    print(f'Running {cypher_file.name}...')
    # Execute queries...
"
```

### 4. GraphRAG Status

```bash
# Check import status and quality metrics
python scripts/graphrag_status.py

# Shows:
# - Node/relationship counts
# - Chunk coverage
# - Missing chunks per SGB
# - Amendment coverage
```

---

## 🎯 Use Cases

### For Sachbearbeiter (Case Workers)

**Primary Use Cases:**
1. **Bürgergeld-Antrag prüfen** - Complete application review with legal basis
2. **Sanktionen verhängen** - Apply sanctions with amendment-aware legal grounds
3. **Einkommen/Vermögen berechnen** - Calculate income/assets with cross-SGB references
4. **Mehrbedarf ermitteln** - Determine additional needs for special situations
5. **Kosten der Unterkunft** - Assess reasonable housing costs

**Example Query:**
```cypher
// Find all relevant paragraphs for Bürgergeld application
MATCH (doc:LegalDocument {sgb_nummer: "II"})
  -[:HAS_STRUCTURE|CONTAINS_NORM*1..3]->(norm:LegalNorm)
WHERE norm.paragraph_nummer IN ["7", "8", "9", "11", "12", "20", "21", "22"]
OPTIONAL MATCH (norm)-[:HAS_CHUNK]->(chunk:Chunk)
RETURN norm.enbez, norm.titel, count(chunk) as chunks
ORDER BY norm.paragraph_nummer
```

### For Prozessberater (Process Consultants)

**Primary Use Cases:**
1. **BPMN-Prozesse entwickeln** - Create process models from legal structure
2. **Durchlaufzeiten optimieren** - Identify bottlenecks via graph analysis
3. **Schulungen erstellen** - Generate training materials from graph structure
4. **Qualitätssicherung** - Monitor decision consistency across team
5. **Cross-SGB Kooperation** - Design multi-agency workflows

**Example Query:**
```cypher
// Analyze most frequently queried paragraphs (bottlenecks)
MATCH (norm:LegalNorm)-[:HAS_CHUNK]->(chunk:Chunk)
WITH norm, count(chunk) as chunk_count
ORDER BY chunk_count DESC
LIMIT 10
RETURN norm.paragraph_nummer, norm.titel, chunk_count
```

---

## 🔧 Configuration

### Environment Variables

Create `.env` file from `.env.example`:

```bash
# Neo4j Connection
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your_secure_password

# Optional: OpenAI for PDF processing
OPENAI_API_KEY=sk-your-key-here

# Optional: Embedding model
EMBEDDING_MODEL=paraphrase-multilingual-mpnet-base-v2
```

### Neo4j Configuration

Recommended settings for `neo4j.conf`:

```properties
# Memory
dbms.memory.heap.initial_size=2G
dbms.memory.heap.max_size=4G
dbms.memory.pagecache.size=2G

# Indexes
db.index.fulltext.eventually_consistent=false

# Security
dbms.security.auth_enabled=true
```

---

## 📖 Schema Documentation

### Node Labels

| Label | Count | Description |
|-------|-------|-------------|
| `LegalDocument` | 13 | SGB law books |
| `StructuralUnit` | 458 | Chapters, sections, subsections |
| `LegalNorm` | 4,213 | Individual paragraphs |
| `TextUnit` | 11,145 | Paragraph subsections/clauses |
| `Chunk` | 41,747 | RAG-optimized text blocks |
| `Amendment` | 21 | Legal change records |
| `Document` | 50 | PDF guidelines |
| `Paragraph` | 4,254 | Legacy structure (deprecated) |

### Relationship Types

| Type | Count | Pattern |
|------|-------|---------|
| `HAS_CHUNK` | 41,747 | LegalNorm → Chunk |
| `HAS_CONTENT` | 11,145 | LegalNorm → TextUnit |
| `CONTAINS_PARAGRAPH` | 5,050 | Legacy relationship |
| `CONTAINS_NORM` | 1,831 | StructuralUnit → LegalNorm |
| `HAS_STRUCTURE` | 717 | LegalDocument → StructuralUnit |
| `HAS_AMENDMENT` | 21 | LegalNorm → Amendment |

### Key Properties

**LegalNorm:**
- `paragraph_nummer`: "20", "11a", etc.
- `enbez`: "§ 20 SGB II"
- `titel`: "Regelbedarf zur Sicherung des Lebensunterhalts"
- `content_text`: Full paragraph text
- `order_index`: Position in document

**Chunk:**
- `text`: Content (max 800 chars)
- `embedding`: 768-dim vector
- `paragraph_context`: "II § 20 - Regelbedarf"
- `chunk_index`: Position within norm

---

## ⚠️ Known Issues & Limitations

### 1. Missing Direct Relationships (Priority: High)

**Issue:** Some use case queries expect direct `LegalDocument → LegalNorm` relationships  
**Impact:** 7/20 use cases fail unnecessarily  
**Workaround:**
```cypher
// Use variable-length path
MATCH (doc:LegalDocument)-[:HAS_STRUCTURE|CONTAINS_NORM*1..3]->(norm:LegalNorm)
```
**Fix:** Run optimization script to add direct links:
```bash
python scripts/optimize_graph_relations.py
```

### 2. Incomplete Amendment Data (Priority: Medium)

**Issue:** Only 0.5% of norms have amendment tracking  
**Impact:** Cannot track legal changes over time  
**Solution:** Parse BGBl references from XML metadata

### 3. Orphaned Nodes (Priority: High)

**Issue:** 151 orphaned nodes found  
**Impact:** Nodes not accessible via normal queries  
**Fix:**
```cypher
// Find and connect orphaned LegalNorms
MATCH (norm:LegalNorm)
WHERE NOT (norm)--()
OPTIONAL MATCH (doc:LegalDocument)
WHERE doc.jurabk CONTAINS substring(norm.id, 0, 5)
CREATE (doc)-[:CONTAINS_NORM]->(norm)
```

### 4. Vector Index Missing (Priority: Medium)

**Issue:** No vector index on Chunk.embedding  
**Impact:** Semantic search slower than optimal  
**Fix:**
```cypher
CREATE VECTOR INDEX chunk_embeddings IF NOT EXISTS
FOR (c:Chunk)
ON c.embedding
OPTIONS {indexConfig: {
  `vector.dimensions`: 768,
  `vector.similarity_function`: 'cosine'
}}
```

---

## 🎯 Improvement Roadmap

### Immediate (Priority 1)
- [ ] Add direct `CONTAINS_NORM` optimization relationships
- [ ] Fix orphaned nodes (151 identified)
- [ ] Create vector index for semantic search
- [ ] Update failing use case queries

### Short-term (Priority 2)
- [ ] Enhance amendment parsing (BGBl references)
- [ ] Import remaining Fachliche Weisungen
- [ ] Add compound indexes for performance
- [ ] Create BPMN export functionality

### Medium-term (Priority 3)
- [ ] Implement full PDF chunking with OpenAI
- [ ] Add cross-reference relationships (`REFERENCES`)
- [ ] Create workflow templates for common cases
- [ ] Build training material generator

### Long-term (Priority 4)
- [ ] Historical version tracking (SUPERSEDES chains)
- [ ] ML-based similarity recommendations
- [ ] Real-time updates from gesetze-im-internet.de
- [ ] Integration with case management systems

---

## 🤝 Contributing

### Running Tests Before Commit

```bash
# 1. Run evaluation tests
python scripts/evaluate_sachbearbeiter_use_cases.py

# 2. Check graph quality
python scripts/analyze_graph_relationships.py

# 3. Verify no regressions
# Pass rate should be ≥60%
# No new orphaned nodes
# All SGBs with chunks

# 4. Update documentation if needed
```

### Code Style

- Python: PEP 8
- Cypher: Uppercase keywords, meaningful variable names
- Commit messages: Conventional Commits format

---

## 📞 Support & Contact

### Documentation
- **Full Import Report:** [COMPLETE_IMPORT_SUMMARY.md](COMPLETE_IMPORT_SUMMARY.md)
- **User Journeys:** [USER_JOURNEYS.md](USER_JOURNEYS.md)
- **Analysis Reports:** `logs/graph_analysis/`

### Logs
- **Import Logs:** `logs/complete_import_*.log`
- **Evaluation Results:** `logs/sachbearbeiter_evaluation.json`
- **Graph Analysis:** `logs/graph_analysis/`

### Cypher Queries
- **Statistics:** `cypher/01_graph_statistics.cypher`
- **Workflows:** `cypher/03_sachbearbeiter_workflows.cypher`
- **RAG Queries:** `cypher/05_rag_sachbearbeiter_queries.cypher`

---

## 📜 License

This project processes publicly available German social law from gesetze-im-internet.de.

**Data Sources:**
- XML Law Texts: © Bundesrepublik Deutschland (public domain)
- Fachliche Weisungen: © Bundesagentur für Arbeit (publicly accessible)
- Embedding Model: sentence-transformers/paraphrase-multilingual-mpnet-base-v2 (Apache 2.0)

---

## 🙏 Acknowledgments

- **Data Source:** [gesetze-im-internet.de](https://www.gesetze-im-internet.de/)
- **Embedding Model:** sentence-transformers
- **Database:** Neo4j Community Edition
- **GraphRAG:** neo4j-graphrag-python

---

**Version:** 2.0  
**Last Updated:** November 1, 2025  
**Status:** ✅ Production Ready  
**Test Coverage:** 60% (12/20 use cases)
