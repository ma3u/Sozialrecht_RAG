// UC16: Qualitätssicherung - Fehlerquellen in Bescheiden
// SGB: II | Paragraphen: *
// Priority: P0 | Tool: Neo4j Browser + Cypher Analytics


                    MATCH (norm:LegalNorm)-[:HAS_CHUNK]->(chunk:Chunk)
                    WHERE EXISTS {
                        MATCH (norm)<-[:CONTAINS_NORM]-(doc:LegalDocument {sgb_nummer: 'II'})
                    }
                    WITH norm, count(chunk) as chunk_count
                    WHERE chunk_count > 10
                    MATCH (norm)-[:HAS_CHUNK]->(chunk:Chunk)
                    WHERE chunk.text CONTAINS 'Ausnahme' 
                       OR chunk.text CONTAINS 'abweichend'
                       OR chunk.text CONTAINS 'jedoch'
                    RETURN 
                        norm.paragraph_nummer,
                        norm.enbez,
                        chunk_count as komplexitaet,
                        count(DISTINCT chunk) as ausnahmen
                    ORDER BY komplexitaet DESC, ausnahmen DESC
                    LIMIT 10
                