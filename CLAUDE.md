# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

## Project Overview

**Sozialrecht RAG Datenbank** - Comprehensive German Social Law (SGB I-XIV) database with Neo4j RAG system and BPMN process visualization for case workers.

**Purpose**: RAG-based legal information system for German social security law with:
- 50 legal documents (laws + administrative guidelines)
- Neo4j graph database integration
- BPMN 2.0 process visualization for caseworkers
- Source trustworthiness tracking (70-100%)
- Hybrid strategy (Law for amounts + Guidelines for procedures)

---

## Core Architecture

### 1. Data Layer (Content)
**Location**: `Gesetze/`, `Fachliche_Weisungen/`, `Rundschreiben_BMAS/`

- **13 Laws (SGB I-XIV)**: Official legal texts from gesetze-im-internet.de (100% trust)
- **34 Administrative Guidelines**: From Bundesagentur für Arbeit (95% trust) + Harald Thomé (85% trust)
- **1 BMAS Circular**: From Tacheles proxy (85% trust)

**Critical**: PDFs remain in Git (~30 MB). Source metadata tracked in `Metadaten/QUELLEN_BEWERTUNG_UND_AKTUALITAET.md`.

### 2. Neo4j RAG System
**Core**: `src/sozialrecht_neo4j_rag.py`

**Graph Schema**:
```
(Document {sgb, type, trust_score, source_url, stand_datum})
  ├─[:HAS_CHUNK]→ (Chunk {text, embedding[768], paragraph_nummer})
  └─[:CONTAINS_PARAGRAPH]→ (Paragraph {nummer, sgb, content})
```

**Key Features**:
- German embeddings: `paraphrase-multilingual-mpnet-base-v2`
- Paragraph-aware chunking: 800 chars + 100 overlap
- Source hierarchy: Law > BA Guidelines > BMAS > Harald Thomé > Expert Associations
- Hybrid strategy: Automatically uses Law for amounts/dates, Guidelines for procedures

### 3. Document Processing
**Core**: `src/sozialrecht_docling_loader.py`

**Metadata Extraction** (from filename/path):
- SGB number (I-XIV from `SGB_XX_*.pdf`)
- Document type (Gesetz, BA_Weisung, Harald_Thome, BMAS_Rundschreiben)
- Paragraph number (from `Par_XX_` pattern)
- Date (from `YYYY-MM-DD` or `DD.MM.YYYY` patterns)
- Source URL (mapped by document type)

### 4. BPMN Process System
**Core**: `src/bpmn_prozess_generator.py`, `src/neo4j_prozess_integration.py`

**Process-Document Integration**:
```cypher
(:ProcessTemplate)-[:HAS_STEP]->(:ProcessStep)
  ├─[:RECHTLICHE_GRUNDLAGE]→ (:Document {type:'Gesetz'})
  ├─[:HANDLUNGSEMPFEHLUNG]→ (:Document {type:'BA_Weisung'})
  └─[:VERWEIST_AUF]→ (:Paragraph)

(:CaseInstance)-[:BASED_ON]→(:ProcessTemplate)
  └─[:HAD_DECISION]→(:Decision)
```

**4 Pre-built Templates** in `processes/`:
- SGB II Antragstellung (most complex)
- SGB II Sanktionsverfahren
- SGB XII Grundsicherung im Alter
- SGB III Arbeitsvermittlung

---

## Common Commands

### Neo4j Operations

```bash
# Start Neo4j
docker-compose up -d

# Check status
docker ps | grep sozialrecht-neo4j

# Stop Neo4j
docker-compose down

# Reset database (delete all data)
docker-compose down -v
```

### Data Upload

```bash
# Activate virtual environment
source venv/bin/activate

# Upload all PDFs to Neo4j
python scripts/upload_sozialrecht_to_neo4j.py

# Dry-run (see what would be uploaded)
python scripts/upload_sozialrecht_to_neo4j.py --dry-run

# Upload specific categories only
python scripts/upload_sozialrecht_to_neo4j.py --categories Gesetze
python scripts/upload_sozialrecht_to_neo4j.py --categories Fachliche_Weisungen

# Limit uploads for testing
python scripts/upload_sozialrecht_to_neo4j.py --limit 5
```

### BPMN Generation

```bash
# Generate all 4 process templates
python src/bpmn_prozess_generator.py

# Output:
# - processes/*.bpmn (BPMN 2.0 XML for Camunda/Signavio)
# - processes/*.mmd (Mermaid diagrams for Markdown)
```

### Process-Document Integration

```bash
# Create process with document links in Neo4j
python src/neo4j_prozess_integration.py

# This creates:
# - ProcessTemplate nodes
# - ProcessStep nodes linked to Documents/Paragraphs
# - Example CaseInstance for demonstration
```

---

## Critical Design Decisions

### 1. Hybrid Strategy (BA Update Policy)

**Problem**: Bundesagentur does NOT update guidelines when only amounts change (e.g., Regelbedarfe 2024/2025).

**Solution**:
- **Law (Gesetz)** for amounts/dates → Always current
- **Guideline (Weisung)** for procedures → Explains HOW to apply

**Implementation**: `SozialrechtNeo4jRAG.get_hybrid_answer()` automatically detects amount queries and prioritizes Law.

### 2. Source Trustworthiness Hierarchy

Hardcoded in `SozialrechtNeo4jRAG.SOURCE_TRUST_SCORES`:
```python
'gesetze-im-internet.de': 100,  # Official laws
'arbeitsagentur.de': 95,         # BA guidelines
'bmas.de': 95,                   # BMAS circulars
'harald-thome.de': 85,           # Expert archive (secondary)
'dguv.de': 85,
'bih.de': 80,
'tacheles-sozialhilfe.de': 85
```

### 3. Document Type Priority

For conflict resolution (lower = higher priority):
```python
DOC_TYPE_PRIORITY = {
    'Gesetz': 1,              # Law always wins
    'BA_Weisung': 2,          # Official BA guideline
    'BMAS_Rundschreiben': 3,  # BMAS circular
    'Harald_Thome': 4,        # Expert archive
    'Fachverband': 5          # Expert associations
}
```

### 4. Paragraph-Aware Chunking

**Text Splitter** configured for legal texts:
```python
chunk_size=800,        # Larger for legal context
chunk_overlap=100,     # More overlap for continuity
separators=["\n\n§", "\n\n", "\n", ". ", " "]  # Paragraph-aware
```

**Paragraph Extraction**: Regex `§\s*(\d+[a-z]?(?:\s*Abs\.?\s*\d+)?)` extracts references like "§ 20", "§ 11a", "§ 8 Abs. 2".

---

## Data Organization

### Metadata Tracking

**Essential files**:
- `Metadaten/QUELLEN_BEWERTUNG_UND_AKTUALITAET.md` - Source trust scores (96% weighted average)
- `Metadaten/KRITISCHE_BEFUNDE.md` - BA update policy explained
- `⚠️_KRITISCHE_WARNUNG_2025_ÄNDERUNGEN.md` - **CRITICAL**: SGB II becomes "Neue Grundsicherung" July 2026

### Known Issues

**Outdated Documents** (see `QUELLEN_BEWERTUNG`):
- SGB II § 19, 20: Latest available is Nov 2023 (BA hasn't updated despite amount changes)
  → Solution: Hybrid strategy implemented
- SGB V, VII: 2021 documents (4 years old) → Use with disclaimer
- BMAS Rundschreiben: Only 1/7 available (download issues)

**Highly Current** (2024-2025):
- SGB II Thomé Folien (20.09.2025) - Most current analysis
- SGB II § 16 (26.03.2025) - Latest
- SGB II § 11-11b (24.10.2024)
- SGB VI RV Ersatz (09.04.2024)

---

## Neo4j Schema Extensions

### For Process Integration

When adding process-document links, use:
```cypher
MATCH (ps:ProcessStep {id: $step_id})
MATCH (d:Document {sgb_nummer: $sgb, document_type: 'Gesetz'})
MERGE (ps)-[:RECHTLICHE_GRUNDLAGE {priority: 1}]->(d)

MATCH (ps)-[:HANDLUNGSEMPFEHLUNG {priority: 2}]->(:Document {type: 'BA_Weisung'})
MATCH (ps)-[:VERWEIST_AUF]->(:Paragraph)
```

### Query Patterns

**Get recommendations for process step**:
```python
# Returns Law + Guidelines + Paragraph text for specific step
recommendations = prozess_integration.get_current_step_recommendations(step_id)
```

**Hybrid search with source ranking**:
```python
# Automatically boosts Law documents for amount queries
results = rag.hybrid_search_with_source_ranking(query, prefer_gesetz=True)
```

---

## Important Constraints

1. **Temporal Validity**: SGB II undergoes complete restructuring July 2026 ("Neue Grundsicherung"). Monitor November 2025 draft legislation.

2. **Source Hierarchy**: Always prefer Law > BA Guidelines > BMAS > Expert sources when conflicts arise.

3. **Disclaimer Required**: All RAG outputs MUST include source citation with trust score and stand date. No legal advice.

4. **PDF Retention**: PDFs stay in Git (design decision - not separated into content repo despite 30 MB size).

---

## Development Workflow

### Adding New Documents

1. Place PDF in appropriate directory (Gesetze/, Fachliche_Weisungen/SGB_X/, etc.)
2. Follow naming convention: `SGB_XX_Title.pdf` or `FW_SGB_XX_Par_YY_Title.pdf`
3. Include stand date in filename if available: `_YYYY_MM_DD.pdf` or `_DD.MM.YYYY.pdf`
4. Run upload script to add to Neo4j
5. Update `Metadaten/QUELLEN_BEWERTUNG_UND_AKTUALITAET.md` if from new source

### Extending BPMN Processes

1. Use `BPMNElementType` enum for element types
2. Add tasks with `add_user_task()` - include `sgb_ref` for document linking
3. Use `add_exclusive_gateway()` for decisions (XOR)
4. Use `add_parallel_gateway()` for concurrent tasks (AND)
5. Export both XML (`.bpmn`) and Mermaid (`.mmd`)

### Modifying Graph Schema

When adding new node types or relationships:
1. Update `_initialize_sozialrecht_schema()` in `sozialrecht_neo4j_rag.py`
2. Add constraints for unique IDs: `CREATE CONSTRAINT IF NOT EXISTS FOR (n:NodeType) REQUIRE n.id IS UNIQUE`
3. Add indexes for frequent queries
4. Document in `NEO4J_SETUP.md`

---

## Testing Queries

**Neo4j Browser** (http://localhost:7474):

```cypher
// Quick stats
MATCH (d:Document)
OPTIONAL MATCH (d)-[:HAS_CHUNK]->(c:Chunk)
RETURN COUNT(DISTINCT d) as documents, COUNT(c) as chunks

// Find all SGB II documents
MATCH (d:Document {sgb_nummer: "II"})
RETURN d.filename, d.document_type, d.trust_score
ORDER BY d.type_priority

// Search paragraph § 20 across all document types
MATCH (d)-[:CONTAINS_PARAGRAPH]->(p:Paragraph {paragraph_nummer: "20"})
RETURN d.document_type, d.filename, d.trust_score, p.content
ORDER BY d.type_priority
```

---

## Project-Specific Knowledge

### Sozialrecht Domain

**SGB Structure** (13 social security books):
- SGB I: General provisions (procedural basics)
- SGB II: Bürgergeld (unemployment benefits) - Most comprehensive collection
- SGB III: Employment promotion
- SGB IV-XIV: Health insurance, pensions, accident insurance, youth welfare, rehabilitation, administration, nursing care, social welfare, social compensation

**Only 9/13 SGBs have administrative guidelines** (Fachliche Weisungen):
- Available: I, II, III, IV, V, VI, VII, IX, X
- Not available: VIII (states), XI (health insurance associations), XII/XIV (BMAS circulars instead)

**Source Types**:
- **Gesetz**: Legal text (highest authority, 100% trust)
- **BA_Weisung**: Bundesagentur für Arbeit administrative guideline (95% trust)
- **BMAS_Rundschreiben**: Federal ministry circular (95% trust)
- **Harald_Thome**: Expert archive (85% trust, secondary source)
- **Fachverband**: Expert associations like BIH, DGUV (80-85% trust)

### Hybrid Strategy Rationale

BA policy: Guidelines updated ONLY for systematic changes, NOT for amount adjustments (Regelbedarfe).

**Example**: § 20 SGB II (standard needs):
- Law states: 563€ for single persons (2025)
- Latest guideline: Nov 2023 (explains procedure, not amounts)
- Solution: Extract amounts from Law, procedures from Guideline

This is implemented in `get_hybrid_answer()` which auto-detects amount queries via keywords: 'regelbedarf', 'betrag', 'höhe', 'euro', '€', 'frist', etc.

---

## Critical Warnings

⚠️ **SGB II Complete Restructuring**: "Neue Grundsicherung" planned for July 2026
- Draft legislation expected: November 2025
- All SGB II guidelines will become obsolete
- Monitoring required: Harald Thomé Newsletter 30/2025+

⚠️ **Outdated Documents Identified**:
- SGB VI (2017) → Updated to April 2024 ✅
- SGB II § 19, 20 (2023) → Latest available, use Hybrid strategy ✅
- SGB V, VII (2021) → 4 years old, use with caution

See `⚠️_KRITISCHE_WARNUNG_2025_ÄNDERUNGEN.md` for timeline.

---

## Integration Points

### With ms-agentf-neo4j Project

This project **adapts components** from `/Users/ma3u/projects/ms-agentf-neo4j`:
- Docling document loader pattern
- Neo4j RAG base implementation
- Batch upload script structure

**Differences**:
- Specialized for legal texts (German)
- Source trustworthiness tracking
- Paragraph-aware chunking
- BPMN process integration
- Hybrid search strategy

### Docker Integration

Neo4j runs in Docker with:
- Image: `neo4j:community` (2025.09.0)
- Plugins: APOC, Graph Data Science
- Ports: 7474 (HTTP), 7687 (Bolt)
- Memory: 2GB heap, 512MB pagecache

Container name: `sozialrecht-neo4j`

---

## Usage Patterns

### For Caseworkers (Sachbearbeiter)

**Typical workflow**:
1. Open BPMN process (e.g., SGB II Antragstellung)
2. Click on process step (e.g., "Erwerbsfähigkeit prüfen" / § 8)
3. System shows via Neo4j:
   - Law text (SGB II § 8) - 100% trust
   - BA guideline (FW § 8) - 95% trust
   - Top 3 relevant text chunks
   - Full paragraph content
4. Decision documented in (:CaseInstance)-[:HAD_DECISION]→(:Decision)

### For RAG Developers

**Query pattern**:
```python
from src.sozialrecht_neo4j_rag import SozialrechtNeo4jRAG

rag = SozialrechtNeo4jRAG()

# Automatic hybrid search
response = rag.get_hybrid_answer("Was ist der Regelbedarf für Alleinstehende?")

# Returns:
# - Law source (amounts): 563€ from Gesetz
# - Guideline source (procedure): Calculation method from Weisung
# - Trust scores: 100% (Law) + 95% (Guideline)
# - Disclaimer included
```

---

## File Organization

**Source code** (`src/`):
- `sozialrecht_neo4j_rag.py`: Main RAG system
- `sozialrecht_docling_loader.py`: PDF extraction
- `bpmn_prozess_generator.py`: BPMN 2.0 generator
- `neo4j_prozess_integration.py`: Process-document linking

**Scripts** (`scripts/`):
- `upload_sozialrecht_to_neo4j.py`: Batch upload for all PDFs

**Processes** (`processes/`):
- `*.bpmn`: BPMN 2.0 XML (Camunda compatible)
- `*.mmd`: Mermaid diagrams (Markdown compatible)

**Metadata** (`Metadaten/`):
- Source URLs, trust scores, actuality analysis
- **READ FIRST**: `QUELLEN_BEWERTUNG_UND_AKTUALITAET.md`

**Config**:
- `docker-compose.yml`: Neo4j setup
- `requirements.txt`: Python dependencies (note: numpy<2.0.0 for langchain compatibility)

---

## Performance Considerations

**Expected metrics after upload**:
- Documents: 50 nodes
- Chunks: ~1500-2000 nodes
- Paragraphs: ~150-200 nodes
- Upload time: 10-15 minutes
- Query time: <100ms (with caching)
- Vector search: <200ms

**Caching**: Query cache in `_query_cache` with 100 entry limit (FIFO).

---

## When Working With This Codebase

1. **Always check source trust scores** before using documents in RAG outputs
2. **Use Hybrid strategy** for amount/date queries (implemented in `get_hybrid_answer()`)
3. **Include disclaimer** in all legal responses (no legal advice)
4. **Monitor November 2025** for SGB II restructuring draft
5. **Verify Neo4j is running** (`docker ps`) before upload/query operations
6. **Use venv** to avoid system package conflicts

---

**Repository**: https://github.com/ma3u/Sozialrecht_RAG
**Neo4j Browser**: http://localhost:7474 (neo4j/password)
**Documentation**: Start with README.md, then NEO4J_SETUP.md and BPMN_PROZESSE.md
