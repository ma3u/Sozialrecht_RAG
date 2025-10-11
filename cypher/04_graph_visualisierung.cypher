// ========================================
// GRAPH VISUALISIERUNGEN
// Cypher Queries für Neo4j Browser Graph-Ansicht
// ========================================

// 1. SGB II Gesetz-Weisungen Netzwerk
// Zeigt wie Gesetze und Weisungen über Paragraphen verbunden sind
MATCH path = (gesetz:Document {sgb_nummer: 'II', document_type: 'Gesetz'})
             -[:CONTAINS_PARAGRAPH]->(p:Paragraph)
             <-[:CONTAINS_PARAGRAPH]-(weisung:Document)
WHERE weisung.document_type IN ['BA_Weisung', 'Harald_Thome']
  AND p.paragraph_nummer IN ['19', '20', '21']  // Wichtigste Paragraphen
RETURN path
LIMIT 50
;

// 2. Quellen-Hierarchie Visualisierung
// Zeigt alle Dokumenttypen für SGB II
MATCH (d:Document {sgb_nummer: 'II'})
OPTIONAL MATCH (d)-[:CONTAINS_PARAGRAPH]->(p:Paragraph)
RETURN d, p
LIMIT 100
;

// 3. Paragraph-Netzwerk (§ 20 Regelbedarfe)
// Alle Dokumente die § 20 SGB II enthalten
MATCH (p:Paragraph {sgb_nummer: 'II', paragraph_nummer: '20'})
MATCH (d:Document)-[:CONTAINS_PARAGRAPH]->(p)
MATCH (d)-[:HAS_CHUNK]->(c:Chunk)
WHERE c.paragraph_nummer = '20'
RETURN d, p, c
LIMIT 30
;

// 4. Vollständigkeits-Graph
// Zeigt welche SGBs Gesetze UND Weisungen haben
MATCH (gesetz:Document {document_type: 'Gesetz'})
OPTIONAL MATCH (weisung:Document {sgb_nummer: gesetz.sgb_nummer})
WHERE weisung.document_type = 'BA_Weisung'
RETURN gesetz, weisung
LIMIT 50
;

// 5. Trust-Score Visualisierung
// Farbcodiert nach Vertrauenswürdigkeit
MATCH (d:Document)
WHERE d.trust_score IS NOT NULL
WITH d,
     CASE
       WHEN d.trust_score >= 95 THEN '🟢 Sehr hoch (95-100%)'
       WHEN d.trust_score >= 85 THEN '🟡 Hoch (85-94%)'
       ELSE '🟠 Mittel (70-84%)'
     END as trust_kategorie
RETURN d, trust_kategorie
LIMIT 50
;

// 6. Aktualitäts-Graph
// Dokumente nach Stand-Datum gruppiert
MATCH (d:Document)
WHERE d.stand_datum IS NOT NULL
WITH d,
     CASE
       WHEN d.stand_datum >= '2024-01-01' THEN '🟢 2024-2025'
       WHEN d.stand_datum >= '2023-01-01' THEN '🟡 2023'
       WHEN d.stand_datum >= '2021-01-01' THEN '🟠 2021-2022'
       ELSE '🔴 Vor 2021'
     END as aktualität
RETURN d, aktualität
LIMIT 50
;

// 7. Chunk-Netzwerk für Keyword
// Zeigt alle Chunks zu "Regelbedarf"
CALL db.index.fulltext.queryNodes('sozialrecht_fulltext', 'Regelbedarf')
YIELD node as chunk, score
MATCH (d:Document)-[:HAS_CHUNK]->(chunk)
RETURN d, chunk
ORDER BY score DESC
LIMIT 20
;

// 8. Hybrid-Strategie Graph
// Visualisiert Gesetz (Beträge) + Weisung (Verfahren) für § 19, 20
MATCH (gesetz:Document {sgb_nummer: 'II', document_type: 'Gesetz'})
      -[:CONTAINS_PARAGRAPH]->(p:Paragraph)
WHERE p.paragraph_nummer IN ['19', '20']
MATCH (weisung:Document)-[:CONTAINS_PARAGRAPH]->(p)
WHERE weisung.document_type IN ['BA_Weisung', 'Harald_Thome']
RETURN gesetz, p, weisung
;

// 9. Alle SGBs Übersicht
// Zeigt alle 13 SGBs mit ihren Dokumenten
MATCH (d:Document {document_type: 'Gesetz'})
RETURN d
ORDER BY d.sgb_nummer
;

// 10. Paragraph-Cluster
// Zeigt welche Paragraphen am meisten Quellen haben
MATCH (p:Paragraph)
MATCH (d:Document)-[:CONTAINS_PARAGRAPH]->(p)
WITH p, COUNT(DISTINCT d) as quellen_anzahl
WHERE quellen_anzahl > 1
MATCH (d:Document)-[:CONTAINS_PARAGRAPH]->(p)
RETURN p, d
LIMIT 50
;
