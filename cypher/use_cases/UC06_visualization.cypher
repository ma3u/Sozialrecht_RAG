// UC06: Bedarfsgemeinschaft vs. Haushaltsgemeinschaft - Visualization
// Run this in Neo4j Browser for graph visualization


                    MATCH path = (doc:LegalDocument {sgb_nummer: 'II'})
                                 -[:CONTAINS_NORM]->(norm:LegalNorm {paragraph_nummer: '7'})
                                 -[:HAS_CHUNK]->(chunk:Chunk)
                    RETURN path LIMIT 100
                