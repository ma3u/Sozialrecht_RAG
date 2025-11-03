// UC19: Schulungskonzept - Gesetzesänderungen - Visualization
// Run this in Neo4j Browser for graph visualization


                    MATCH path = (doc:LegalDocument {sgb_nummer: 'II'})
                                 -[:CONTAINS_NORM]->(norm:LegalNorm)
                                 -[:HAS_AMENDMENT]->(amendment:Amendment)
                    RETURN path LIMIT 20
                