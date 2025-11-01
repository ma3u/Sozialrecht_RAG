// UC10: Widerspruch bearbeiten - Visualization
// Run this in Neo4j Browser for graph visualization


                    MATCH path = (doc:LegalDocument {sgb_nummer: 'X'})
                                 -[:CONTAINS_NORM]->(norm:LegalNorm)
                    WHERE norm.paragraph_nummer IN ['79', '80', '84', '85']
                    RETURN path LIMIT 20
                