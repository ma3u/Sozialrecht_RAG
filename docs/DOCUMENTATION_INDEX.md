# Documentation Index

Complete guide to all documentation in the Sozialrecht RAG project.

## 📖 Table of Contents

1. [Quick Navigation](#quick-navigation)
2. [Getting Started](#getting-started)
3. [Technical Documentation](#technical-documentation)
4. [User Guides](#user-guides)
5. [Testing & Validation](#testing--validation)
6. [Configuration](#configuration)
7. [Development](#development)

---

## Quick Navigation

### 🚀 For New Users
1. Start with **[README.md](../README.md)** - Project overview
2. Follow **[QUICKSTART.md](../QUICKSTART.md)** - Quick installation guide
3. Read **[Configuration Guide](#configuration)** - Setup instructions

### 👨‍💼 For Case Workers (Sachbearbeiter)
1. **[User Journeys (German)](BENUTZER_JOURNEYS_DE.md)** - 20 real-world scenarios
2. **[Use Case Validation](USE_CASE_VALIDATION.md)** - Test coverage details
3. **[Cypher Queries](../cypher/)** - Ready-to-use queries

### 🔧 For Developers
1. **[Scripts Directory Guide](../scripts/README.md)** - All scripts documented
2. **[Schema Documentation](../README.md#schema-documentation)** - Graph structure
3. **[Testing Guide](#testing--validation)** - How to run tests

### 📊 For Analysts
1. **[SGB Coverage Analysis](SGB_COVERAGE_ANALYSIS.md)** - Data quality metrics
2. **[Graph Analysis Reports](../logs/graph_analysis/)** - Statistical insights
3. **[Complete Import Summary](../COMPLETE_IMPORT_SUMMARY.md)** - Import details

---

## Getting Started

### Installation & Setup

| Document | Description | Audience |
|----------|-------------|----------|
| **[README.md](../README.md)** | Main project documentation | Everyone |
| **[QUICKSTART.md](../QUICKSTART.md)** | Fast setup guide (5 minutes) | New users |
| **[Configuration Guide](#configuration)** | Detailed configuration steps | Administrators |
| **[Docker Deployment](../DEPLOYMENT_NEO4J_DESKTOP.md)** | Neo4j Desktop setup | Developers |

### Data Import

| Document | Description | Link |
|----------|-------------|------|
| **Complete Import Guide** | Full data import process | [COMPLETE_IMPORT_SUMMARY.md](../COMPLETE_IMPORT_SUMMARY.md) |
| **Import Script** | Automated import | [complete_knowledge_graph_import.py](../scripts/README.md#data-import--processing) |
| **SGB Coverage** | Which SGBs have data | [SGB_COVERAGE_ANALYSIS.md](SGB_COVERAGE_ANALYSIS.md) |

---

## Technical Documentation

### Architecture & Design

| Topic | Document | Key Information |
|-------|----------|-----------------|
| **Graph Schema** | [README.md § Schema](../README.md#-schema-documentation) | Node labels, relationships, properties |
| **Graph Architecture** | [README.md § Architecture](../README.md#graph-architecture) | Hierarchical structure |
| **Data Statistics** | [README.md § Statistics](../README.md#-current-statistics-january-2025) | 61,901 nodes, 60,511 relationships |

### Database Management

| Task | Script | Documentation |
|------|--------|---------------|
| **Setup Indexes** | `setup_neo4j_indexes.py` | [Scripts README](../scripts/README.md#neo4j-database-management) |
| **Generate Embeddings** | `generate_embeddings.py` | [Scripts README](../scripts/README.md#neo4j-database-management) |
| **Fix Vector Index** | `fix_vector_index.py` | [Scripts README](../scripts/README.md#neo4j-database-management) |
| **Analyze Schema** | `analyze_graph_schema.py` | [Scripts README](../scripts/README.md#analysis--debugging) |

### Query Collections

All Cypher queries are organized in the `cypher/` directory:

| File | Purpose | Examples |
|------|---------|----------|
| `01_graph_statistics.cypher` | Database metrics | Node counts, relationship types |
| `02_gesetze_weisungen_beziehungen.cypher` | Law-guideline links | Cross-references |
| `03_sachbearbeiter_workflows.cypher` | Case worker queries | Bürgergeld application checks |
| `04_graph_visualisierung.cypher` | Visualization queries | SGB structure trees |
| `05_rag_sachbearbeiter_queries.cypher` | RAG-optimized queries | Semantic search |

📖 See: [Cypher Query Guide](../cypher/ANLEITUNG_NEO4J_BROWSER.md)

---

## User Guides

### For Case Workers (Sachbearbeiter)

| Guide | Language | Content |
|-------|----------|---------|
| **[User Journeys](BENUTZER_JOURNEYS_DE.md)** | 🇩🇪 German | 20 real-world scenarios with BPMN diagrams |
| **[User Journeys (EN)](../USER_JOURNEYS.md)** | 🇬🇧 English | Older version, 14 scenarios |
| **[Use Case Validation](USE_CASE_VALIDATION.md)** | 🇬🇧 English | Test results for all 20 use cases |

### Use Case Categories

1. **SGB II (Grundsicherung)** - 8 use cases
   - Regelbedarf, Leistungsberechtigung, Einkommen, Vermögen
   - Mehrbedarf, Unterkunft, Sanktionen, EGV
   
2. **Cross-SGB Queries** - 7 use cases
   - ALG I, Krankenversicherung, Rentenversicherung
   - Rehabilitation, Sozialhilfe, Datenschutz
   
3. **Workflow & Integration** - 5 use cases
   - Complete application workflow, navigation, semantic search
   - Guidelines integration, amendment history

📖 See: [Complete Use Case List](BENUTZER_JOURNEYS_DE.md#inhaltsverzeichnis)

---

## Testing & Validation

### Evaluation Suite

**Main Test Script:** `scripts/evaluate_sachbearbeiter_use_cases.py`

```bash
# Run all 20 use case tests
python scripts/evaluate_sachbearbeiter_use_cases.py
```

**Current Status (November 1, 2025):**
- ✅ **20/20 tests passing** (100% success rate)
- ⚡ **Average query time:** 4.32ms
- 📊 **Quality score:** 100%

**Output:** `logs/sachbearbeiter_evaluation.json`

### Test Categories

| Category | Use Cases | Status | Details |
|----------|-----------|--------|---------|
| **SGB II Queries** | UC01-UC08 | ✅ 8/8 passing | Core benefit calculations |
| **Cross-SGB Queries** | UC09-UC15 | ✅ 7/7 passing | Multi-law references |
| **Workflow Tests** | UC16-UC20 | ✅ 5/5 passing | Integration scenarios |

### Individual Test Descriptions

#### SGB II (Grundsicherung) Tests

```python
# UC01: Regelbedarf ermitteln
# Tests: § 20 SGB II queries, chunk availability
# Expected: ≥1 result with title and chunks

# UC02: Leistungsberechtigung prüfen  
# Tests: §§ 7-9 age, capacity, need requirements
# Expected: ≥3 norms found

# UC03: Einkommen berechnen
# Tests: § 11, 11a, 11b income calculation
# Expected: ≥5 results with allowances

# UC04: Vermögen prüfen
# Tests: § 12 asset limits and exemptions
# Expected: ≥1 result with 40 chunks

# UC05: Mehrbedarf Alleinerziehende
# Tests: § 21 additional needs calculations
# Expected: ≥2 results for different types

# UC06: Kosten der Unterkunft
# Tests: § 22 housing costs, heating
# Expected: ≥1 result with 96 chunks

# UC07: Sanktionen prüfen
# Tests: §§ 31-32 sanctions for violations
# Expected: ≥3 results with types

# UC08: Eingliederungsvereinbarung
# Tests: § 15 integration agreements
# Expected: ≥1 result with text units
```

#### Cross-SGB Tests

```python
# UC09: ALG I Anspruchsprüfung
# Tests: SGB III §§ 136-143 unemployment benefit
# Expected: ≥2 results

# UC10: Zuständigkeit klären
# Tests: SGB II §§ 37, 40 jurisdiction
# Expected: ≥2 results with territorial rules

# UC11: Krankenversicherung
# Tests: SGB V §§ 106-106d health insurance
# Expected: ≥2 results (economic efficiency checks)

# UC12: Rentenversicherung
# Tests: SGB VI §§ 100-107 pension rules
# Expected: ≥3 results (start, change, end)

# UC13: Rehabilitation
# Tests: SGB IX §§ 100-105 integration support
# Expected: ≥4 results for disabled persons

# UC14: Sozialhilfe
# Tests: SGB XII §§ 102-106 social assistance
# Expected: ≥3 results (cost reimbursement)

# UC15: Sozialdatenschutz
# Tests: SGB X §§ 67-69 data protection
# Expected: ≥2 results with privacy rules
```

#### Workflow Tests

```python
# UC16: Vollständiger Antrag
# Tests: Complete application workflow across 10 paragraphs
# Expected: ≥8 results in correct order

# UC17: Strukturnavigation
# Tests: Hierarchical navigation through SGB II structure
# Expected: ≥5 structural units with norm counts

# UC18: Semantische Suche
# Tests: Full-text search for "Regelbedarf"
# Expected: ≥1 result with chunk counts

# UC19: Fachliche Weisungen
# Tests: PDF guidelines linked to laws
# Expected: ≥1 document with trust score

# UC20: Änderungshistorie
# Tests: Amendment tracking with dates
# Expected: ≥1 amendment with BGBl reference
```

### Running Specific Tests

```python
# Run single test category
from scripts.evaluate_sachbearbeiter_use_cases import SachbearbeiterEvaluator

evaluator = SachbearbeiterEvaluator()

# Run specific test
evaluator.uc01_regelbedarf_ermitteln()
evaluator.uc16_kompletter_buergergeld_antrag()

# Run category
# SGB II tests: uc01 - uc08
# Cross-SGB: uc09 - uc15  
# Workflow: uc16 - uc20
```

### Analysis & Debugging Tools

| Tool | Purpose | Command |
|------|---------|---------|
| **Graph Analysis** | Relationship patterns | `python scripts/analyze_graph_relationships.py` |
| **Schema Analysis** | Node/relationship types | `python scripts/analyze_graph_schema.py` |
| **GraphRAG Status** | Import completeness | `python scripts/graphrag_status.py` |
| **Vector Search Test** | Embedding quality | `python scripts/test_vector_search.py` |

📖 See: [Scripts README](../scripts/README.md#evaluation--testing)

---

## Configuration

### 1. Environment Setup

#### Required Environment Variables

Create `.env` file in project root:

```bash
# Neo4j Connection (Required)
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your_secure_password_here

# Database Name (Optional, default: neo4j)
NEO4J_DATABASE=neo4j

# OpenAI API (Optional, for PDF processing)
OPENAI_API_KEY=sk-your-key-here

# Embedding Model (Optional, default shown)
EMBEDDING_MODEL=paraphrase-multilingual-mpnet-base-v2
EMBEDDING_DIMENSION=768

# Logging (Optional)
LOG_LEVEL=INFO
```

#### Environment Variable Reference

| Variable | Required | Default | Purpose |
|----------|----------|---------|---------|
| `NEO4J_URI` | ✅ Yes | `bolt://localhost:7687` | Neo4j connection string |
| `NEO4J_USERNAME` | ✅ Yes | `neo4j` | Database username |
| `NEO4J_PASSWORD` | ✅ Yes | - | Database password |
| `NEO4J_DATABASE` | ❌ No | `neo4j` | Database name |
| `OPENAI_API_KEY` | ❌ No | - | For PDF chunking (optional) |
| `EMBEDDING_MODEL` | ❌ No | `paraphrase-multilingual-mpnet-base-v2` | Sentence transformer model |
| `EMBEDDING_DIMENSION` | ❌ No | `768` | Vector dimension |

### 2. Neo4j Configuration

#### Recommended `neo4j.conf` Settings

```properties
# === Memory Configuration ===
# Heap size (2-4GB for this dataset)
dbms.memory.heap.initial_size=2G
dbms.memory.heap.max_size=4G

# Page cache (2-4GB recommended)
dbms.memory.pagecache.size=2G

# === Performance ===
# Transaction log retention
dbms.tx_log.rotation.retention_policy=2 days

# Query timeout (30 seconds)
dbms.transaction.timeout=30s

# === Indexes ===
# Fulltext index consistency
db.index.fulltext.eventually_consistent=false

# === Security ===
# Enable authentication
dbms.security.auth_enabled=true

# Default database
dbms.default_database=neo4j

# === Network ===
# Bolt connector
dbms.connector.bolt.enabled=true
dbms.connector.bolt.listen_address=:7687

# HTTP connector (for browser)
dbms.connector.http.enabled=true
dbms.connector.http.listen_address=:7474

# === Logging ===
dbms.logs.query.enabled=true
dbms.logs.query.threshold=1s
```

#### Docker Configuration

Use provided `docker-compose.yml`:

```yaml
version: '3.8'
services:
  neo4j:
    image: neo4j:5.15-community
    ports:
      - "7474:7474"  # HTTP
      - "7687:7687"  # Bolt
    environment:
      - NEO4J_AUTH=neo4j/your_password
      - NEO4J_PLUGINS=["apoc"]
      - NEO4J_dbms_memory_heap_max__size=4G
      - NEO4J_dbms_memory_pagecache_size=2G
    volumes:
      - neo4j_data:/data
      - neo4j_logs:/logs
      - neo4j_import:/var/lib/neo4j/import

volumes:
  neo4j_data:
  neo4j_logs:
  neo4j_import:
```

Start with:
```bash
docker-compose up -d
```

### 3. Index Setup

#### Create Required Indexes

Run the setup script:

```bash
python scripts/setup_neo4j_indexes.py
```

This creates:

**Property Indexes:**
```cypher
CREATE INDEX legal_norm_paragraph IF NOT EXISTS
FOR (n:LegalNorm) ON (n.paragraph_nummer)

CREATE INDEX legal_norm_enbez IF NOT EXISTS  
FOR (n:LegalNorm) ON (n.enbez)

CREATE INDEX legal_doc_sgb IF NOT EXISTS
FOR (d:LegalDocument) ON (d.sgb_nummer)

CREATE INDEX chunk_paragraph_context IF NOT EXISTS
FOR (c:Chunk) ON (c.paragraph_context)
```

**Vector Index:**
```cypher
CREATE VECTOR INDEX chunk_embeddings IF NOT EXISTS
FOR (c:Chunk) ON (c.embedding)
OPTIONS {
  indexConfig: {
    `vector.dimensions`: 768,
    `vector.similarity_function`: 'cosine'
  }
}
```

**Fulltext Index:**
```cypher
CREATE FULLTEXT INDEX chunk_text_search IF NOT EXISTS
FOR (c:Chunk) ON EACH [c.text, c.paragraph_context]
```

#### Verify Indexes

```cypher
// Show all indexes
SHOW INDEXES

// Check index usage
EXPLAIN MATCH (n:LegalNorm {paragraph_nummer: "20"}) RETURN n
```

### 4. Embedding Configuration

#### Install Sentence Transformers

```bash
pip install sentence-transformers
```

#### Generate Embeddings

```bash
# Generate embeddings for all chunks
python scripts/generate_embeddings.py

# Options:
# --batch-size 32    # Process 32 chunks at a time
# --model-name       # Override default model
```

#### Model Options

| Model | Dimensions | Languages | Quality | Speed |
|-------|------------|-----------|---------|-------|
| `paraphrase-multilingual-mpnet-base-v2` | 768 | 50+ | ⭐⭐⭐⭐⭐ | Medium |
| `distiluse-base-multilingual-cased-v2` | 512 | 50+ | ⭐⭐⭐⭐ | Fast |
| `paraphrase-multilingual-MiniLM-L12-v2` | 384 | 50+ | ⭐⭐⭐ | Very Fast |

### 5. Performance Tuning

#### Query Optimization

```cypher
// Use indexes explicitly
MATCH (n:LegalNorm {paragraph_nummer: $para})
USING INDEX n:LegalNorm(paragraph_nummer)
RETURN n

// Limit relationship hops
MATCH path = (d:LegalDocument)-[*1..3]->(n:LegalNorm)
RETURN path LIMIT 100

// Use specific relationship types
MATCH (d)-[:HAS_STRUCTURE|CONTAINS_NORM]->(n)
```

#### Monitoring Queries

```cypher
// Show slow queries
CALL dbms.listQueries() 
YIELD query, elapsedTimeMillis 
WHERE elapsedTimeMillis > 1000
RETURN query, elapsedTimeMillis

// Query statistics
CALL db.stats.retrieve('QUERY')
```

---

## Development

### Project Structure

```
Sozialrecht_RAG/
├── README.md                 # Main documentation
├── scripts/                  # All executable scripts
│   ├── README.md            # Scripts guide
│   ├── evaluate_*.py        # Test scripts
│   ├── setup_*.py           # Setup scripts
│   └── analyze_*.py         # Analysis scripts
├── src/                      # Source code
│   ├── graphrag_*.py        # GraphRAG modules
│   ├── neo4j_*.py           # Neo4j integration
│   └── xml_*.py             # XML parsers
├── docs/                     # Documentation
│   ├── DOCUMENTATION_INDEX.md   # This file
│   ├── BENUTZER_JOURNEYS_DE.md  # User journeys
│   ├── USE_CASE_VALIDATION.md   # Test validation
│   └── SGB_COVERAGE_ANALYSIS.md # Data analysis
├── cypher/                   # Cypher query files
│   ├── 01_graph_statistics.cypher
│   ├── 03_sachbearbeiter_workflows.cypher
│   └── 05_rag_sachbearbeiter_queries.cypher
├── config/                   # Configuration files
├── logs/                     # Log files
│   ├── sachbearbeiter_evaluation.json
│   └── graph_analysis/
├── data/                     # Data files
│   └── fachliche_weisungen/ # PDF guidelines
└── xml_cache/                # Cached XML files
```

### Scripts Organization

See detailed breakdown: **[scripts/README.md](../scripts/README.md)**

**Active Scripts:**
- Evaluation & Testing (3 scripts)
- Neo4j Management (3 scripts)  
- Data Import (2 scripts)
- Analysis & Debugging (4 scripts)

**Archive Scripts:**
- Data Repair (6 scripts)
- Legacy Testing (3 scripts)
- One-time Setup (4 scripts)

### Contributing Guidelines

#### Before Committing

```bash
# 1. Run tests
python scripts/evaluate_sachbearbeiter_use_cases.py

# 2. Verify no regressions  
# - All 20 tests must pass
# - No new orphaned nodes
# - Query time < 10ms average

# 3. Update documentation if needed
# - Update README.md for API changes
# - Update scripts/README.md for new scripts
# - Add entries to DOCUMENTATION_INDEX.md

# 4. Format code
black src/ scripts/
isort src/ scripts/
```

#### Commit Message Format

```
type(scope): subject

body (optional)

footer (optional)
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation only
- `test`: Test changes
- `refactor`: Code refactoring
- `perf`: Performance improvement

**Examples:**
```
feat(query): add vector similarity search for chunks

fix(uc17): resolve Cypher syntax error in structure navigation

docs(readme): update test results to 100% pass rate
```

---

## Quick Reference Card

### Essential Commands

```bash
# === Setup ===
python scripts/setup_neo4j_indexes.py          # Create indexes
python scripts/generate_embeddings.py          # Generate vectors
python scripts/complete_knowledge_graph_import.py  # Import data

# === Testing ===
python scripts/evaluate_sachbearbeiter_use_cases.py  # Run all tests
python scripts/graphrag_status.py             # Check status

# === Analysis ===
python scripts/analyze_graph_schema.py        # Schema analysis
python scripts/analyze_graph_relationships.py # Relationship analysis

# === Monitoring ===
python scripts/dashboard.py                    # Start dashboard
```

### Key Cypher Queries

```cypher
// Count all nodes
MATCH (n) RETURN labels(n) as label, count(*) as count

// Find paragraph
MATCH (n:LegalNorm {paragraph_nummer: "20"})
RETURN n.enbez, n.titel

// Semantic search
CALL db.index.vector.queryNodes('chunk_embeddings', 5, $embedding)
YIELD node, score
RETURN node.text, score

// Use case query
MATCH (doc:LegalDocument {sgb_nummer: "II"})
  -[:HAS_STRUCTURE|CONTAINS_NORM*1..3]->(norm:LegalNorm)
WHERE norm.paragraph_nummer IN ["7", "11", "20"]
RETURN norm.enbez, norm.titel
```

---

## Support & Resources

### Documentation Links

- **Main README:** [README.md](../README.md)
- **Quick Start:** [QUICKSTART.md](../QUICKSTART.md)
- **Scripts Guide:** [scripts/README.md](../scripts/README.md)
- **User Journeys:** [BENUTZER_JOURNEYS_DE.md](BENUTZER_JOURNEYS_DE.md)
- **Test Results:** [USE_CASE_VALIDATION.md](USE_CASE_VALIDATION.md)

### Log Files

- **Test Results:** `logs/sachbearbeiter_evaluation.json`
- **Import Logs:** `logs/complete_import_*.log`
- **Analysis Reports:** `logs/graph_analysis/`

### External Resources

- **Neo4j Docs:** https://neo4j.com/docs/
- **Cypher Manual:** https://neo4j.com/docs/cypher-manual/
- **German Law Source:** https://www.gesetze-im-internet.de/
- **Sentence Transformers:** https://www.sbert.net/

---

**Last Updated:** November 1, 2025  
**Version:** 2.2  
**Status:** ✅ Complete and Production-Ready
