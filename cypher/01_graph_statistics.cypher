// ========================================
// SOZIALRECHT GRAPH - STATISTIKEN
// ========================================

// 1. Gesamt-Übersicht
// Zeigt Anzahl Dokumente, Chunks, Paragraphen
MATCH (d:Document)
OPTIONAL MATCH (d)-[:HAS_CHUNK]->(c:Chunk)
OPTIONAL MATCH (d)-[:CONTAINS_PARAGRAPH]->(p:Paragraph)
RETURN
  COUNT(DISTINCT d) as Dokumente,
  COUNT(DISTINCT c) as Chunks,
  COUNT(DISTINCT p) as Paragraphen,
  AVG(SIZE(c.embedding)) as Embedding_Dimension
;

// 2. Dokumente pro SGB
// Übersicht welche SGBs wie viele Dokumente haben
MATCH (d:Document)
RETURN
  d.sgb_nummer as SGB,
  COUNT(d) as Anzahl_Dokumente,
  COLLECT(DISTINCT d.document_type) as Dokumenttypen
ORDER BY SGB
;

// 3. Chunks pro SGB (Detailliert)
// Zeigt Chunk-Verteilung über SGBs
MATCH (d:Document)-[:HAS_CHUNK]->(c:Chunk)
WITH d.sgb_nummer as SGB,
     d.document_type as Typ,
     c,
     SIZE(c.text) as text_länge
RETURN
  SGB,
  Typ,
  COUNT(c) as Anzahl_Chunks,
  AVG(text_länge) as Durchschnitt_Chunk_Länge
ORDER BY Anzahl_Chunks DESC
;

// 4. Vertrauenswürdigkeit pro Quelle
// Analysiert Trust-Scores nach Quelle
MATCH (d:Document)
RETURN
  d.source_domain as Quelle,
  AVG(d.trust_score) as Durchschnitt_Trust,
  MIN(d.trust_score) as Min_Trust,
  MAX(d.trust_score) as Max_Trust,
  COUNT(d) as Anzahl_Dokumente
ORDER BY Durchschnitt_Trust DESC
;

// 5. Paragraph-Abdeckung pro SGB
// Zeigt welche Paragraphen in welchen SGBs vorhanden sind
MATCH (p:Paragraph)
RETURN
  p.sgb_nummer as SGB,
  COUNT(DISTINCT p) as Anzahl_Paragraphen,
  COLLECT(DISTINCT p.paragraph_nummer)[0..10] as Beispiel_Paragraphen
ORDER BY Anzahl_Paragraphen DESC
;

// 6. Dokument-Typ Verteilung
// Analyse der Dokumenttypen (Gesetz, Weisung, etc.)
MATCH (d:Document)
RETURN
  d.document_type as Dokumenttyp,
  COUNT(d) as Anzahl,
  AVG(d.trust_score) as Durchschnitt_Trust,
  SUM(d.chunk_count) as Gesamt_Chunks
ORDER BY Anzahl DESC
;

// 7. Aktualität Check
// Zeigt Stand-Datum der Dokumente
MATCH (d:Document)
WHERE d.stand_datum IS NOT NULL
RETURN
  d.sgb_nummer as SGB,
  d.filename as Datei,
  d.stand_datum as Stand,
  d.document_type as Typ,
  d.trust_score as Trust
ORDER BY d.stand_datum DESC
LIMIT 20
;

// 8. Top 10 größte Dokumente (nach Chunks)
// Zeigt umfangreichste Dokumente
MATCH (d:Document)-[:HAS_CHUNK]->(c:Chunk)
RETURN
  d.filename as Datei,
  d.sgb_nummer as SGB,
  COUNT(c) as Anzahl_Chunks,
  d.trust_score as Trust,
  d.stand_datum as Stand
ORDER BY Anzahl_Chunks DESC
LIMIT 10
;
