// UC18: Prozessmodellierung - Ideal-Prozess Antragsprüfung
// SGB: II | Paragraphen: 7, 11, 11b, 12, 37, 33
// Priority: P0 | Tool: Neo4j Browser + BPMN Modeler


                    MATCH (doc:LegalDocument {sgb_nummer: 'II'})
                          -[:CONTAINS_NORM]->(norm:LegalNorm)
                    WHERE norm.paragraph_nummer IN ['7', '11', '11b', '12', '37', '33']
                    RETURN 
                        norm.paragraph_nummer,
                        norm.enbez,
                        'Phase: ' + 
                        CASE 
                            WHEN norm.paragraph_nummer = '7' THEN '2 - Anspruchsprüfung'
                            WHEN norm.paragraph_nummer IN ['11', '11b', '12'] THEN '2 - Bedürftigkeitsprüfung'
                            WHEN norm.paragraph_nummer IN ['37', '33'] THEN '3 - Entscheidung'
                        END as prozessphase
                    ORDER BY prozessphase, norm.paragraph_nummer
                