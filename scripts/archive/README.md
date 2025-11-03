# Archived Scripts

This directory contains legacy and deprecated scripts that have been superseded by newer implementations.

## Archived Scripts

### Testing Scripts (Superseded by evaluate_sachbearbeiter_use_cases.py)
- **test_uc10_uc14.py** - Legacy specific use case tests
- **test_graphrag_efficiency.py** - Legacy GraphRAG performance tests
- **test_vector_search.py** - Legacy vector search tests
- **test_embedding_quality.py** - Legacy embedding quality tests
- **validate_and_visualize_use_cases.py** - Legacy visualization tests

### One-time Setup Scripts (Historical)
- **fix_graphrag_setup.py** - Initial GraphRAG setup (completed)
- **reimport_all_with_graphrag.py** - Bulk reimport (completed)
- **optimize_graph_relations.py** - Relationship optimization (completed)
- **find_doknr_patterns.py** - Document number analysis (completed)

## Why These Were Archived

1. **Superseded by Comprehensive Evaluator**: The `evaluate_sachbearbeiter_use_cases.py` script now provides comprehensive testing that includes all functionality from the legacy test scripts.

2. **One-time Operations Completed**: Setup and optimization scripts were needed for initial implementation but are no longer required for regular operations.

3. **Better Alternatives Available**: Newer scripts provide improved functionality, better error handling, and more comprehensive reporting.

## Current Scripts

For current operations, use:
- **evaluate_sachbearbeiter_use_cases.py** - Comprehensive use case testing
- **analyze_graph_schema.py** - Schema analysis
- **graphrag_status.py** - Status checking

See `scripts/README.md` for complete documentation of active scripts.

## Note

These scripts are kept for historical reference and may be useful for understanding the evolution of the system. They should not be used in production.
