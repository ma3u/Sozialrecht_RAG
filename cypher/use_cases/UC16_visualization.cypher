// UC16: Qualitätssicherung - Fehlerquellen in Bescheiden - Visualization
// Run this in Neo4j Browser for graph visualization


                    MATCH (norm:LegalNorm)-[:HAS_CHUNK]->(chunk:Chunk)
                    WHERE EXISTS {
                        MATCH (norm)<-[:CONTAINS_NORM]-(doc:LegalDocument {sgb_nummer: 'II'})
                    }
                    WITH norm, count(chunk) as chunk_count
                    WHERE chunk_count > 15
                    MATCH path = (norm)-[:HAS_CHUNK]->(chunk)
                    RETURN path LIMIT 50
                