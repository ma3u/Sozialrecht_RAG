// UC19: Schulungskonzept - Gesetzesänderungen
// SGB: II | Paragraphen: *
// Priority: P1 | Tool: N/A (Amendment data import required)


                    MATCH (doc:LegalDocument {sgb_nummer: 'II'})
                          -[:CONTAINS_NORM]->(norm:LegalNorm)
                          -[:AMENDED_BY]->(amendment:Amendment)
                    WHERE amendment.date >= date('2023-01-01')
                    RETURN 
                        norm.paragraph_nummer,
                        norm.enbez,
                        amendment.title,
                        amendment.date,
                        amendment.summary
                    ORDER BY amendment.date DESC
                    LIMIT 10
                