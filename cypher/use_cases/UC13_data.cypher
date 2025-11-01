// UC13: Prozessanalyse - Durchlaufzeiten Erstantrag
// SGB: II | Paragraphen: 37, 41, 44
// Priority: P0 | Tool: Neo4j Browser + Python Analytics


                    MATCH (doc:LegalDocument {sgb_nummer: 'II'})
                          -[:CONTAINS_NORM]->(norm:LegalNorm)
                    WHERE norm.paragraph_nummer IN ['37', '41', '44']
                    OPTIONAL MATCH (norm)-[:HAS_CHUNK]->(chunk:Chunk)
                    WHERE chunk.text CONTAINS 'Frist' 
                       OR chunk.text CONTAINS 'unverzüglich'
                       OR chunk.text CONTAINS 'Monat'
                    RETURN 
                        norm.paragraph_nummer,
                        norm.enbez,
                        count(DISTINCT chunk) as fristen_chunks,
                        collect(DISTINCT chunk.text)[0..2] as beispiel_fristen
                