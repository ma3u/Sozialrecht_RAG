# Scripts Directory

Scripts for managing the Sozialrecht RAG knowledge graph in Neo4j.

## 📁 Script Organization

### 🔧 Active Production Scripts

#### Evaluation & Testing
- **`evaluate_sachbearbeiter_use_cases.py`** - Validates all 20 real-world use cases for case workers
  - Tests: SGB II (Grundsicherung), Cross-SGB queries, workflow scenarios
  - Status: ✅ All 20 tests passing (100% success rate)

#### Neo4j Database Management
- **`setup_neo4j_indexes.py`** - Creates necessary indexes and constraints
- **`generate_embeddings.py`** - Generates vector embeddings for semantic search
- **`fix_vector_index.py`** - Repairs vector index if corrupted

#### Data Import & Processing
- **`complete_knowledge_graph_import.py`** - Full knowledge graph import from XML/JSON
- **`upload_sozialrecht_to_neo4j.py`** - Initial data upload script

#### Dashboard & Monitoring
- **`dashboard.py`** - Flask dashboard for graph visualization and monitoring

#### Analysis & Debugging
- **`analyze_graph_schema.py`** - Analyzes Neo4j graph schema
- **`analyze_graph_relationships.py`** - Detailed relationship analysis
- **`graphrag_query.py`** - Query interface for GraphRAG
- **`graphrag_status.py`** - Check GraphRAG setup status

### 🗄️ Archive / Specialized Scripts

#### Data Repair (Run as needed)
- **`fix_sgb_coverage.py`** - Fixes missing SGB coverage
- **`link_orphaned_norms.py`** - Links orphaned legal norms
- **`analyze_remaining_orphans.py`** - Analyzes unlinked norms
- **`import_sgb_x_from_json.py`** - Import SGB X from JSON
- **`import_sgb_x_missing_paragraphs.py`** - Add missing SGB X paragraphs
- **`parse_sgb_x_xml.py`** - Parse SGB X XML files

#### Testing (Superseded by evaluate_sachbearbeiter_use_cases.py)
- `test_uc10_uc14.py` - Legacy: specific use case tests
- `test_graphrag_efficiency.py` - Legacy: GraphRAG performance tests
- `test_vector_search.py` - Legacy: vector search tests
- `validate_and_visualize_use_cases.py` - Legacy: visualization tests

#### One-time Setup (Historical)
- `fix_graphrag_setup.py` - Legacy: initial GraphRAG setup
- `reimport_all_with_graphrag.py` - Legacy: bulk reimport
- `optimize_graph_relations.py` - Legacy: relationship optimization
- `find_doknr_patterns.py` - Legacy: document number analysis

### 🛠️ Utility Scripts
- **`cypher_query.sh`** - Shell script for quick Cypher queries

### 📂 Subdirectories
- `dev/` - Development/experimental scripts
- `maintenance/` - Maintenance utilities

## 🚀 Quick Start

### Initial Setup
```bash
# 1. Setup indexes
python scripts/setup_neo4j_indexes.py

# 2. Import data
python scripts/complete_knowledge_graph_import.py

# 3. Generate embeddings
python scripts/generate_embeddings.py
```

### Testing
```bash
# Run full evaluation (recommended)
python scripts/evaluate_sachbearbeiter_use_cases.py
```

### Monitoring
```bash
# Check GraphRAG status
python scripts/graphrag_status.py

# Analyze schema
python scripts/analyze_graph_schema.py

# Start dashboard
python scripts/dashboard.py
```

## 📊 Current Status

- **Knowledge Graph**: ✅ Fully populated
- **Vector Embeddings**: ✅ Generated
- **Indexes**: ✅ Optimized
- **Use Cases**: ✅ 20/20 passing (100%)
- **Performance**: ⚡ Average query time: 4.32ms

## 🔮 Recommended Workflow

1. **For new features**: Use `evaluate_sachbearbeiter_use_cases.py` as template
2. **For data issues**: Run relevant repair scripts (link_orphaned_norms, fix_sgb_coverage)
3. **For monitoring**: Use `dashboard.py` or `graphrag_status.py`
4. **For debugging**: Use `analyze_graph_*.py` scripts

## 🗑️ Deprecated Scripts

Consider removing these after verification:
- `test_uc10_uc14.py` (replaced by comprehensive evaluator)
- `test_graphrag_efficiency.py` (functionality in evaluator)
- `validate_and_visualize_use_cases.py` (replaced by evaluator)

## 📝 Notes

- All scripts require Neo4j connection (set environment variables or use config)
- Vector search requires OpenAI API key for embeddings
- Run evaluation script after any schema changes
