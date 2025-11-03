# Scripts Directory

Scripts for managing the Sozialrecht RAG knowledge graph in Neo4j.

## 📁 Script Organization

### 🔧 Active Production Scripts

These scripts are actively maintained and used in regular operations:

#### Evaluation & Testing
- **`evaluate_sachbearbeiter_use_cases.py`** ⭐ - Validates all 20 real-world use cases
  - Status: ✅ 100% passing (20/20 tests), avg 4.32ms
  - Output: `logs/sachbearbeiter_evaluation.json`

#### Data Import & Processing
- **`complete_knowledge_graph_import.py`** ⭐ - Full knowledge graph import
  - Imports all 13 SGBs, PDFs, embeddings, and relationships
  - Duration: ~15 minutes
- **`upload_sozialrecht_to_neo4j.py`** - Legacy data upload script

#### Neo4j Database Management
- **`setup_neo4j_indexes.py`** - Creates indexes and constraints
- **`generate_embeddings.py`** - Generates vector embeddings
- **`generate_embeddings_azure.py`** - Azure OpenAI embeddings
- **`fix_vector_index.py`** - Repairs vector index

#### Analysis & Monitoring
- **`analyze_graph_schema.py`** - Analyzes graph schema
- **`analyze_graph_relationships.py`** - Relationship pattern analysis
- **`graphrag_query.py`** - GraphRAG query interface
- **`graphrag_status.py`** - Status and health checks
- **`verify_sgb_coverage.py`** - Verify SGB data coverage
- **`dashboard.py`** - Flask monitoring dashboard

### 📦 Archived Scripts

Moved to `archive/` - superseded by newer implementations:
- Legacy test scripts (replaced by `evaluate_sachbearbeiter_use_cases.py`)
- One-time setup scripts (historical)
- See `archive/README.md` for details

### 🔧 Maintenance Scripts

Moved to `maintenance/` - run only when repairs are needed:
- Orphaned node linking scripts
- Coverage fix scripts
- SGB-specific import scripts
- See `maintenance/README.md` for details and warnings

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

1. **Development**: Use `evaluate_sachbearbeiter_use_cases.py` for testing
2. **Data Issues**: Check `maintenance/` directory for repair scripts
3. **Monitoring**: Use `graphrag_status.py` or `dashboard.py`
4. **Debugging**: Use `analyze_graph_*.py` scripts
5. **Historical Reference**: Check `archive/` for legacy implementations

## 📝 Notes

- All scripts require Neo4j connection (set environment variables or use config)
- Vector search requires OpenAI API key for embeddings
- Run evaluation script after any schema changes
