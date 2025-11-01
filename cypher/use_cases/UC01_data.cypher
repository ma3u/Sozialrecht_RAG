// UC01: Regelbedarfsermittlung für Familie
// SGB: II | Paragraphen: 20, 21, 22, 23
// Priority: P0 | Tool: Neo4j Browser


                    MATCH (doc:LegalDocument {sgb_nummer: 'II'})
                          -[:CONTAINS_NORM]->(norm:LegalNorm)
                          -[:HAS_CHUNK]->(chunk:Chunk)
                    WHERE norm.paragraph_nummer IN ['20', '21', '22', '23']
                    RETURN 
                        norm.paragraph_nummer as paragraph,
                        norm.enbez as titel,
                        count(DISTINCT chunk) as chunks,
                        collect(DISTINCT chunk.text)[0..2] as beispiel_texte
                    ORDER BY norm.order_index
                