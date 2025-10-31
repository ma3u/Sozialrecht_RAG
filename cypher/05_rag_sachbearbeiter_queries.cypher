// ================================================================
// RAG SACHBEARBEITER QUERIES (XML-Based)
// Effiziente Queries für Fallbearbeitung mit dem neuen XML-Schema
// ================================================================

// =================================
// 1. REGELBEDARFE PRÜFEN (§ 20 SGB II)
// Häufigster Use Case: Regelbedarfe berechnen
// =================================

// 1a. Finde § 20 SGB II mit vollständiger Hierarchie
MATCH (doc:LegalDocument {sgb_nummer: "II"})
-[:HAS_STRUCTURE]->(struct:StructuralUnit)
-[:CONTAINS_NORM]->(norm:LegalNorm)
WHERE norm.paragraph_nummer = "20"

// Hole alle Texteinheiten und Chunks
MATCH (norm)-[:HAS_CONTENT]->(text:TextUnit)
OPTIONAL MATCH (norm)-[:HAS_CHUNK]->(chunk:Chunk)

RETURN 
  doc.jurabk as Gesetz,
  struct.gliederungsbez as Kapitel,
  norm.enbez as Paragraph,
  norm.titel as Titel,
  COLLECT(DISTINCT text.text) as Gesetzestext,
  COUNT(DISTINCT chunk) as Anzahl_RAG_Chunks,
  doc.builddate as Stand
ORDER BY text.order_index;

// 1b. Semantische Suche: "Regelbedarfe" über alle Chunks
CALL db.index.vector.queryNodes('chunk_embeddings', 10, $embedding_vektor)
YIELD node as chunk, score

MATCH (norm:LegalNorm)-[:HAS_CHUNK]->(chunk)
MATCH (doc:LegalDocument)-[:HAS_STRUCTURE]->()-[:CONTAINS_NORM]->(norm)

RETURN 
  score as Relevanz,
  doc.sgb_nummer as SGB,
  norm.enbez as Paragraph,
  norm.titel as Titel,
  chunk.text as Relevanter_Text
ORDER BY score DESC
LIMIT 5;


// =================================
// 2. LEISTUNGSBERECHTIGUNG PRÜFEN
// Workflow: Erwerbsfähigkeit → Hilfebedürftigkeit → Alter
// =================================

// 2a. §§ 7-9 SGB II: Alle Voraussetzungen für Bürgergeld
MATCH (doc:LegalDocument {sgb_nummer: "II"})
-[:HAS_STRUCTURE]->(struct:StructuralUnit)
-[:CONTAINS_NORM]->(norm:LegalNorm)
WHERE norm.paragraph_nummer IN ["7", "8", "9"]

MATCH (norm)-[:HAS_CONTENT]->(text:TextUnit)

RETURN 
  norm.paragraph_nummer as Paragraph_Nr,
  norm.enbez as Paragraph,
  norm.titel as Prüfpunkt,
  CASE norm.paragraph_nummer
    WHEN "7" THEN "1️⃣ Leistungsberechtigung"
    WHEN "8" THEN "2️⃣ Erwerbsfähigkeit (15-67 Jahre, 3h/Tag)"
    WHEN "9" THEN "3️⃣ Hilfebedürftigkeit (Lebensunterhalt)"
  END as Prüfschritt,
  text.text as Gesetzlicher_Inhalt
ORDER BY norm.paragraph_nummer, text.order_index;


// =================================
// 3. EINKOMMEN & VERMÖGEN BERECHNEN
// §§ 11-12 SGB II mit Unterabschnitten
// =================================

// 3a. Alle Einkommens-Paragraphen mit Struktur
MATCH (doc:LegalDocument {sgb_nummer: "II"})
-[:HAS_STRUCTURE]->(struct:StructuralUnit)
-[:CONTAINS_NORM]->(norm:LegalNorm)
WHERE norm.paragraph_nummer STARTS WITH "11"
   OR norm.paragraph_nummer = "12"

MATCH (norm)-[:HAS_CONTENT]->(text:TextUnit)

RETURN 
  struct.gliederungsbez as Kapitel,
  norm.paragraph_nummer as Paragraph_Nr,
  norm.enbez as Paragraph,
  norm.titel as Thema,
  SUBSTRING(text.text, 0, 200) as Gesetzesauszug,
  COUNT(text) as Anzahl_Absätze
ORDER BY norm.paragraph_nummer, text.order_index;

// 3b. Finde verwandte Normen über Chunk-Ähnlichkeit
// Beispiel: § 11 SGB II → finde ähnliche Einkommensregelungen in anderen SGBs
MATCH (norm:LegalNorm {paragraph_nummer: "11"})
-[:HAS_CHUNK]->(ref_chunk:Chunk)
WHERE EXISTS {
  MATCH (norm)<-[:CONTAINS_NORM]-()<-[:HAS_STRUCTURE]-
        (doc:LegalDocument {sgb_nummer: "II"})
}

WITH ref_chunk.embedding as query_embedding
LIMIT 1

CALL db.index.vector.queryNodes('chunk_embeddings', 5, query_embedding)
YIELD node as similar_chunk, score

MATCH (related_norm:LegalNorm)-[:HAS_CHUNK]->(similar_chunk)
MATCH (related_doc:LegalDocument)-[:HAS_STRUCTURE]->()
      -[:CONTAINS_NORM]->(related_norm)
WHERE related_doc.sgb_nummer <> "II"

RETURN 
  score as Ähnlichkeit,
  related_doc.sgb_nummer as Anderes_SGB,
  related_norm.enbez as Paragraph,
  related_norm.titel as Thema,
  similar_chunk.text as Vergleichstext
ORDER BY score DESC;


// =================================
// 4. MEHRBEDARF PRÜFEN (§ 21 SGB II)
// Mit allen Unterabschnitten (Alleinerziehende, Behinderung, etc.)
// =================================

MATCH (doc:LegalDocument {sgb_nummer: "II"})
-[:HAS_STRUCTURE]->()-[:CONTAINS_NORM]->(norm:LegalNorm)
WHERE norm.paragraph_nummer STARTS WITH "21"

MATCH (norm)-[:HAS_CONTENT]->(text:TextUnit)

RETURN 
  norm.paragraph_nummer as Paragraph_Nr,
  norm.enbez as Paragraph,
  norm.titel as Mehrbedarf_Typ,
  text.text as Regelung,
  text.order_index as Absatz_Nr
ORDER BY norm.paragraph_nummer, text.order_index;


// =================================
// 5. SANKTIONEN PRÜFEN (§§ 31-32 SGB II)
// Pflichtverletzungen und Rechtsfolgen
// =================================

MATCH (doc:LegalDocument {sgb_nummer: "II"})
-[:HAS_STRUCTURE]->()-[:CONTAINS_NORM]->(norm:LegalNorm)
WHERE norm.paragraph_nummer IN ["31", "31a", "31b", "32"]

MATCH (norm)-[:HAS_CONTENT]->(text:TextUnit)

RETURN 
  norm.enbez as Paragraph,
  CASE norm.paragraph_nummer
    WHEN "31"  THEN "⚠️ Pflichtverletzungen"
    WHEN "31a" THEN "📉 Minderung 30%"
    WHEN "31b" THEN "📉 Minderung 60-100%"
    WHEN "32"  THEN "📋 Ergänzende Regeln"
  END as Kategorie,
  norm.titel as Titel,
  text.text as Gesetzestext
ORDER BY norm.paragraph_nummer, text.order_index;


// =================================
// 6. ANTRAGSPRÜFUNG: VOLLSTÄNDIGE CHECKLISTE
// Kompletter Workflow von Antrag bis Bescheid
// =================================

MATCH (doc:LegalDocument {sgb_nummer: "II"})
-[:HAS_STRUCTURE]->()-[:CONTAINS_NORM]->(norm:LegalNorm)
WHERE norm.paragraph_nummer IN [
  "7",   // Leistungsberechtigte
  "8",   // Erwerbsfähigkeit
  "9",   // Hilfebedürftigkeit
  "11",  // Einkommen
  "12",  // Vermögen
  "20",  // Regelbedarf
  "21",  // Mehrbedarf
  "22",  // Kosten der Unterkunft
  "37",  // Zuständigkeit
  "40"   // Antragserfordernis
]

RETURN 
  CASE norm.paragraph_nummer
    WHEN "7"  THEN 1
    WHEN "8"  THEN 2
    WHEN "9"  THEN 3
    WHEN "11" THEN 4
    WHEN "12" THEN 5
    WHEN "20" THEN 6
    WHEN "21" THEN 7
    WHEN "22" THEN 8
    WHEN "37" THEN 9
    WHEN "40" THEN 10
  END as Schritt,
  
  norm.enbez as Paragraph,
  norm.titel as Prüfpunkt,
  
  CASE norm.paragraph_nummer
    WHEN "7"  THEN "✅ Person berechtigt?"
    WHEN "8"  THEN "✅ 15-67 Jahre, 3h arbeitsfähig?"
    WHEN "9"  THEN "✅ Lebensunterhalt nicht gesichert?"
    WHEN "11" THEN "💶 Einkommen berechnen"
    WHEN "12" THEN "🏦 Vermögen prüfen"
    WHEN "20" THEN "💰 Regelbedarf ermitteln"
    WHEN "21" THEN "➕ Mehrbedarfe prüfen"
    WHEN "22" THEN "🏠 KdU (Miete) berücksichtigen"
    WHEN "37" THEN "📍 Zuständigkeit klären"
    WHEN "40" THEN "📄 Antrag vollständig?"
  END as Handlung

ORDER BY Schritt;


// =================================
// 7. CROSS-SGB SUCHE: REHABILITATION
// Finde alle relevanten Paragraphen zur Rehabilitation über alle SGBs
// =================================

// Semantische Suche: "Rehabilitation"
CALL db.index.vector.queryNodes('chunk_embeddings', 15, $embedding_rehabilitation)
YIELD node as chunk, score

MATCH (norm:LegalNorm)-[:HAS_CHUNK]->(chunk)
MATCH (doc:LegalDocument)-[:HAS_STRUCTURE]->()-[:CONTAINS_NORM]->(norm)

RETURN 
  score as Relevanz,
  doc.sgb_nummer as SGB,
  doc.jurabk as Gesetz,
  norm.enbez as Paragraph,
  norm.titel as Titel,
  chunk.text as Relevanter_Abschnitt
ORDER BY score DESC
LIMIT 10;


// =================================
// 8. AKTUALITÄT PRÜFEN
// Zeigt den Stand aller importierten Gesetze
// =================================

MATCH (doc:LegalDocument)
RETURN 
  doc.sgb_nummer as SGB,
  doc.jurabk as Gesetz,
  doc.lange_titel as Vollständiger_Name,
  doc.builddate as Letzter_Stand,
  doc.trust_score as Vertrauenswürdigkeit,
  CASE 
    WHEN duration.between(doc.builddate, datetime()).months < 6 
    THEN "✅ Aktuell"
    WHEN duration.between(doc.builddate, datetime()).months < 12 
    THEN "⚠️ 6-12 Monate alt"
    ELSE "❗ Älter als 1 Jahr"
  END as Aktualitäts_Status
ORDER BY doc.sgb_nummer;


// =================================
// 9. HIERARCHISCHE NAVIGATION
// Zeigt die vollständige Struktur eines SGB
// =================================

// 9a. SGB II Struktur-Übersicht
MATCH (doc:LegalDocument {sgb_nummer: "II"})
-[:HAS_STRUCTURE]->(struct:StructuralUnit)

OPTIONAL MATCH (struct)-[:CONTAINS_NORM]->(norm:LegalNorm)

RETURN 
  struct.gliederungskennzahl as Kennzahl,
  struct.gliederungsbez as Strukturtyp,
  struct.gliederungstitel as Titel,
  COUNT(norm) as Anzahl_Paragraphen
ORDER BY struct.gliederungskennzahl;

// 9b. Drill-Down: Kapitel → Paragraphen → Inhalt
MATCH (doc:LegalDocument {sgb_nummer: "II"})
-[:HAS_STRUCTURE]->(struct:StructuralUnit {gliederungsbez: "Kapitel 3"})
-[:CONTAINS_NORM]->(norm:LegalNorm)

MATCH (norm)-[:HAS_CONTENT]->(text:TextUnit)

RETURN 
  norm.enbez as Paragraph,
  norm.titel as Titel,
  COLLECT(text.text)[0..1] as Erste_Absätze
ORDER BY norm.order_index
LIMIT 10;


// =================================
// 10. ÄNDERUNGSHISTORIE (AMENDMENTS)
// Zeigt, welche Paragraphen kürzlich geändert wurden
// =================================

MATCH (norm:LegalNorm)-[:HAS_AMENDMENT]->(amendment:Amendment)
MATCH (doc:LegalDocument)-[:HAS_STRUCTURE]->()-[:CONTAINS_NORM]->(norm)

WHERE doc.sgb_nummer = "II"

RETURN 
  norm.enbez as Paragraph,
  norm.titel as Titel,
  amendment.standtyp as Änderungstyp,
  amendment.standkommentar as Beschreibung,
  amendment.amendment_date as Datum
ORDER BY amendment.amendment_date DESC
LIMIT 20;


// =================================
// 11. PERFORMANCE-OPTIMIERTE SUCHE
// Nutzt Indizes für schnelle Paragraph-Lookups
// =================================

// 11a. Index-basierte Suche (sehr schnell)
MATCH (norm:LegalNorm)
WHERE norm.paragraph_nummer = "20"
  AND EXISTS {
    MATCH (norm)<-[:CONTAINS_NORM]-()<-[:HAS_STRUCTURE]-
          (doc:LegalDocument {sgb_nummer: "II"})
  }

MATCH (norm)-[:HAS_CONTENT]->(text:TextUnit)

RETURN 
  norm.enbez as Paragraph,
  norm.titel as Titel,
  text.text as Inhalt
ORDER BY text.order_index;


// =================================
// 12. BATCH-EXPORT FÜR SACHBEARBEITER
// Exportiert alle wichtigen Paragraphen eines Falls
// =================================

// Beispiel: Bürgergeld-Fall Export
MATCH (doc:LegalDocument {sgb_nummer: "II"})
-[:HAS_STRUCTURE]->()-[:CONTAINS_NORM]->(norm:LegalNorm)
WHERE norm.paragraph_nummer IN [
  "7", "8", "9", "11", "11a", "11b", "12", 
  "20", "21", "22", "31", "37", "40"
]

MATCH (norm)-[:HAS_CONTENT]->(text:TextUnit)

RETURN 
  norm.paragraph_nummer as Paragraph_Nr,
  norm.enbez as Paragraph,
  norm.titel as Titel,
  COLLECT(text.text) as Vollständiger_Text
ORDER BY norm.paragraph_nummer;


// =================================
// 13. QUALITÄTSSICHERUNG
// Prüft Vollständigkeit der Daten
// =================================

// 13a. Paragraphen ohne Chunks (sollten wenige sein)
MATCH (norm:LegalNorm)
WHERE NOT EXISTS {
  MATCH (norm)-[:HAS_CHUNK]->(:Chunk)
}

MATCH (doc:LegalDocument)-[:HAS_STRUCTURE]->()-[:CONTAINS_NORM]->(norm)

RETURN 
  doc.sgb_nummer as SGB,
  norm.enbez as Paragraph_ohne_Chunks,
  norm.titel as Titel
LIMIT 20;

// 13b. Chunk-Verteilung pro SGB
MATCH (doc:LegalDocument)
MATCH (doc)-[:HAS_STRUCTURE]->()-[:CONTAINS_NORM]->(norm:LegalNorm)
OPTIONAL MATCH (norm)-[:HAS_CHUNK]->(chunk:Chunk)

RETURN 
  doc.sgb_nummer as SGB,
  COUNT(DISTINCT norm) as Anzahl_Paragraphen,
  COUNT(DISTINCT chunk) as Anzahl_Chunks,
  COUNT(DISTINCT chunk) * 1.0 / COUNT(DISTINCT norm) as Chunks_pro_Paragraph
ORDER BY doc.sgb_nummer;


// =================================
// USAGE NOTES
// =================================

/*
PARAMETER USAGE:

Für semantische Suchen (Queries 1b, 7):
  :param embedding_vektor => [768-dim Float-Array]
  :param embedding_rehabilitation => [768-dim Float-Array]

Diese werden von der Python-Anwendung generiert:

  from sentence_transformers import SentenceTransformer
  model = SentenceTransformer('paraphrase-multilingual-mpnet-base-v2')
  embedding = model.encode("Regelbedarfe").tolist()
  
  # In Neo4j übergeben:
  session.run(query, embedding_vektor=embedding)

PERFORMANCE TIPS:
- Queries 1a, 2a, 3a, 4, 5, 6, 9, 11: Sehr schnell (< 100ms)
- Queries 1b, 7: Schnell bei richtigen Indizes (< 500ms)
- Query 12: Mittel bei vielen Paragraphen (< 1s)

INDEX VORAUSSETZUNGEN:
- Vector Index: `chunk_embeddings` auf Chunk.embedding
- Property Indizes auf: 
  - LegalNorm.paragraph_nummer
  - LegalDocument.sgb_nummer
*/
