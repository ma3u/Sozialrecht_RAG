# Extend Neo4j Schema with gesetze-im-internet.de XML Structure

## 🎯 Overview

Extend the Sozialrecht_RAG Neo4j data schema to directly process and store the structured XML format provided by [gesetze-im-internet.de](https://www.gesetze-im-internet.de/), using the [neo4j-graphrag-python SDK](https://github.com/neo4j/neo4j-graphrag-python) for extraction and relation building.

### Current State
- **Existing approach**: PDF-based extraction using Docling
- **Data source**: 50+ PDFs (Laws, Administrative Guidelines, BMAS Circulars)
- **Current schema**: `Document → Chunk → Paragraph` (paragraph-aware but limited structure)
- **Trust scoring**: 70-100% based on domain reliability

### Target State
- **Enhanced approach**: Direct XML processing + PDF fallback
- **Data source**: XML from gesetze-im-internet.de (100% trust score) + existing PDFs
- **Enhanced schema**: Rich hierarchical legal structure preserving XML semantics
- **Improved capabilities**: Precise paragraph-level queries, structural navigation, citation tracking

---

## 📊 XML Structure Analysis

### Available Data Format

**TOC XML**: `https://www.gesetze-im-internet.de/gii-toc.xml`
- Lists all available laws/ordinances
- Each `<item>` contains `<title>` and `<link>` to XML.zip

**Example Law XML**: `https://www.gesetze-im-internet.de/sgb_2/xml.zip`
- Single XML file per law (e.g., `BJNR295500003.xml` for SGB II)
- 362KB uncompressed for SGB II (86 paragraphs)
- Structured with metadata and hierarchical text data

### XML Schema Structure

```xml
<dokumente builddate="YYYYMMDDHHMMSS" doknr="BJNRXXXXXXXXX">
  <!-- Root document node -->
  
  <norm builddate="..." doknr="...">
    <!-- Each norm represents a legal unit (§, chapter, TOC) -->
    
    <metadaten>
      <jurabk>SGB 2</jurabk>  <!-- Short code -->
      <enbez>§ 1</enbez>  <!-- Section number -->
      <titel format="XML">Section title</titel>
      <ausfertigung-datum>2003-12-24</ausfertigung-datum>
      <fundstelle typ="amtlich">
        <periodikum>BGBl I</periodikum>
        <zitstelle>2003, 2954, 2955</zitstelle>
      </fundstelle>
      <gliederungseinheit>
        <gliederungskennzahl>010</gliederungskennzahl>
        <gliederungsbez>Kapitel 1</gliederungsbez>
        <gliederungstitel>Chapter title</gliederungstitel>
      </gliederungseinheit>
      <standangabe checked="ja">
        <standtyp>Neuf|Stand</standtyp>
        <standkommentar>Amendment text</standkommentar>
      </standangabe>
    </metadaten>
    
    <textdaten>
      <text format="XML">
        <!-- Table of Contents -->
        <TOC>
          <Ident Class="S1">Kapitel 1</Ident>
          <Title>Chapter Title</Title>
          <table>...</table>
        </TOC>
        
        <!-- Content -->
        <Content>
          <P>Main text paragraph</P>
          <DL Type="arabic">  <!-- Definition/Enumeration List -->
            <DT>1.</DT>  <!-- Term -->
            <DD><LA>List content</LA></DD>  <!-- Definition -->
          </DL>
          <table>...</table>  <!-- Tables -->
        </Content>
      </text>
      
      <fussnoten>
        <Content><P>Footnote text</P></Content>
      </fussnoten>
    </textdaten>
  </norm>
</dokumente>
```

### Key XML Elements

| Element | Purpose | Example |
|---------|---------|---------|
| `dokumente` | Root container | Document collection |
| `norm` | Legal unit | §, Chapter, TOC |
| `jurabk` | Law abbreviation | "SGB 2", "SGB 12" |
| `enbez` | Section label | "§ 1", "§ 20", "Inhaltsübersicht" |
| `titel` | Title | "Regelbedarf zur Sicherung des Lebensunterhalts" |
| `gliederungseinheit` | Structural unit | Chapter, Section grouping |
| `Content/P` | Paragraph text | Actual legal text |
| `DL/DT/DD` | Lists | Numbered/lettered enumerations |
| `table` | Tables | TOC, structured data |
| `fussnoten` | Footnotes | Additional annotations |

---

## 🏗️ Proposed Neo4j Schema Extension

### Node Types

```cypher
// 1. Legal Document (Root)
(:LegalDocument {
  id: String,                    // SHA256 hash
  doknr: String,                 // BJNR number (e.g., "BJNR295500003")
  builddate: DateTime,           // XML build timestamp
  jurabk: String,                // Law abbreviation (e.g., "SGB 2")
  lange_titel: String,           // Full official title
  sgb_nummer: String,            // Roman numeral (I, II, III, ...)
  ausfertigung_datum: Date,      // Original enactment date
  fundstelle: String,            // Official publication reference
  trust_score: Integer = 100,    // Always 100 for official XML
  source_type: "XML_OFFICIAL",
  xml_source_url: String,        // Download URL
  last_updated: DateTime
})

// 2. Structural Unit (Chapters, Sections, Subsections)
(:StructuralUnit {
  id: String,
  gliederungskennzahl: String,   // Structural ID (e.g., "010")
  gliederungsbez: String,        // Type (e.g., "Kapitel 1", "Abschnitt 1")
  gliederungstitel: String,      // Title
  level: Integer,                // Hierarchy depth (1=Chapter, 2=Section, etc.)
  order_index: Integer           // Position in parent
})

// 3. Legal Norm (§ Paragraphs)
(:LegalNorm {
  id: String,
  norm_doknr: String,            // Unique norm identifier
  enbez: String,                 // § label (e.g., "§ 1", "§ 20")
  paragraph_nummer: String,      // Normalized (e.g., "1", "20", "11a")
  titel: String,                 // Section title
  content_text: String,          // Full text content
  has_footnotes: Boolean,
  order_index: Integer
})

// 4. Text Content Unit (Absätze)
(:TextUnit {
  id: String,
  type: String,                  // "Paragraph", "List", "Table"
  text: String,                  // Actual text content
  absatz_nummer: String,         // (1), (2), (3), etc.
  order_index: Integer
})

// 5. List Item (Enumeration Items)
(:ListItem {
  id: String,
  list_type: String,             // "arabic", "alpha", "roman"
  term: String,                  // DT content (e.g., "1.", "a)")
  definition: String,            // DD/LA content
  order_index: Integer
})

// 6. Amendment History
(:Amendment {
  id: String,
  standtyp: String,              // "Neuf", "Stand"
  standkommentar: String,        // Amendment description
  amendment_date: Date,          // Extracted from text
  bgbl_reference: String         // BGBl citation if present
})

// 7. Chunk (for RAG - retain existing)
(:Chunk {
  text: String,
  embedding: Vector(768),
  chunk_index: Integer,
  paragraph_context: String
})
```

### Relationships

```cypher
// Structural Hierarchy
(LegalDocument)-[:HAS_STRUCTURE]->(StructuralUnit)
(StructuralUnit)-[:PARENT_OF]->(StructuralUnit)      // Nested structures
(StructuralUnit)-[:CONTAINS_NORM]->(LegalNorm)

// Norm Content
(LegalNorm)-[:HAS_CONTENT]->(TextUnit)
(TextUnit)-[:HAS_LIST_ITEM]->(ListItem)
(ListUnit)-[:HAS_NESTED_LIST]->(ListItem)             // Multi-level lists

// Amendments
(LegalNorm)-[:HAS_AMENDMENT]->(Amendment)
(LegalDocument)-[:HAS_GLOBAL_AMENDMENT]->(Amendment)

// RAG Integration (retain existing)
(LegalDocument)-[:HAS_CHUNK]->(Chunk)
(LegalNorm)-[:HAS_CHUNK]->(Chunk)                     // Link chunks to specific norms
(TextUnit)-[:GENERATES_CHUNK]->(Chunk)

// Cross-References (future enhancement)
(LegalNorm)-[:REFERS_TO]->(LegalNorm)                 // § X verweist auf § Y
(LegalNorm)-[:SUPERSEDES]->(LegalNorm)                // Amendment chains
```

### Schema Diagram

```
LegalDocument (SGB II)
  ├─ HAS_STRUCTURE → StructuralUnit (Kapitel 1)
  │    └─ CONTAINS_NORM → LegalNorm (§ 1)
  │         ├─ HAS_CONTENT → TextUnit (Absatz 1)
  │         │    ├─ text: "Die Grundsicherung..."
  │         │    └─ GENERATES_CHUNK → Chunk (embedding)
  │         ├─ HAS_CONTENT → TextUnit (Absatz 2)
  │         │    └─ HAS_LIST_ITEM → ListItem (1., 2., ...)
  │         └─ HAS_AMENDMENT → Amendment (2025-02-24)
  ├─ HAS_STRUCTURE → StructuralUnit (Kapitel 2)
  │    └─ CONTAINS_NORM → LegalNorm (§ 20)
  └─ HAS_CHUNK → Chunk (legacy compatibility)
```

---

## 🛠️ Implementation Plan

### Phase 1: XML Processing Infrastructure (Week 1-2)

**Goal**: Build XML extraction pipeline using neo4j-graphrag-python

#### Tasks

1. **XML Downloader Module** (`src/xml_downloader.py`)
   ```python
   class GIIXMLDownloader:
       """Download and cache XML from gesetze-im-internet.de"""
       
       def download_toc(self) -> List[Dict]:
           """Parse gii-toc.xml and return law catalog"""
       
       def download_law_xml(self, sgb_short_name: str) -> Path:
           """Download and extract XML.zip for specific law"""
       
       def get_sgb_xml_urls(self) -> Dict[str, str]:
           """Map SGB I-XIV to their XML URLs"""
   ```

2. **XML Parser Module** (`src/xml_legal_parser.py`)
   ```python
   from neo4j_graphrag.experimental.pipeline import Pipeline
   from neo4j_graphrag.llm import LLMInterface
   
   class LegalXMLParser:
       """Parse legal XML structure using neo4j-graphrag"""
       
       def parse_dokument(self, xml_path: Path) -> LegalDocument:
           """Extract root document metadata"""
       
       def parse_norms(self, xml_root) -> List[LegalNorm]:
           """Extract all <norm> elements with structure"""
       
       def extract_gliederung(self, metadaten) -> StructuralUnit:
           """Parse <gliederungseinheit> hierarchy"""
       
       def parse_textdaten(self, textdaten) -> List[TextUnit]:
           """Extract <Content><P>, <DL>, <table> elements"""
       
       def extract_amendments(self, standangabe) -> List[Amendment]:
           """Parse amendment history"""
   ```

3. **neo4j-graphrag Integration** (`src/graphrag_legal_extractor.py`)
   ```python
   from neo4j_graphrag.experimental.components import (
       EntityExtractor,
       RelationExtractor,
       KnowledgeGraphBuilder
   )
   
   class LegalKnowledgeGraphBuilder:
       """Use neo4j-graphrag-python to build legal KG"""
       
       def __init__(self, neo4j_driver, llm: LLMInterface):
           self.kg_builder = KnowledgeGraphBuilder(
               driver=neo4j_driver,
               llm=llm
           )
       
       def build_from_xml(self, legal_document: LegalDocument):
           """Convert parsed XML to Neo4j graph"""
           
       def extract_legal_entities(self, text: str) -> List[Entity]:
           """Extract legal concepts (e.g., "Regelbedarf", "Hilfebedürftigkeit")"""
       
       def extract_cross_references(self, norm: LegalNorm) -> List[Relation]:
           """Detect § X references in text"""
   ```

**Deliverables**:
- [ ] XML download and caching working for all SGB I-XIV
- [ ] Complete parsing of SGB II XML structure (test case)
- [ ] neo4j-graphrag pipeline configured for legal domain

---

### Phase 2: Neo4j Schema Migration (Week 3)

**Goal**: Implement new schema alongside existing structure

#### Tasks

1. **Schema Definition** (`cypher/xml_schema.cypher`)
   ```cypher
   // Create constraints
   CREATE CONSTRAINT legal_document_id IF NOT EXISTS 
   FOR (d:LegalDocument) REQUIRE d.id IS UNIQUE;
   
   CREATE CONSTRAINT legal_norm_id IF NOT EXISTS 
   FOR (n:LegalNorm) REQUIRE n.id IS UNIQUE;
   
   // Create indexes
   CREATE INDEX legal_norm_enbez IF NOT EXISTS 
   FOR (n:LegalNorm) ON (n.enbez);
   
   CREATE INDEX legal_document_sgb IF NOT EXISTS 
   FOR (d:LegalDocument) ON (d.sgb_nummer);
   
   // Vector index for chunks (if not exists)
   CREATE VECTOR INDEX chunk_embeddings IF NOT EXISTS
   FOR (c:Chunk) ON (c.embedding)
   OPTIONS {indexConfig: {
     `vector.dimensions`: 768,
     `vector.similarity_function`: 'cosine'
   }};
   ```

2. **Migration Script** (`scripts/migrate_to_xml_schema.py`)
   ```python
   class SchemaM igrator:
       """Migrate existing data to new schema"""
       
       def migrate_existing_documents(self):
           """Link old Document nodes to new LegalDocument"""
       
       def preserve_existing_chunks(self):
           """Maintain chunk → norm relationships"""
       
       def create_compatibility_layer(self):
           """Ensure old queries still work"""
   ```

3. **Backward Compatibility** (`src/compatibility_adapter.py`)
   ```python
   class CompatibilityAdapter:
       """Adapter for existing code to work with new schema"""
       
       def get_document_by_sgb(self, sgb_nummer: str):
           """Works with both old and new schema"""
       
       def search_by_paragraph(self, sgb: str, para: str):
           """Unified interface for old/new data"""
   ```

**Deliverables**:
- [ ] New schema constraints and indexes created
- [ ] Migration script tested with SGB II
- [ ] All existing unit tests pass with compatibility layer

---

### Phase 3: XML Data Ingestion (Week 4-5)

**Goal**: Populate Neo4j with all SGB I-XIV XML data

#### Tasks

1. **Bulk Import Script** (`scripts/import_all_sgb_xml.py`)
   ```python
   class SGBXMLImporter:
       """Batch import all SGB XML files"""
       
       def import_all_sgbs(self):
           """Download and import SGB I-XIV"""
           for sgb in ["I", "II", "III", ..., "XIV"]:
               self.import_sgb(sgb)
       
       def import_sgb(self, sgb_nummer: str):
           """Complete import pipeline for one SGB"""
           xml_path = self.downloader.download_law_xml(f"sgb_{sgb_nummer}")
           legal_doc = self.parser.parse_dokument(xml_path)
           self.kg_builder.build_from_xml(legal_doc)
       
       def generate_chunks_for_rag(self, legal_norm: LegalNorm):
           """Create Chunk nodes with embeddings"""
           # Use existing chunking strategy from sozialrecht_neo4j_rag.py
   ```

2. **Validation Queries** (`cypher/validation_queries.cypher`)
   ```cypher
   // Verify structure completeness
   MATCH (d:LegalDocument {sgb_nummer: "II"})-[:HAS_STRUCTURE]->(s:StructuralUnit)
         -[:CONTAINS_NORM]->(n:LegalNorm)
   RETURN d.jurabk, 
          count(DISTINCT s) as structures,
          count(DISTINCT n) as norms;
   
   // Check § 20 SGB II structure
   MATCH path = (d:LegalDocument {sgb_nummer: "II"})
                -[:HAS_STRUCTURE*]->(:StructuralUnit)
                -[:CONTAINS_NORM]->(n:LegalNorm {paragraph_nummer: "20"})
                -[:HAS_CONTENT]->(t:TextUnit)
   RETURN path LIMIT 1;
   
   // Verify chunk linkage
   MATCH (n:LegalNorm {paragraph_nummer: "20"})-[:HAS_CHUNK]->(c:Chunk)
   RETURN n.enbez, count(c) as chunk_count, size(c.embedding) as embedding_dim;
   ```

3. **Quality Assurance** (`tests/test_xml_import.py`)
   ```python
   def test_sgb_ii_structure():
       """Verify SGB II has correct structure"""
       # Should have 11 Kapitel, 86 Paragraphen
   
   def test_paragraph_20_content():
       """Verify § 20 text matches official source"""
   
   def test_cross_references():
       """Check § X references are extracted"""
   ```

**Deliverables**:
- [ ] All SGB I-XIV imported into Neo4j
- [ ] Validation confirms 100% structure match with XML
- [ ] Chunk embeddings generated for all norms

---

### Phase 4: Enhanced RAG Integration (Week 6)

**Goal**: Leverage structured XML for improved queries

#### Tasks

1. **Structured Query Engine** (`src/xml_aware_rag.py`)
   ```python
   class XMLAwareRAG(SozialrechtNeo4jRAG):
       """Enhanced RAG using XML structure"""
       
       def hybrid_search_with_structure(self, query: str) -> List[Dict]:
           """
           1. Vector search on Chunks
           2. Navigate to parent LegalNorm
           3. Retrieve full structured context (TextUnits, Lists)
           4. Return with hierarchy info (Chapter → Section → §)
           """
       
       def query_by_hierarchy(self, sgb: str, kapitel: int, paragraph: str):
           """Navigate: SGB II → Kapitel 3 → § 20"""
       
       def get_paragraph_with_amendments(self, sgb: str, para: str):
           """Return § text + amendment history"""
       
       def find_related_paragraphs(self, paragraph: str) -> List[str]:
           """Use REFERS_TO relationships"""
   ```

2. **Citation Resolver** (`src/citation_resolver.py`)
   ```python
   class LegalCitationResolver:
       """Extract and resolve legal citations"""
       
       def extract_citations(self, text: str) -> List[Citation]:
           """Parse "§ 20 Abs. 2 SGB II" references"""
       
       def resolve_citation(self, citation: Citation) -> LegalNorm:
           """Find target LegalNorm in graph"""
       
       def build_citation_graph(self):
           """Create REFERS_TO relationships"""
   ```

3. **Advanced Queries** (`cypher/advanced_queries.cypher`)
   ```cypher
   // Query: "Show me all paragraphs about Regelbedarf"
   CALL db.index.fulltext.queryNodes("sozialrecht_fulltext", "Regelbedarf")
   YIELD node as chunk, score
   MATCH (chunk)<-[:HAS_CHUNK]-(norm:LegalNorm)
   MATCH (norm)<-[:CONTAINS_NORM]-(struct:StructuralUnit)
   MATCH (struct)<-[:HAS_STRUCTURE]-(doc:LegalDocument)
   RETURN doc.jurabk, 
          struct.gliederungstitel as chapter,
          norm.enbez as paragraph,
          norm.titel as title,
          score
   ORDER BY score DESC LIMIT 5;
   
   // Query: "What amended § 20 recently?"
   MATCH (n:LegalNorm {paragraph_nummer: "20"})-[:HAS_AMENDMENT]->(a:Amendment)
   WHERE a.amendment_date > date('2024-01-01')
   RETURN n.enbez, a.standkommentar, a.amendment_date
   ORDER BY a.amendment_date DESC;
   ```

**Deliverables**:
- [ ] XMLAwareRAG class with enhanced queries
- [ ] Citation extraction and linking working
- [ ] Example queries demonstrating new capabilities

---

### Phase 5: Testing & Documentation (Week 7)

**Goal**: Comprehensive testing and user documentation

#### Tasks

1. **Integration Tests** (`tests/test_xml_rag_integration.py`)
   - Test complete pipeline from XML → Neo4j → RAG query
   - Verify performance (query latency < 500ms)
   - Validate answer quality vs. PDF-based approach

2. **Documentation** (`docs/XML_SCHEMA_GUIDE.md`)
   - Schema explanation with examples
   - Query cookbook (common use cases)
   - Migration guide for existing users
   - neo4j-graphrag-python usage patterns

3. **Performance Benchmarks** (`scripts/benchmark_xml_rag.py`)
   - Compare XML vs. PDF approach
   - Query performance metrics
   - Memory usage analysis

**Deliverables**:
- [ ] 95%+ test coverage for XML pipeline
- [ ] Complete documentation published
- [ ] Benchmark results showing improvements

---

## 📈 Expected Benefits

### 1. **Improved Accuracy**
- **100% trust score** (official XML vs. 95% for PDF scraping)
- **No OCR errors** (direct structured data)
- **Precise paragraph boundaries** (XML tags vs. heuristic splitting)

### 2. **Enhanced Queries**
```cypher
// Before (PDF-based):
"Find § 20" → Text search in chunks → Ambiguous results

// After (XML-based):
"Find § 20" → Direct LegalNorm lookup → Exact match
              + Full structure (Absätze, Lists)
              + Amendment history
              + Cross-references
```

### 3. **Better Context for RAG**
- **Hierarchy-aware answers**: "§ 20 is in Kapitel 3, Abschnitt 2 (Bürgergeld)"
- **Related sections**: "§ 20 is related to § 19 (Anspruch) and § 21 (Mehrbedarfe)"
- **Amendment tracking**: "§ 20 was last changed on 2024-02-24"

### 4. **Future-Proof Architecture**
- **Automatic updates**: Poll XML build dates, re-import only changed laws
- **Version control**: Track amendment history in graph
- **Cross-law queries**: "Show all SGB references to § 20 SGB II"

---

## 🔄 Backward Compatibility

### Compatibility Layer
```python
# Old code continues to work:
rag = SozialrechtNeo4jRAG()
result = rag.search_by_sgb_and_paragraph("II", "20")

# New code gets enhanced features:
xml_rag = XMLAwareRAG()
result = xml_rag.query_by_hierarchy(sgb="II", kapitel=3, paragraph="20")
```

### Migration Path
1. **Phase 1**: Run both schemas in parallel (LegalDocument + old Document)
2. **Phase 2**: Gradually migrate queries to new schema
3. **Phase 3**: Deprecate old schema (after 6 months)

---

## 📚 Technology Stack

### Core Libraries
- **neo4j-graphrag-python** v0.9.0+: Entity extraction, relation building, KG construction
- **neo4j** v5.25.0: Python driver
- **lxml** v5.3.0: XML parsing
- **sentence-transformers** v3.3.1: Embeddings (retain existing)

### Optional LLM Integration (via neo4j-graphrag)
- **OpenAI GPT-4**: Entity extraction from legal text
- **Local LLM (Ollama)**: For citation resolution (privacy-sensitive deployments)

### Neo4j Setup
- **Neo4j 5.x** with APOC and GDS plugins
- **Vector index** for chunk embeddings
- **Full-text index** for legal text search

---

## 🚀 Success Metrics

### Phase 1-2 (Infrastructure)
- [ ] All 13 SGB XML files downloaded and parsed
- [ ] Neo4j schema created with all node/relationship types
- [ ] Migration script tested on SGB II

### Phase 3-4 (Data & RAG)
- [ ] 100% of SGB I-XIV norms imported (estimated ~1,500 paragraphs)
- [ ] Vector embeddings generated for all chunks
- [ ] Query latency < 500ms for paragraph lookups

### Phase 5 (Quality)
- [ ] Answer accuracy improvement: 15%+ vs. PDF approach
- [ ] Test coverage: 95%+
- [ ] Documentation complete with 10+ query examples

---

## 🔗 References

### Official Sources
- **XML TOC**: https://www.gesetze-im-internet.de/gii-toc.xml
- **SGB II XML**: https://www.gesetze-im-internet.de/sgb_2/xml.zip
- **GII DTD**: http://www.gesetze-im-internet.de/dtd/1.01/gii-norm.dtd

### neo4j-graphrag-python
- **GitHub**: https://github.com/neo4j/neo4j-graphrag-python
- **Docs**: https://neo4j.com/docs/neo4j-graphrag-python/current/
- **Examples**: https://github.com/neo4j/neo4j-graphrag-python/tree/main/examples

### Project Context
- **Current README**: `README.md`
- **Current Schema**: `src/sozialrecht_neo4j_rag.py`
- **WARP Guide**: `WARP.md`

---

## 👥 Contributors & Feedback

**Primary Maintainer**: @ma3u  
**Repository**: https://github.com/ma3u/Sozialrecht_RAG

### Questions for Discussion
1. Should we use LLM-based entity extraction (via neo4j-graphrag) or rule-based?
2. Priority order for SGB import (II first, then I, III, ...)?
3. Hosting: Local Neo4j vs. Aura Professional for production?

### Contributing
See `CONTRIBUTING.md` for development workflow.

---

**Labels**: `enhancement`, `schema`, `neo4j-graphrag`, `xml-processing`  
**Milestone**: v2.0 - Structured Legal Data  
**Estimated Effort**: 7 weeks (1 developer)
