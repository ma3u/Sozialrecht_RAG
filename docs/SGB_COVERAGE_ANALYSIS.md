# SGB Coverage Analysis for Case Work

**Report Date:** 2025-01-XX  
**Neo4j Database:** Sozialrecht RAG Knowledge Graph

---

## Executive Summary

The Neo4j knowledge graph contains **41,747 text chunks** for semantic search and RAG functionality. Currently, **only 7,318 chunks (17.5%) are accessible** through the complete `LegalDocument → CONTAINS_NORM → LegalNorm → HAS_CHUNK → Chunk` path for **SGB II only**.

**Critical Issue:** 2,227 LegalNorm nodes containing 9,604 chunks (23% of total) are **orphaned** - they have no `CONTAINS_NORM` relationship from any LegalDocument, making them inaccessible for case work queries.

**Good News:** All orphaned norms can be automatically linked to their correct SGB documents by matching their `norm_doknr` property. A repair script is available and ready to execute.

---

## Database Statistics

| Metric | Count |
|--------|-------|
| **Total Chunks** | 41,747 |
| **Total LegalNorm nodes** | 4,213 |
| **Connected LegalNorm nodes** | 1,987 (47%) |
| **Orphaned LegalNorm nodes** | 2,227 (53%) |
| **Chunks accessible via SGB II** | 7,318 (17.5%) |
| **Chunks in orphaned norms** | 9,604 (23%) |
| **CONTAINS_NORM relationships** | 1,114 (only to SGB II) |

---

## SGB Coverage Status

### Complete Path Analysis

The ideal path for case work queries is:
```
LegalDocument → CONTAINS_NORM → LegalNorm → HAS_CHUNK → Chunk
```

| SGB | Structures | Norms | Chunks | Complete Path |
|-----|------------|-------|--------|---------------|
| **SGB II** | 21 | 1,073 | 7,318 | ✅ (44 more fixable) |
| **SGB III** | 107 | 300 | **1,168** | ⚠️ **426 orphaned norms** |
| **SGB IV** | 39 | 118 | **588** | ⚠️ **159 orphaned norms** |
| **SGB V** | 80 | 393 | **4,298** | ⚠️ **717 orphaned norms** |
| **SGB VI** | 63 | 284 | **1,768** | ⚠️ **562 orphaned norms** |
| **SGB VII** | 41 | 183 | 0 | ❌ |
| **SGB VIII** | 95 | 297 | **318** | ⚠️ **113 orphaned norms** |
| **SGB IX** | 67 | 317 | 0 | ❌ |
| **SGB X** | 57 | 159 | 0 | ❌ |
| **SGB XI** | 80 | 205 | **928** | ⚠️ **206 orphaned norms** |
| **SGB XII** | 47 | 130 | 0 | ❌ |
| **SGB I** | 21 | 34 | 0 | ❌ |

**Note:** 
- ✅ = Complete path exists and is functional
- ⚠️ = Chunks exist but norms are orphaned (not linked to LegalDocument)
- ❌ = No chunks found (may not be imported yet)
- **Bold numbers** show chunks that exist but are currently inaccessible
- After running the repair script, all ⚠️ entries will become ✅

---

## Implications for Case Work (Sachbearbeiter)

### ✅ **What Works (SGB II only)**
- **Regelbedarfe (§§ 20-28 SGB II)**: Full text chunks available for semantic search
- **Leistungsberechtigung (§ 7 SGB II)**: Can retrieve detailed eligibility criteria
- **Sanktionen (§§ 31-32 SGB II)**: Chunks support RAG-based explanations
- **Einkommen/Vermögen (§§ 11-12 SGB II)**: Income and asset rules are queryable

### ❌ **What Doesn't Work (All other SGBs)**
Without chunks, Sachbearbeiter **cannot**:
- Perform semantic search for relevant legal passages
- Use RAG to retrieve context-sensitive legal text
- Get AI-generated answers grounded in actual law text
- Find similar cases or precedents based on text embeddings

They are limited to:
- Browsing hierarchical structure (chapters, sections)
- Viewing paragraph identifiers (§ numbers)
- No access to actual legal text content via AI

---

## Root Cause Analysis

### Issue 1: Missing `sgb_nummer` on LegalNorm Nodes
- **All 4,213 LegalNorm nodes** have `sgb_nummer = None`
- This property should be inherited or set during import
- Without it, chunks cannot be attributed to an SGB

### Issue 2: Incomplete Chunk-to-Document Linking
- Chunks exist and are linked to LegalNorm nodes (`HAS_CHUNK` relationship exists)
- But LegalNorm nodes are not properly connected back to LegalDocument nodes
- Or the `sgb_nummer` property is not propagated during chunking/ingestion

### Issue 3: Import Pipeline Gap
Possible causes:
1. **XML/PDF parsing** may not extract SGB identifiers correctly
2. **Chunking script** doesn't preserve `sgb_nummer` when creating chunk relationships
3. **Neo4j ingestion** lacks a step to propagate `sgb_nummer` from document to norms to chunks
4. **Data model inconsistency**: Perhaps some norms were imported from a different source without SGB metadata

---

## Recommended Fix Strategy

### Phase 1: Investigate Data Provenance
```cypher
// Check where chunks come from
MATCH (c:Chunk)-[:HAS_CHUNK]-(norm:LegalNorm)
RETURN norm.dokumenttyp, norm.title, count(c) as chunks
ORDER BY chunks DESC LIMIT 20;

// Check if norms have any SGB-related properties
MATCH (norm:LegalNorm)
RETURN keys(norm) as properties LIMIT 5;
```

### Phase 2: Repair `sgb_nummer` Property
Option A: **Backfill from connected documents**
```cypher
// Propagate sgb_nummer from LegalDocument to LegalNorm
MATCH (doc:LegalDocument)-[:CONTAINS_NORM]->(norm:LegalNorm)
WHERE norm.sgb_nummer IS NULL
SET norm.sgb_nummer = doc.sgb_nummer
RETURN count(norm) as updated_norms;
```

Option B: **Parse from norm identifiers**
```cypher
// Extract SGB number from norm.norm_id (e.g., "SGB_II_§_7")
MATCH (norm:LegalNorm)
WHERE norm.sgb_nummer IS NULL AND norm.norm_id CONTAINS 'SGB_'
SET norm.sgb_nummer = split(split(norm.norm_id, '_')[1], '_')[0]
RETURN count(norm) as updated_norms;
```

### Phase 3: Verify Chunk Connectivity
```cypher
// After fix, verify complete paths exist
MATCH path = (doc:LegalDocument)-[:CONTAINS_NORM]->(norm:LegalNorm)-[:HAS_CHUNK]->(c:Chunk)
RETURN doc.sgb_nummer as sgb, 
       count(DISTINCT norm) as norms,
       count(DISTINCT c) as chunks
ORDER BY sgb;
```

### Phase 4: Re-index Vector Embeddings
If chunks were ingested without SGB context:
1. Update chunk metadata to include `sgb_nummer`
2. Optionally re-generate embeddings with SGB context in the text
3. Rebuild vector index for semantic search

---

## Next Steps

1. **Run diagnostic queries** (Phase 1) to understand data structure
2. **Execute backfill script** (Phase 2) to repair missing `sgb_nummer`
3. **Validate chunk connectivity** (Phase 3) for all SGBs
4. **Test semantic search** with example Sachbearbeiter queries
5. **Update documentation** with correct SGB coverage status

---

## Testing Checklist for Each SGB

Once fixed, verify each SGB with:

```cypher
// For SGB X (replace with I, II, III, etc.)
MATCH path = (doc:LegalDocument {sgb_nummer: 'X'})
             -[:CONTAINS_NORM]->(norm:LegalNorm)
             -[:HAS_CHUNK]->(c:Chunk)
RETURN 
  doc.sgb_nummer as sgb,
  count(DISTINCT norm) as norms_with_chunks,
  count(DISTINCT c) as total_chunks,
  CASE 
    WHEN count(DISTINCT c) > 0 THEN '✅ COMPLETE'
    ELSE '❌ BROKEN'
  END as status;
```

Expected result for all SGBs: **✅ COMPLETE** with non-zero chunk counts.

---

## Impact on User Journeys

### Current State
- **Sachbearbeiter** can only fully leverage RAG for SGB II cases
- All other SGB queries fall back to rule-based or incomplete retrieval
- Knowledge graph value proposition is severely limited

### After Fix
- **All SGBs** support semantic search and RAG
- Sachbearbeiter can ask natural language questions across all social law books
- Consistent user experience regardless of SGB
- Full coverage of Regelbedarfe, Leistungen, Sanktionen, etc. across all domains

---

## REPAIR SCRIPT AVAILABLE

A fully automated repair script is ready to fix this issue:

```bash
cd /Users/ma3u/projects/sozialgesetze/Sozialrecht_RAG
source venv/bin/activate

# Step 1: Analyze the problem (read-only)
python scripts/link_orphaned_norms.py --analyze

# Step 2: Execute the repair
python scripts/link_orphaned_norms.py --fix

# Step 3: Verify the fix
python scripts/link_orphaned_norms.py --verify
```

The script will:
1. Match 2,227 orphaned norms to their correct SGB documents using `norm_doknr`
2. Create CONTAINS_NORM relationships
3. Make 9,604 additional chunks (23% of total) accessible for RAG queries

**Expected Results After Fix:**
- SGB II: 7,854 chunks (current 7,318 + 536)
- SGB III: 1,168 chunks (new)
- SGB IV: 588 chunks (new)
- SGB V: 4,298 chunks (new)
- SGB VI: 1,768 chunks (new)
- SGB VIII: 318 chunks (new)
- SGB XI: 928 chunks (new)

**Total accessible chunks: 16,922 (40.5% of database) - up from 7,318 (17.5%)**

---

**Status**: 🔴 **CRITICAL** - Immediate repair required for production readiness  
**Fix Available**: ✅ Automated repair script ready (`scripts/link_orphaned_norms.py`)  
**Owner**: Data Engineering / Neo4j Pipeline Team  
**Priority**: P0 (Blocking case work functionality)
