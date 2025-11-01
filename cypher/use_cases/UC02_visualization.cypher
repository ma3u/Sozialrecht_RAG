// UC02: Sanktionsprüfung bei Meldeversäumnis - Visualization
// Run this in Neo4j Browser for graph visualization


                    MATCH path = (doc:LegalDocument {sgb_nummer: 'II'})
                                 -[:CONTAINS_NORM]->(norm:LegalNorm {paragraph_nummer: '32'})
                                 -[:HAS_CHUNK]->(chunk:Chunk)
                    RETURN path LIMIT 30
                