// UC03: Einkommensanrechnung mit Freibeträgen
// SGB: II | Paragraphen: 11, 11b
// Priority: P0 | Tool: Neo4j Browser + Python Berechnungsmodul


                    MATCH (doc:LegalDocument {sgb_nummer: 'II'})
                          -[:CONTAINS_NORM]->(norm:LegalNorm)
                    WHERE norm.paragraph_nummer IN ['11', '11b']
                    OPTIONAL MATCH (norm)-[:HAS_CHUNK]->(chunk:Chunk)
                    WITH norm, collect(chunk.text) as chunks
                    RETURN 
                        norm.paragraph_nummer,
                        norm.enbez,
                        size(chunks) as chunk_count,
                        chunks[0..2] as beispiele
                    ORDER BY norm.paragraph_nummer
                