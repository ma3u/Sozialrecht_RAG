# Maintenance Scripts

This directory contains one-time repair and maintenance scripts that are not part of regular operations.

## Data Repair Scripts

### Orphaned Node Linking
- **link_orphaned_norms.py** - Link disconnected legal norms to documents
- **link_orphaned_chunks.py** - Link disconnected chunks to norms
- **analyze_remaining_orphans.py** - Analyze unlinked nodes
- **link_all_norms_to_documents.py** - Bulk linking of norms to documents
- **analyze_chunk_linking.py** - Analyze chunk linkage patterns

### Coverage Fixes
- **fix_sgb_coverage.py** - Fix missing SGB coverage
- **repair_and_chunk_all_sgbs.py** - Repair and re-chunk all SGBs

### SGB X Specific Imports
- **import_sgb_x_from_json.py** - Import SGB X from JSON format
- **import_sgb_x_missing_paragraphs.py** - Add missing SGB X paragraphs
- **parse_sgb_x_xml.py** - Parse SGB X XML files

### Embedding Management
- **regenerate_embeddings_production.py** - Regenerate embeddings for production
- **generate_additional_chunks.py** - Generate additional text chunks

## When to Use These Scripts

### Routine Maintenance
These scripts should generally NOT be needed in regular operations. They were created to:
1. Fix specific data issues during initial import
2. Repair graph relationships after schema changes
3. Handle edge cases in data processing

### When Repairs Are Needed
Run these scripts only when:
- You detect orphaned nodes (use `analyze_graph_schema.py` to check)
- Coverage analysis shows missing data
- After major schema changes
- When re-importing specific SGBs

## Usage Warnings

⚠️ **Before running any maintenance script:**
1. Backup your Neo4j database
2. Test on a development instance first
3. Review the script code to understand what it does
4. Check for recent updates in the main documentation

⚠️ **These scripts may:**
- Modify existing graph relationships
- Create new nodes and edges
- Take significant time to complete (10-60 minutes)
- Require substantial memory

## Recommended Workflow

1. **Diagnose first**: Use analysis scripts to identify issues
   ```bash
   python scripts/analyze_graph_schema.py
   python scripts/graphrag_status.py
   ```

2. **Check if repair is needed**: Compare stats with expected values in README.md

3. **Backup database**: Create Neo4j backup before running repairs

4. **Run specific repair**: Only run the script that addresses your specific issue

5. **Verify results**: Re-run analysis scripts to confirm fix

## Active Production Scripts

For regular operations, use scripts in the parent `scripts/` directory:
- `evaluate_sachbearbeiter_use_cases.py`
- `complete_knowledge_graph_import.py`
- `setup_neo4j_indexes.py`
- `generate_embeddings.py`

See `scripts/README.md` for complete documentation.
