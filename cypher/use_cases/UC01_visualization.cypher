// UC01: Regelbedarfsermittlung für Familie - Visualization
// Run this in Neo4j Browser for graph visualization


                    MATCH path = (doc:LegalDocument {sgb_nummer: 'II'})
                                 -[:CONTAINS_NORM]->(norm:LegalNorm)
                                 -[:HAS_CHUNK]->(chunk:Chunk)
                    WHERE norm.paragraph_nummer IN ['20', '21', '22', '23']
                    RETURN path LIMIT 50
                