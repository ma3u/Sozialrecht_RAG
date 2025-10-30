// ===================================================
// Neo4j Schema for XML Legal Data (Phase 2)
// Sozialrecht RAG - XML Schema Extension
// ===================================================

// ==========================================
// CONSTRAINTS
// ==========================================

// Legal Document constraints
CREATE CONSTRAINT legal_document_id IF NOT EXISTS 
FOR (d:LegalDocument) REQUIRE d.id IS UNIQUE;

// Legal Norm constraints
CREATE CONSTRAINT legal_norm_id IF NOT EXISTS 
FOR (n:LegalNorm) REQUIRE n.id IS UNIQUE;

// Structural Unit constraints
CREATE CONSTRAINT structural_unit_id IF NOT EXISTS 
FOR (s:StructuralUnit) REQUIRE s.id IS UNIQUE;

// Text Unit constraints
CREATE CONSTRAINT text_unit_id IF NOT EXISTS 
FOR (t:TextUnit) REQUIRE t.id IS UNIQUE;

// List Item constraints
CREATE CONSTRAINT list_item_id IF NOT EXISTS 
FOR (l:ListItem) REQUIRE l.id IS UNIQUE;

// Amendment constraints
CREATE CONSTRAINT amendment_id IF NOT EXISTS 
FOR (a:Amendment) REQUIRE a.id IS UNIQUE;

// ==========================================
// INDEXES
// ==========================================

// SGB number index (critical for queries)
CREATE INDEX legal_document_sgb IF NOT EXISTS 
FOR (d:LegalDocument) ON (d.sgb_nummer);

// Jurabk index
CREATE INDEX legal_document_jurabk IF NOT EXISTS 
FOR (d:LegalDocument) ON (d.jurabk);

// Doknr index
CREATE INDEX legal_document_doknr IF NOT EXISTS 
FOR (d:LegalDocument) ON (d.doknr);

// Paragraph number index (critical for queries)
CREATE INDEX legal_norm_paragraph IF NOT EXISTS 
FOR (n:LegalNorm) ON (n.paragraph_nummer);

// Enbez index (§ label)
CREATE INDEX legal_norm_enbez IF NOT EXISTS 
FOR (n:LegalNorm) ON (n.enbez);

// Norm doknr index
CREATE INDEX legal_norm_doknr IF NOT EXISTS 
FOR (n:LegalNorm) ON (n.norm_doknr);

// Structural unit level index
CREATE INDEX structural_unit_level IF NOT EXISTS 
FOR (s:StructuralUnit) ON (s.level);

// Structural unit kennzahl index
CREATE INDEX structural_unit_kennzahl IF NOT EXISTS 
FOR (s:StructuralUnit) ON (s.gliederungskennzahl);

// ==========================================
// FULL-TEXT SEARCH INDEXES
// ==========================================

// Full-text search on legal content
CREATE FULLTEXT INDEX legal_content_fulltext IF NOT EXISTS
FOR (n:LegalNorm) ON EACH [n.content_text, n.titel, n.enbez];

// Full-text search on text units
CREATE FULLTEXT INDEX text_unit_fulltext IF NOT EXISTS
FOR (t:TextUnit) ON EACH [t.text];

// ==========================================
// VECTOR INDEXES (for RAG embeddings)
// ==========================================

// Vector index for chunk embeddings (retain existing)
// Note: This assumes embedding dimension of 768 (paraphrase-multilingual-mpnet-base-v2)
CREATE VECTOR INDEX chunk_embeddings IF NOT EXISTS
FOR (c:Chunk) ON (c.embedding)
OPTIONS {indexConfig: {
  `vector.dimensions`: 768,
  `vector.similarity_function`: 'cosine'
}};

// ==========================================
// VERIFICATION QUERIES
// ==========================================

// To verify schema creation, run:
// SHOW CONSTRAINTS;
// SHOW INDEXES;
// CALL db.indexes();
