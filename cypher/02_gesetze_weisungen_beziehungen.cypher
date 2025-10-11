// ========================================
// GESETZE & WEISUNGEN - BEZIEHUNGS-ANALYSEN
// Verknüpft Gesetze mit Fachlichen Weisungen über Paragraphen
// ========================================

// 1. Finde alle Weisungen zu einem Gesetz-Paragraph
// Beispiel: SGB II § 20 (Regelbedarfe)
MATCH (gesetz:Document {sgb_nummer: 'II', document_type: 'Gesetz'})
MATCH (gesetz)-[:CONTAINS_PARAGRAPH]->(p:Paragraph {paragraph_nummer: '20'})
MATCH (weisung:Document)-[:CONTAINS_PARAGRAPH]->(p)
WHERE weisung.document_type IN ['BA_Weisung', 'Harald_Thome', 'BMAS_Rundschreiben']
WITH p, gesetz, weisung
ORDER BY weisung.trust_score DESC
RETURN
  p.paragraph_nummer as Paragraph,
  gesetz.filename as Gesetz,
  COLLECT({
    typ: weisung.document_type,
    datei: weisung.filename,
    trust: weisung.trust_score,
    stand: weisung.stand_datum
  }) as Weisungen
;

// 2. Hybrid-Strategie Analyse
// Zeigt Gesetz + Weisung Paare für Paragraphen
MATCH (p:Paragraph)
WHERE p.paragraph_nummer IN ['19', '20', '21']  // Wichtige SGB II Paragraphen
MATCH (gesetz:Document {document_type: 'Gesetz'})-[:CONTAINS_PARAGRAPH]->(p)
OPTIONAL MATCH (weisung:Document)-[:CONTAINS_PARAGRAPH]->(p)
WHERE weisung.document_type = 'BA_Weisung'
RETURN
  p.sgb_nummer as SGB,
  p.paragraph_nummer as Paragraph,
  gesetz.filename as Gesetz_Datei,
  gesetz.trust_score as Gesetz_Trust,
  weisung.filename as Weisung_Datei,
  weisung.trust_score as Weisung_Trust,
  weisung.stand_datum as Weisung_Stand
ORDER BY p.sgb_nummer, p.paragraph_nummer
;

// 3. Fehlende Weisungen identifizieren
// Paragraphen die NUR im Gesetz, aber KEINE Weisung haben
MATCH (gesetz:Document {sgb_nummer: 'II', document_type: 'Gesetz'})-[:CONTAINS_PARAGRAPH]->(p:Paragraph)
WHERE NOT EXISTS {
  MATCH (weisung:Document {document_type: 'BA_Weisung'})-[:CONTAINS_PARAGRAPH]->(p)
}
RETURN
  p.paragraph_nummer as Paragraph_ohne_Weisung,
  SUBSTRING(p.content, 0, 100) as Inhalt_Vorschau
ORDER BY p.paragraph_nummer
LIMIT 20
;

// 4. Quellen-Hierarchie für Paragraph
// Alle verfügbaren Quellen für einen Paragraph (sortiert nach Priorität)
MATCH (d:Document)-[:CONTAINS_PARAGRAPH]->(p:Paragraph {sgb_nummer: 'II', paragraph_nummer: '11'})
RETURN
  d.document_type as Typ,
  d.filename as Datei,
  d.trust_score as Trust,
  d.type_priority as Priorität,
  d.stand_datum as Stand,
  SUBSTRING(p.content, 0, 200) as Inhalt
ORDER BY d.type_priority ASC, d.trust_score DESC
;

// 5. Chunk-Qualität Analyse
// Zeigt Chunks mit Paragraph-Kontext
MATCH (d:Document {sgb_nummer: 'II'})-[:HAS_CHUNK]->(c:Chunk)
WHERE c.paragraph_nummer IS NOT NULL
RETURN
  d.document_type as Dokumenttyp,
  c.paragraph_nummer as Paragraph,
  COUNT(c) as Anzahl_Chunks,
  AVG(LENGTH(c.text)) as Durchschnitt_Länge,
  COLLECT(c.paragraph_context)[0] as Beispiel_Kontext
ORDER BY Anzahl_Chunks DESC
LIMIT 15
;

// 6. Cross-SGB Paragraph-Verweise
// Findet Paragraphen die in mehreren SGBs existieren (z.B. § 8 in SGB I, II, III)
MATCH (p:Paragraph)
WITH p.paragraph_nummer as para_num, COLLECT(DISTINCT p.sgb_nummer) as sgbs
WHERE SIZE(sgbs) > 1
RETURN
  para_num as Paragraph,
  sgbs as SGBs_mit_diesem_Paragraph,
  SIZE(sgbs) as Anzahl_SGBs
ORDER BY Anzahl_SGBs DESC, para_num
;

// 7. Vertrauenswürdigkeit vs. Aktualität
// Trade-off Analyse: Hoher Trust vs. Aktuelles Datum
MATCH (d:Document)
WHERE d.stand_datum IS NOT NULL
WITH d,
     CASE
       WHEN d.stand_datum >= '2024-01-01' THEN 'Sehr aktuell (2024-2025)'
       WHEN d.stand_datum >= '2023-01-01' THEN 'Aktuell (2023)'
       WHEN d.stand_datum >= '2021-01-01' THEN 'Älter (2021-2022)'
       ELSE 'Veraltet (vor 2021)'
     END as Aktualität
RETURN
  Aktualität,
  AVG(d.trust_score) as Durchschnitt_Trust,
  COUNT(d) as Anzahl,
  COLLECT(d.filename)[0..3] as Beispiele
ORDER BY Aktualität
;

// 8. Vollständigkeits-Check: SGB mit Gesetz UND Weisung
// Zeigt welche SGBs sowohl Gesetz als auch Weisungen haben
MATCH (gesetz:Document {document_type: 'Gesetz'})
OPTIONAL MATCH (weisung:Document {sgb_nummer: gesetz.sgb_nummer})
WHERE weisung.document_type IN ['BA_Weisung', 'Harald_Thome']
RETURN
  gesetz.sgb_nummer as SGB,
  gesetz.filename as Gesetz,
  COUNT(DISTINCT weisung) as Anzahl_Weisungen,
  CASE
    WHEN COUNT(weisung) > 0 THEN '✅ Vollständig'
    ELSE '⚠️ Nur Gesetz'
  END as Status
ORDER BY Anzahl_Weisungen DESC
;
