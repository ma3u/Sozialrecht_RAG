// UC19: Schulungskonzept - Gesetzesänderungen
// SGB: II | Paragraphen: *
// Priority: P1 | Tool: N/A (Amendment data import required)


                    MATCH (doc:LegalDocument {sgb_nummer: 'II'})
                          -[:CONTAINS_NORM]->(norm:LegalNorm)
                          -[:HAS_AMENDMENT]->(amendment:Amendment)
                    WHERE amendment.amendment_date >= date('2023-01-01')
                    RETURN 
                        norm.paragraph_nummer,
                        norm.enbez,
                        amendment.raw_text as title,
                        amendment.amendment_date as date,
                        amendment.amendment_type as summary
                    ORDER BY amendment.amendment_date DESC
                    LIMIT 10
                