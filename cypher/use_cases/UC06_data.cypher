// UC06: Bedarfsgemeinschaft vs. Haushaltsgemeinschaft
// SGB: II | Paragraphen: 7
// Priority: P0 | Tool: Neo4j Browser + Bloom (Graph Exploration)


                    MATCH (doc:LegalDocument {sgb_nummer: 'II'})
                          -[:CONTAINS_NORM]->(norm:LegalNorm)
                    WHERE norm.paragraph_nummer = '7'
                    MATCH (norm)-[:HAS_CHUNK]->(chunk:Chunk)
                    RETURN 
                        norm.paragraph_nummer,
                        norm.enbez,
                        count(chunk) as chunks,
                        collect(chunk.text)[0..3] as beispiel_definitionen
                    ORDER BY chunk.chunk_index
                