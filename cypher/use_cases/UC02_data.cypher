// UC02: Sanktionsprüfung bei Meldeversäumnis
// SGB: II | Paragraphen: 32
// Priority: P0 | Tool: Neo4j Browser


                    MATCH (doc:LegalDocument {sgb_nummer: 'II'})
                          -[:CONTAINS_NORM]->(norm:LegalNorm)
                    WHERE norm.paragraph_nummer = '32'
                    OPTIONAL MATCH (norm)-[:HAS_CHUNK]->(chunk:Chunk)
                    WHERE chunk.text CONTAINS 'Meldeversäumnis' 
                       OR chunk.text CONTAINS 'Minderung'
                       OR chunk.text CONTAINS 'Sanktion'
                    RETURN 
                        norm.paragraph_nummer,
                        norm.enbez,
                        count(DISTINCT chunk) as relevante_chunks,
                        collect(DISTINCT chunk.text)[0..1] as beispiele
                