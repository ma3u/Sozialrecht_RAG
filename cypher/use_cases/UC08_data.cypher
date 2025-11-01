// UC08: Darlehen für Erstausstattung
// SGB: II | Paragraphen: 24
// Priority: P0 | Tool: Neo4j Browser


                    MATCH (norm:LegalNorm)
                    WHERE norm.paragraph_nummer = '24'
                      AND EXISTS {
                          MATCH (norm)<-[:CONTAINS_NORM]-(doc:LegalDocument {sgb_nummer: 'II'})
                      }
                    MATCH (norm)-[:HAS_CHUNK]->(chunk:Chunk)
                    WHERE chunk.text CONTAINS 'Erstausstattung' 
                       OR chunk.text CONTAINS 'Schwangerschaft'
                       OR chunk.text CONTAINS 'Darlehen'
                    RETURN 
                        norm.enbez,
                        count(chunk) as relevante_chunks,
                        collect(chunk.text)[0..2] as beispiele
                