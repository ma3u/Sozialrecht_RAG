// UC13: Prozessanalyse - Durchlaufzeiten Erstantrag - Visualization
// Run this in Neo4j Browser for graph visualization


                    MATCH path = (doc:LegalDocument {sgb_nummer: 'II'})
                                 -[:CONTAINS_NORM]->(norm:LegalNorm)
                                 -[:HAS_CHUNK]->(chunk:Chunk)
                    WHERE norm.paragraph_nummer IN ['37', '41', '44']
                      AND (chunk.text CONTAINS 'Frist' OR chunk.text CONTAINS 'Monat')
                    RETURN path LIMIT 30
                