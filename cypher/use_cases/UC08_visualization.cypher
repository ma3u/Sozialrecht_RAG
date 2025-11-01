// UC08: Darlehen für Erstausstattung - Visualization
// Run this in Neo4j Browser for graph visualization


                    MATCH path = (doc:LegalDocument {sgb_nummer: 'II'})
                                 -[:CONTAINS_NORM]->(norm:LegalNorm {paragraph_nummer: '24'})
                                 -[:HAS_CHUNK]->(chunk:Chunk)
                    WHERE chunk.text CONTAINS 'Erstausstattung'
                    RETURN path LIMIT 30
                