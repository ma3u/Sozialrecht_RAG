// UC19: Schulungskonzept - Gesetzesänderungen
// SGB: II | Paragraphen: Document-level (amendments track law changes, not individual paragraphs)
// Priority: P1 | Amendments are tracked at document level in German legal XML
// Note: Amendments show when the entire law was changed, not specific paragraphs

                    MATCH (doc:LegalDocument {sgb_nummer: 'II'})
                          -[:CONTAINS_NORM]->(norm:LegalNorm)
                          -[:HAS_AMENDMENT]->(amendment:Amendment)
                    WHERE amendment.amendment_date >= date('2023-01-01')
                      AND norm.paragraph_nummer IS NOT NULL  // Filter out document-level norm
                    RETURN 
                        'SGB II' as gesetz,
                        amendment.artikel as artikel,
                        amendment.gesetz_ref as aenderndes_gesetz,
                        amendment.amendment_date as datum,
                        amendment.amendment_type as typ,
                        amendment.raw_text as beschreibung
                    ORDER BY amendment.amendment_date DESC
                    LIMIT 10
                    
                    // Alternative: Show all amendments to SGB II
                    UNION
                    MATCH (doc:LegalDocument {sgb_nummer: 'II'})
                          -[:CONTAINS_NORM]->(norm:LegalNorm)
                          -[:HAS_AMENDMENT]->(amendment:Amendment)
                    WHERE amendment.amendment_date >= date('2023-01-01')
                      AND norm.paragraph_nummer = 'Norm 0'  // Document-level
                    RETURN 
                        'SGB II (Gesamt)' as gesetz,
                        amendment.artikel as artikel,
                        amendment.gesetz_ref as aenderndes_gesetz,
                        amendment.amendment_date as datum,
                        amendment.amendment_type as typ,
                        amendment.raw_text as beschreibung
                    ORDER BY datum DESC
                    LIMIT 10
                