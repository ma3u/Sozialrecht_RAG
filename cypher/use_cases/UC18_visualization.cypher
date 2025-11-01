// UC18: Prozessmodellierung - Ideal-Prozess Antragsprüfung - Visualization
// Run this in Neo4j Browser for graph visualization


                    MATCH path = (doc:LegalDocument {sgb_nummer: 'II'})
                                 -[:CONTAINS_NORM]->(norm:LegalNorm)
                    WHERE norm.paragraph_nummer IN ['7', '11', '11b', '12', '37', '33']
                    RETURN path
                