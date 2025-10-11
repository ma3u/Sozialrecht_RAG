# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Project Overview

This is Sozialrecht_RAG - a specialized German Social Law RAG system that combines Neo4j graph database, Docling PDF processing, and BPMN workflow visualization to create an intelligent legal information system for German social security law (SGB I-XIV).

### Core Architecture

**Triple-Layer System:**
1. **Document Layer**: 50+ PDFs (Laws, Administrative Guidelines, BMAS Circulars)  
2. **Graph Database Layer**: Neo4j with paragraph-aware chunking and metadata
3. **Process Layer**: BPMN 2.0 workflows for case worker procedures

**Key Features:**
- Hybrid Strategy: Laws for amounts/deadlines + Guidelines for procedures
- Source Trust Scoring (70-100%) with domain-based reliability
- German-optimized embeddings (`paraphrase-multilingual-mpnet-base-v2`)
- Paragraph-aware chunking preserving legal context
- BPMN process templates with document linkage

## Common Development Commands

### Environment Setup
```bash
# Start Neo4j database
docker-compose up -d

# Install dependencies
pip install -r requirements.txt

# Verify Neo4j is healthy
docker-compose ps
# Should show "healthy" status
```

### Data Loading & RAG Operations
```bash
# Upload all documents to Neo4j (main operation)
python scripts/upload_sozialrecht_to_neo4j.py

# Dry run to see what would be processed
python scripts/upload_sozialrecht_to_neo4j.py --dry-run

# Upload specific categories only
python scripts/upload_sozialrecht_to_neo4j.py --categories Gesetze Fachliche_Weisungen

# Limit upload for testing
python scripts/upload_sozialrecht_to_neo4j.py --limit 5
```

### BPMN Process Generation
```bash
# Generate all BPMN process templates
python src/bpmn_prozess_generator.py

# View generated processes
ls -la processes/
# Opens .bpmn files in Camunda Modeler
# Opens .mmd files in Mermaid Live Editor
```

### Neo4j Database Access
```bash
# Access Neo4j Browser
open http://localhost:7474
# Credentials: neo4j / password

# Check database status
docker logs sozialrecht-neo4j
```

### Development & Testing
```bash
# Interactive RAG testing
python -c "
from src.sozialrecht_neo4j_rag import SozialrechtNeo4jRAG
rag = SozialrechtNeo4jRAG()
result = rag.get_hybrid_answer('Was ist der Regelbedarf für Alleinstehende?')
print(result['answer'])
rag.close()
"

# Process integration demo
python src/neo4j_prozess_integration.py
```

## Architecture Details

### Document Processing Pipeline

**Stage 1: PDF Ingestion**
- Docling extracts text with structure preservation
- Automatic metadata extraction from filenames/paths
- SGB number detection (I-XIV → Roman numerals)
- Document type classification (Gesetz, BA_Weisung, BMAS_Rundschreiben, etc.)

**Stage 2: Intelligent Chunking**
- Paragraph-aware splitting (800 chars, 100 overlap)
- Legal separators: `\\n\\n§`, `\\n\\n`, `\\n`, `. `
- Paragraph number extraction via regex: `§\\s*(\\d+[a-z]?)`
- Context preservation for cross-references

**Stage 3: Neo4j Graph Creation**
```
Document → HAS_CHUNK → Chunk (with embeddings)
Document → CONTAINS_PARAGRAPH → Paragraph
ProcessStep → RECHTLICHE_GRUNDLAGE → Document
ProcessStep → HANDLUNGSEMPFEHLUNG → Document
```

### Source Trust Framework

**Primary Sources (95-100%)**:
- `gesetze-im-internet.de`: 100% (BMJ official laws)
- `arbeitsagentur.de`: 95% (BA administrative guidelines) 
- `bmas.de`: 95% (BMAS circulars)

**Secondary Sources (80-85%)**:
- `harald-thome.de`: 85% (Expert legal commentary)
- `bih.de`: 80% (Professional associations)

**Trust Score Usage**:
- Combined scoring: `similarity * 0.6 + trust * 0.25 + type_priority * 0.15`
- Boosts Gesetz documents for amount/deadline queries
- Enables conflict resolution between sources

### Hybrid Search Strategy

**Critical Legal Problem**: BA doesn't update guidelines when amounts change
- **Problem**: Regelbedarfe 2025 = 563€ (law) vs 2023 amounts (guideline)  
- **Solution**: Hybrid queries prioritize law for amounts, guidelines for procedures
- **Implementation**: `prefer_gesetz=True` for betrag/frist queries

### BPMN Process Integration

**Available Templates**:
1. `SGB_II_Antragstellung.bpmn` - Full benefit application workflow
2. `SGB_II_Sanktionsverfahren.bpmn` - Sanctions with legal hearing
3. `SGB_XII_Grundsicherung_Alter.bpmn` - Senior basic security with DRV interface
4. `SGB_III_Arbeitsvermittlung.bpmn` - Job placement with iterative approach

**Process-Document Linking**:
- Each process step links to relevant law paragraphs
- Automatic document recommendations based on legal references
- Case tracking with decision logging

## Development Patterns

### Adding New Documents
```python
# Use the specialized loader
from src.sozialrecht_docling_loader import SozialrechtDoclingLoader
from src.sozialrecht_neo4j_rag import SozialrechtNeo4jRAG

rag = SozialrechtNeo4jRAG()
loader = SozialrechtDoclingLoader(rag)

# Automatic metadata extraction from path/filename
result = loader.load_sozialrecht_pdf(pdf_path)
```

### Implementing Legal Queries
```python
# Hybrid search with source ranking
results = rag.hybrid_search_with_source_ranking(
    query="Regelbedarf Alleinstehende",
    k=5,
    prefer_gesetz=True  # For amounts/deadlines
)

# Specific paragraph lookup
docs = rag.search_by_sgb_and_paragraph("II", "20")
```

### Creating Process Workflows
```python
from src.bpmn_prozess_generator import SozialrechtBPMNGenerator

bpmn = SozialrechtBPMNGenerator()
start = bpmn.add_start_event("Antrag eingegangen")
task = bpmn.add_user_task("Antrag prüfen", sgb_ref="SGB II § 37")
bpmn.add_sequence_flow(start, task)

xml_output = bpmn.generate_bpmn_xml()
mermaid_output = bpmn.generate_mermaid()
```

## Critical Implementation Notes

### Neo4j Schema Requirements
- Document.id must be unique (SHA256 hash)
- Paragraph.id follows pattern: `{sgb}_{paragraph_num}`
- Embedding vectors are 768-dimensional floats
- Full-text search index required: `sozialrecht_fulltext`

### German Language Optimization
- Embedding model: `paraphrase-multilingual-mpnet-base-v2`
- Legal text chunking preserves paragraph boundaries
- Regex patterns handle German legal citations: `§ 20 Abs. 1 SGB II`

### Docker & Dependencies
- Neo4j Community with APOC and GDS plugins
- Python dependencies include: `docling==2.14.0`, `neo4j==5.25.0`, `sentence-transformers==3.3.1`
- Memory settings: 2GB heap, 512MB pagecache for decent performance

### Data Currency Warning
- SGB II undergoes major reform July 2026 ("Neue Grundsicherung")
- All SGB II guidelines will become obsolete
- Hybrid strategy mitigates current guideline staleness

## File Structure Navigation

**Core Modules**:
- `src/sozialrecht_neo4j_rag.py` - Main RAG system with hybrid search
- `src/sozialrecht_docling_loader.py` - PDF processing with legal metadata extraction
- `src/bpmn_prozess_generator.py` - BPMN 2.0 process creation
- `src/neo4j_prozess_integration.py` - Process-document linking

**Data Directories**:
- `Gesetze/` - 13 SGB laws (9.5 MB, 100% coverage)
- `Fachliche_Weisungen/` - BA administrative guidelines by SGB
- `Rundschreiben_BMAS/` - BMAS ministry circulars
- `processes/` - Generated BPMN files

**Key Scripts**:
- `scripts/upload_sozialrecht_to_neo4j.py` - Main data ingestion pipeline
- `docker-compose.yml` - Neo4j with required plugins and memory config

## Neo4j Query Examples

### Find All Documents for SGB II
```cypher
MATCH (d:Document {sgb_nummer: "II"})
RETURN d.filename, d.document_type, d.trust_score, d.stand_datum
ORDER BY d.type_priority ASC, d.trust_score DESC
```

### Get Paragraph § 20 from All Sources
```cypher
MATCH (d:Document {sgb_nummer: "II"})-[:CONTAINS_PARAGRAPH]->(p:Paragraph {paragraph_nummer: "20"})
RETURN d.document_type, d.filename, d.trust_score, p.content
ORDER BY d.type_priority ASC
```

### Vector Search with Trust Scoring
```cypher
MATCH (d:Document)-[:HAS_CHUNK]->(c:Chunk)
WITH d, c, gds.similarity.cosine(c.embedding, $query_embedding) as similarity
WHERE similarity > 0.7
RETURN c.text, d.filename, d.trust_score, similarity
ORDER BY (similarity * 0.6 + d.trust_score/100 * 0.4) DESC
LIMIT 5
```

## Production Considerations

### Monitoring & Updates
- Weekly BA website monitoring for new guidelines
- Monthly RSS feed checks for law changes
- November 2025: Critical analysis of "Neue Grundsicherung" draft
- July 2026: Complete SGB II system replacement required

### Performance Optimization
- Chunk batch processing (ThreadPoolExecutor for embeddings)
- Query result caching with thread-safe locks
- Connection pooling: max 10 connections, 30s timeout

### Legal Compliance
- All sources properly attributed with trust scores
- Disclaimer required: "Keine Rechtsberatung - bei Rechtsfragen Behörde konsultieren"
- Document URLs tracked for audit trails
- GDPR compliance for case tracking data

<citations>
<document>
<document_type>RULE</document_type>
<document_id>4XaGNkxmJEk2CuNjVBixpD</document_id>
</document>
<document>
<document_type>RULE</document_type>
<document_id>jYQJvThg9PyaUPB1pqNGDW</document_id>
</document>
</citations>