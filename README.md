# Sozialrecht RAG - German Social Law Knowledge Graph

**A Neo4j GraphRAG Demonstration Project**

[![Status](https://img.shields.io/badge/status-production%20ready-brightgreen)]()
[![Version](https://img.shields.io/badge/version-2.4-blue)]()
[![Neo4j](https://img.shields.io/badge/neo4j-5.x-008CC1)]()
[![Python](https://img.shields.io/badge/python-3.11+-blue)]()

---

## 🎯 Project Purpose

This project demonstrates **Neo4j Graph Database** combined with **GraphRAG (Graph Retrieval-Augmented Generation)** as a linked knowledge base for intelligent legal information retrieval. It showcases how graph technology can structure complex legal documents to serve different user journeys with semantic search capabilities.

### What This Demonstrates

**Graph Database Architecture**:
- ✅ Hierarchical legal document structure in Neo4j
- ✅ 61,945 nodes with 63,722 relationships
- ✅ Complex multi-level connections (documents → structures → norms → chunks)
- ✅ Amendment tracking with temporal relationships

**GraphRAG Implementation**:
- ✅ Text chunking optimized for legal content
- ✅ 41,781 semantic embeddings for vector search
- ✅ Hybrid retrieval (graph traversal + semantic similarity)
- ✅ Context-aware information retrieval

**Real-World Use Cases**:
- ✅ 20 documented user journeys
- ✅ 100% test coverage with production queries
- ✅ Multiple user personas (case workers, policy analysts, lawyers)

---

## 📊 Current Status

| Component | Count | Status |
|-----------|-------|--------|
| **Legal Documents** | 13 SGB volumes | ✅ Complete |
| **Legal Norms** | 4,203 | ✅ Complete |
| **Text Chunks** | 41,781 | ✅ Complete |
| **Vector Embeddings** | 41,781 (100%) | ✅ Complete |
| **Amendments** | 21 with full metadata | ✅ Complete |
| **BGBl References** | 13 | ✅ Complete |
| **User Journeys** | 20 (all passing) | ✅ Validated |

**Performance**: Average query time < 5ms | Throughput: 79.59 norms/sec

---

## 🚀 Quick Start

### Prerequisites

- **Neo4j 5.x** (Community or Enterprise)
- **Python 3.11+**
- **8GB RAM** minimum

### Installation

```bash
# Clone and setup
git clone https://github.com/ma3u/Sozialrecht_RAG.git
cd Sozialrecht_RAG
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configure
cp .env.example .env
# Edit .env with your Neo4j credentials

# Start Neo4j
docker-compose up -d
# or: neo4j start
```

### Deploy Data

```bash
# Full deployment (all 13 SGB volumes with amendments)
python scripts/deploy_all_sgb_volumes.py
```

This imports:
- 4,203 legal norms across 13 social law books
- 41,781 text chunks with embeddings
- 21 amendments with historical tracking
- Complete graph structure

### Verify

```bash
# Run validation
python scripts/validate_import.py

# Test use cases (all 20 should pass)
python scripts/evaluate_sachbearbeiter_use_cases.py
```

---

## 📖 Documentation

### Core Documentation

**Getting Started**:
- 📘 [Complete Documentation Index](docs/DOCUMENTATION_INDEX.md) - Full guide to all docs
- 📘 [Phase 2 Executive Summary](PHASE_2_EXECUTIVE_SUMMARY.md) - Project achievements and status

**GraphRAG Features**:
- 📗 [Graph Schema Documentation](docs/DOCUMENTATION_INDEX.md#architecture--design) - Node types, relationships, properties
- 📗 [GraphRAG Learnings](docs/NEO4J_GRAPHRAG_LEARNINGS.md) - Implementation insights and best practices

**Amendment Tracking** (Phase 2):
- 📙 [Phase 2 Complete](PHASE_2_COMPLETE.md) - Amendment features overview
- 📙 [Validation Report](PHASE_2_VALIDATION_REPORT.md) - Deployment results and data quality
- 📙 [Implementation Summary](PHASE_2_IMPLEMENTATION_SUMMARY.md) - Technical details

**User Journeys**:
- 👤 [German User Journeys](docs/BENUTZER_JOURNEYS_DE.md) - 20 case worker scenarios (German)
- 👤 [Amendment User Journeys](docs/AMENDMENT_USER_JOURNEYS.md) - 6 amendment-specific scenarios
- 👤 [Use Case Validation](docs/USE_CASE_VALIDATION.md) - Test results for all 20 journeys

### Reports

- 📊 [Deployment Report](docs/reports/DEPLOYMENT_REPORT_20251103_190858.md) - Latest deployment statistics
- 📊 [Amendment Analysis](docs/reports/AMENDMENT_ANALYSIS_SUMMARY.md) - Amendment coverage analysis

### Query Collections

Ready-to-use Cypher queries organized by purpose:
- [01_graph_statistics.cypher](cypher/01_graph_statistics.cypher) - Database metrics
- [03_sachbearbeiter_workflows.cypher](cypher/03_sachbearbeiter_workflows.cypher) - Case worker queries
- [05_rag_sachbearbeiter_queries.cypher](cypher/05_rag_sachbearbeiter_queries.cypher) - RAG-optimized queries

See [Cypher Query Guide](cypher/ANLEITUNG_NEO4J_BROWSER.md) for usage instructions.

---

## 🎭 User Journeys

This project demonstrates GraphRAG serving **different user personas** with tailored information retrieval:

### 1. Case Workers (Sachbearbeiter)
**Scenario**: Daily benefit administration decisions

**Example Journey**: *"Check eligibility for housing benefits"*
```cypher
MATCH (doc:LegalDocument {sgb_nummer: "II"})
  -[:HAS_STRUCTURE|CONTAINS_NORM*1..3]->(norm:LegalNorm)
WHERE norm.paragraph_nummer = "22"
RETURN norm.enbez, norm.titel, norm.content_text
```

**Queries**: Basic facts, paragraph lookup, benefit calculations  
**Documentation**: [BENUTZER_JOURNEYS_DE.md](docs/BENUTZER_JOURNEYS_DE.md) (German, 20 scenarios)

### 2. Legal Researchers
**Scenario**: Historical law changes and impact analysis

**Example Journey**: *"When did § 20 SGB II last change?"*
```cypher
MATCH (norm:Norm {paragraph_nummer: "20"})
  -[:HAS_AMENDMENT]->(a:Amendment)
RETURN a.amendment_date, a.raw_text
ORDER BY a.amendment_date DESC
LIMIT 1
```

**Queries**: Amendment timelines, law impact analysis, BGBl citations  
**Documentation**: [AMENDMENT_USER_JOURNEYS.md](docs/AMENDMENT_USER_JOURNEYS.md) (6 scenarios)

### 3. Policy Analysts
**Scenario**: Cross-law analysis and coverage assessment

**Example Journey**: *"Find all norms affected by a specific law change"*
```cypher
MATCH (a:Amendment {gesetz_ref: "G v. 23.10.2024 I Nr. 323"})
  <-[:HAS_AMENDMENT]-(norm:Norm)
RETURN norm.paragraph_nummer, norm.titel, a.amendment_date
```

**Queries**: Cross-SGB analysis, change impact, statistical aggregations  
**Documentation**: [Query Library](src/queries/amendment_queries.py) (20+ specialized queries)

### 4. Semantic Search Users
**Scenario**: Finding relevant content without knowing exact paragraphs

**Example**: *"regulations about single parents"*
```cypher
CALL db.index.vector.queryNodes('chunk_embeddings', 5, $embedding)
YIELD node, score
MATCH (node)<-[:HAS_CHUNK]-(norm:LegalNorm)
RETURN norm.paragraph_nummer, node.text, score
```

**Features**: Vector similarity search, context-aware retrieval  
**Documentation**: [GraphRAG Status](scripts/graphrag_status.py)

---

## 🏗️ Graph Architecture

### Schema Overview

```
LegalDocument (13 SGBs)
├── HAS_STRUCTURE ─────> StructuralUnit (458)
│   └── CONTAINS_NORM ─> LegalNorm (4,203)
│       ├── HAS_CHUNK ────────> Chunk (41,781)
│       │   └── embedding [768-dim vector]
│       ├── HAS_AMENDMENT ────> Amendment (21)
│       │   └── SUPERSEDED_BY ─> Amendment
│       └── HAS_FUSSNOTE ─────> Fussnote (16)
└── PUBLISHED_IN ──────────────> BGBl (13)
```

### Key Node Types

| Node Type | Purpose | Count | Example Properties |
|-----------|---------|-------|-------------------|
| `LegalDocument` | SGB volumes | 13 | sgb_nummer, jurabk, lange_titel |
| `LegalNorm` | Legal paragraphs | 4,203 | paragraph_nummer, titel, content_text |
| `Chunk` | Text segments for RAG | 41,781 | text, embedding[768], paragraph_context |
| `Amendment` | Historical changes | 21 | amendment_date, artikel, gesetz_ref |
| `BGBl` | Official gazette refs | 13 | year, page, full_reference |

### Relationship Types

| Relationship | Purpose | Count |
|--------------|---------|-------|
| `CONTAINS_NORM` | Document → Norm | 4,203 |
| `HAS_CHUNK` | Norm → Chunk | 41,781 |
| `HAS_AMENDMENT` | Norm → Amendment | 21 |
| `SUPERSEDED_BY` | Amendment timeline | 10 |
| `PUBLISHED_IN` | Document → BGBl | 13 |

**Total**: 61,945 nodes | 63,722 relationships

---

## 🧪 Testing & Validation

### Run All Tests

```bash
# Unit tests (amendment parser)
python tests/test_amendment_parser.py
# Result: 33/33 passing (100%)

# Integration tests (use cases)
python scripts/evaluate_sachbearbeiter_use_cases.py
# Result: 20/20 passing (100%)

# Data validation
python scripts/validate_import.py
# Checks: data quality, relationships, indexes
```

### Test Coverage

- ✅ **Unit Tests**: 33/33 (100%) - Parser functionality
- ✅ **Integration Tests**: 20/20 (100%) - End-to-end user journeys
- ✅ **Data Quality**: 0 orphaned nodes, all relationships valid
- ✅ **Performance**: < 1s query time (target: < 2s)

---

## 💡 Key Features Demonstrated

### 1. Graph Database Capabilities

**Hierarchical Structure**:
- Multi-level document organization (Document → Structure → Norm)
- Efficient traversal with relationship types
- Optimized indexes for fast lookup

**Temporal Relationships**:
- Amendment chains with SUPERSEDED_BY
- Historical state queries (law at specific date)
- Version tracking through Fussnoten

### 2. GraphRAG Implementation

**Hybrid Retrieval**:
- Graph traversal for structural navigation
- Vector similarity for semantic search
- Combined approach for context-aware results

**Chunking Strategy**:
- Legal-optimized text segmentation
- Context preservation with paragraph_context
- 768-dimensional embeddings (Azure OpenAI)

### 3. Production-Ready Features

**Performance**:
- 7 optimized indexes for query speed
- Batch import (79.59 norms/sec)
- Sub-second query response times

**Data Quality**:
- 100% date extraction accuracy
- 0 orphaned nodes
- Comprehensive validation

**Monitoring**:
- Automated deployment reports
- Data quality checks
- Performance metrics tracking

---

## 📁 Project Structure

```
Sozialrecht_RAG/
├── README.md                          # This file
├── PHASE_2_*.md                       # Phase 2 documentation (4 files)
├── docs/                              # Documentation
│   ├── DOCUMENTATION_INDEX.md         # Complete guide
│   ├── BENUTZER_JOURNEYS_DE.md       # User journeys (German)
│   ├── AMENDMENT_USER_JOURNEYS.md    # Amendment scenarios
│   ├── reports/                       # Deployment reports
│   └── archive/                       # Historical docs
├── src/                               # Source code
│   ├── amendment_parser.py            # Amendment extraction
│   ├── xml_to_neo4j_enhanced.py      # Import with amendments
│   ├── queries/                       # Query library
│   └── xml_legal_parser.py           # XML parsing
├── scripts/                           # Executable scripts
│   ├── deploy_all_sgb_volumes.py     # Full deployment
│   ├── validate_import.py            # Validation
│   ├── evaluate_sachbearbeiter_use_cases.py  # Testing
│   └── archive/                       # Historical scripts
├── tests/                             # Unit tests
│   └── test_amendment_parser.py      # Parser tests
├── cypher/                            # Cypher query collections
│   ├── 01_graph_statistics.cypher
│   ├── 03_sachbearbeiter_workflows.cypher
│   └── 05_rag_sachbearbeiter_queries.cypher
└── xml_cache/                         # Source XML files
```

---

## 🎓 Learning Resources

### Understanding This Project

1. **Start Here**: [PHASE_2_EXECUTIVE_SUMMARY.md](PHASE_2_EXECUTIVE_SUMMARY.md)
   - Project overview and achievements
   - Quick understanding of capabilities

2. **GraphRAG Concepts**: [NEO4J_GRAPHRAG_LEARNINGS.md](docs/NEO4J_GRAPHRAG_LEARNINGS.md)
   - How graph + RAG work together
   - Implementation insights

3. **User Journeys**: [BENUTZER_JOURNEYS_DE.md](docs/BENUTZER_JOURNEYS_DE.md)
   - Real-world usage examples
   - Query patterns for different personas

4. **Technical Deep-Dive**: [PHASE_2_IMPLEMENTATION_SUMMARY.md](PHASE_2_IMPLEMENTATION_SUMMARY.md)
   - Implementation details
   - Code architecture

### Running Your Own GraphRAG

This project serves as a **template** for building domain-specific GraphRAG systems:

**Adapt For Your Domain**:
- Replace legal XML with your data source
- Adjust chunking strategy for your content
- Modify schema for your relationships
- Create user journeys for your users

**Key Patterns to Reuse**:
- Hierarchical document structure
- Chunk-based RAG implementation
- Hybrid retrieval (graph + vector)
- Amendment/version tracking approach
- Automated deployment and validation

---

## 🔗 External Resources

### Data Source
- **German Social Law (SGB)**: [www.gesetze-im-internet.de](https://www.gesetze-im-internet.de/)
- Official government-provided XML files
- Updated regularly with amendments

### Technologies Used
- **Neo4j 5.x**: Graph database
- **Python 3.11+**: Implementation language
- **Azure OpenAI**: Embeddings generation
- **sentence-transformers**: Local embeddings (alternative)
- **lxml**: XML parsing

### Related Documentation
- [Neo4j Documentation](https://neo4j.com/docs/)
- [Cypher Query Language](https://neo4j.com/docs/cypher-manual/)
- [GraphRAG Overview](https://neo4j.com/use-cases/graph-rag/)

---

## 📞 Support

### Documentation
- **Complete Guide**: [docs/DOCUMENTATION_INDEX.md](docs/DOCUMENTATION_INDEX.md)
- **User Journeys**: [docs/BENUTZER_JOURNEYS_DE.md](docs/BENUTZER_JOURNEYS_DE.md)
- **Query Library**: [src/queries/amendment_queries.py](src/queries/amendment_queries.py)

### Testing
```bash
# Validate your installation
python scripts/validate_import.py

# Test specific use case
python scripts/evaluate_sachbearbeiter_use_cases.py
```

### Troubleshooting
- Check [docs/DOCUMENTATION_INDEX.md](docs/DOCUMENTATION_INDEX.md) § Configuration
- Review [PHASE_2_VALIDATION_REPORT.md](PHASE_2_VALIDATION_REPORT.md) for validation patterns
- See [scripts/README.md](scripts/README.md) for script documentation

---

## 📄 License

This project is provided as-is for educational and demonstration purposes.

**Data**: German social law texts are public domain (official government documents)  
**Code**: Available for study and adaptation  
**Use Case**: Demonstration of Neo4j GraphRAG capabilities

---

## 🙏 Acknowledgments

**Data Source**: [www.gesetze-im-internet.de](https://www.gesetze-im-internet.de/) - German Federal Ministry of Justice  
**Technology**: Neo4j Graph Database and Azure OpenAI  
**Purpose**: GraphRAG demonstration and legal knowledge graph research

---

**Version**: 2.4 (Amendment Features Complete)  
**Last Updated**: November 3, 2025  
**Status**: ✅ Production Ready - All 20 use cases validated
