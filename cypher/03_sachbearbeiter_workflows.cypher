// ========================================
// SACHBEARBEITER WORKFLOWS
// Praktische Queries für Fallbearbeitung
// ========================================

// 1. Regelbedarfe-Abfrage (Hybrid-Strategie)
// Zeigt GESETZ (Beträge) + WEISUNG (Verfahren) für § 20
MATCH (gesetz:Document {sgb_nummer: 'II', document_type: 'Gesetz'})-[:CONTAINS_PARAGRAPH]->(p:Paragraph {paragraph_nummer: '20'})
OPTIONAL MATCH (weisung:Document {document_type: 'BA_Weisung'})-[:CONTAINS_PARAGRAPH]->(p)
RETURN
  '📋 Regelbedarfe (§ 20 SGB II)' as Thema,
  gesetz.filename as Gesetz_Quelle,
  gesetz.trust_score as Gesetz_Trust,
  SUBSTRING(p.content, 0, 500) as Gesetz_Inhalt,
  weisung.filename as Weisung_Quelle,
  weisung.trust_score as Weisung_Trust,
  weisung.stand_datum as Weisung_Stand
;

// 2. Leistungsberechtigung komplett
// Alle relevanten Paragraphen für Leistungsanspruch
MATCH (d:Document {sgb_nummer: 'II'})-[:CONTAINS_PARAGRAPH]->(p:Paragraph)
WHERE p.paragraph_nummer IN ['7', '8', '9']  // Leistungsberechtigte, Erwerbsfähigkeit, Hilfebedürftigkeit
RETURN
  p.paragraph_nummer as Paragraph,
  d.document_type as Quelle,
  d.filename as Datei,
  d.trust_score as Trust,
  SUBSTRING(p.content, 0, 200) as Inhalt
ORDER BY p.paragraph_nummer, d.type_priority
;

// 3. Einkommen/Vermögen - Alle Quellen
// Umfassende Analyse für §§ 11-12
MATCH (p:Paragraph)
WHERE p.sgb_nummer = 'II' AND p.paragraph_nummer IN ['11', '11a', '11b', '12']
MATCH (d:Document)-[:CONTAINS_PARAGRAPH]->(p)
RETURN
  p.paragraph_nummer as Paragraph,
  COLLECT({
    typ: d.document_type,
    datei: d.filename,
    trust: d.trust_score,
    stand: d.stand_datum,
    priorität: d.type_priority
  }) as Alle_Quellen
ORDER BY p.paragraph_nummer
;

// 4. Sachbearbeiter-Checkliste generieren
// Erstellt Checkliste aus Paragraphen für Antragsprüfung
MATCH (p:Paragraph {sgb_nummer: 'II'})
WHERE p.paragraph_nummer IN ['7', '8', '9', '10', '11', '12', '20', '21']
MATCH (d:Document {document_type: 'Gesetz'})-[:CONTAINS_PARAGRAPH]->(p)
RETURN
  p.paragraph_nummer as Schritt,
  CASE p.paragraph_nummer
    WHEN '7' THEN '1. Leistungsberechtigung prüfen'
    WHEN '8' THEN '2. Erwerbsfähigkeit prüfen'
    WHEN '9' THEN '3. Hilfebedürftigkeit prüfen'
    WHEN '10' THEN '4. Zumutbarkeit prüfen'
    WHEN '11' THEN '5. Einkommen berechnen'
    WHEN '12' THEN '6. Vermögen prüfen'
    WHEN '20' THEN '7. Regelbedarf berechnen'
    WHEN '21' THEN '8. Mehrbedarfe prüfen'
  END as Aufgabe,
  SUBSTRING(p.content, 0, 150) as Rechtliche_Grundlage
ORDER BY p.paragraph_nummer
;

// 5. Sanktions-Prüfung (§ 31-32)
// Alle Dokumente zu Sanktionen
MATCH (p:Paragraph)
WHERE p.sgb_nummer = 'II' AND p.paragraph_nummer IN ['31', '31a', '31b', '32']
MATCH (d:Document)-[:CONTAINS_PARAGRAPH]->(p)
RETURN
  p.paragraph_nummer as Paragraph,
  CASE p.paragraph_nummer
    WHEN '31' THEN 'Pflichtverletzungen'
    WHEN '31a' THEN 'Rechtsfolgen (30% Minderung)'
    WHEN '31b' THEN 'Wiederholte Pflichtverletzung (60-100%)'
    WHEN '32' THEN 'Ergänzende Regelungen'
  END as Thema,
  d.document_type as Quelle,
  d.trust_score as Trust
ORDER BY p.paragraph_nummer, d.type_priority
;

// 6. Aktualitäts-Warnung für Sachbearbeiter
// Zeigt veraltete Weisungen (>2 Jahre) mit Warnung
MATCH (d:Document)
WHERE d.document_type IN ['BA_Weisung', 'Harald_Thome']
  AND d.stand_datum < '2023-01-01'
RETURN
  d.sgb_nummer as SGB,
  d.filename as Datei,
  d.stand_datum as Stand,
  CASE
    WHEN d.stand_datum < '2021-01-01' THEN '🔴 VERALTET (>4 Jahre)'
    WHEN d.stand_datum < '2023-01-01' THEN '⚠️ ALT (2-4 Jahre)'
    ELSE '🟡 PRÜFEN'
  END as Warnung,
  '→ Hybrid-Strategie nutzen (Gesetz bevorzugen)' as Empfehlung
ORDER BY d.stand_datum ASC
;

// 7. Verfahrens-Schritte mit Rechtsgrundlagen
// Für Prozess-Integration (BPMN)
MATCH (p:Paragraph {sgb_nummer: 'II'})
WHERE p.paragraph_nummer IN ['37', '40', '41', '42']  // Verfahrensvorschriften
MATCH (d:Document)-[:CONTAINS_PARAGRAPH]->(p)
RETURN
  p.paragraph_nummer as Paragraph,
  CASE p.paragraph_nummer
    WHEN '37' THEN 'Antragstellung (Zuständigkeit)'
    WHEN '40' THEN 'Antragserfordernis'
    WHEN '41' THEN 'Beratung und Unterstützung'
    WHEN '42' THEN 'Verfahrensvorschriften'
  END as Prozess_Schritt,
  d.document_type as Quelle,
  d.filename as Handlungsempfehlung
ORDER BY p.paragraph_nummer, d.type_priority
;

// 8. Quick-Search: Finde alle Dokumente zu Stichwort
// Beispiel: "Mehrbedarf"
CALL db.index.fulltext.queryNodes('sozialrecht_fulltext', 'Mehrbedarf') YIELD node, score
MATCH (d:Document)-[:HAS_CHUNK]->(node)
RETURN DISTINCT
  d.sgb_nummer as SGB,
  d.document_type as Typ,
  d.filename as Datei,
  d.trust_score as Trust,
  score as Relevanz,
  node.paragraph_nummer as Paragraph
ORDER BY score DESC
LIMIT 10
;
