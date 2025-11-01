// UC19: Schulungskonzept - Gesetzesänderungen - Visualization
// Run this in Neo4j Browser for graph visualization


                    MATCH path = (doc:LegalDocument {sgb_nummer: 'II'})
                                 -[:CONTAINS_NORM]->(norm:LegalNorm)
                                 -[:AMENDED_BY]->(amendment:Amendment)
                    RETURN path LIMIT 20
                