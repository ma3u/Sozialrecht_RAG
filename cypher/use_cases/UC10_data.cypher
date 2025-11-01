// UC10: Widerspruch bearbeiten
// SGB: X | Paragraphen: 79, 80, 84, 85
// Priority: P0 | Tool: N/A (SGB X import required)


                    MATCH (doc:LegalDocument {sgb_nummer: 'X'})
                          -[:CONTAINS_NORM]->(norm:LegalNorm)
                    WHERE norm.paragraph_nummer IN ['79', '80', '84', '85']
                    OPTIONAL MATCH (norm)-[:HAS_CHUNK]->(chunk:Chunk)
                    RETURN 
                        norm.paragraph_nummer,
                        norm.enbez,
                        count(chunk) as chunks
                    ORDER BY norm.paragraph_nummer
                