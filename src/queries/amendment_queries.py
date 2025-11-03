#!/usr/bin/env python3
"""
Amendment Query Library
Predefined Cypher queries for amendment timeline, law impact analysis, and version tracking
"""

from typing import Dict, List, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AmendmentQueries:
    """Collection of Cypher queries for amendment analysis"""
    
    # ========== Timeline Queries ==========
    
    @staticmethod
    def get_amendment_history(doknr: str) -> str:
        """
        Get complete amendment history for a specific norm
        
        Args:
            doknr: Document number (e.g., 'BJNR125410996')
            
        Returns:
            Cypher query string
        """
        return """
        MATCH (norm:Norm {doknr: $doknr})-[:HAS_AMENDMENT]->(amendment:Amendment)
        RETURN 
            amendment.amendment_date as date,
            amendment.amendment_type as type,
            amendment.artikel as artikel,
            amendment.gesetz_ref as gesetz,
            amendment.bgbl_issue as bgbl,
            amendment.raw_text as description
        ORDER BY amendment.amendment_date DESC
        """
    
    @staticmethod
    def get_amendments_by_law(jurabk: str) -> str:
        """
        Get all amendments for a specific law (e.g., 'SGB 7')
        
        Args:
            jurabk: Law abbreviation (e.g., 'SGB 7', 'SGB II')
            
        Returns:
            Cypher query string
        """
        return """
        MATCH (doc:LegalDocument {jurabk: $jurabk})-[:CONTAINS_NORM]->(norm:Norm)
        OPTIONAL MATCH (norm)-[:HAS_AMENDMENT]->(amendment:Amendment)
        WITH norm, amendment
        WHERE amendment IS NOT NULL
        RETURN 
            norm.enbez as paragraph,
            norm.titel as title,
            amendment.amendment_date as date,
            amendment.amendment_type as type,
            amendment.artikel as artikel,
            amendment.gesetz_ref as gesetz
        ORDER BY amendment.amendment_date DESC, norm.paragraph_nummer
        """
    
    @staticmethod
    def get_recent_amendments(days: int = 365) -> str:
        """
        Get all amendments from the last N days
        
        Args:
            days: Number of days to look back (default 365)
            
        Returns:
            Cypher query string
        """
        return """
        MATCH (amendment:Amendment)
        WHERE amendment.amendment_date >= date() - duration({days: $days})
        MATCH (norm:Norm)-[:HAS_AMENDMENT]->(amendment)
        OPTIONAL MATCH (doc:LegalDocument)-[:CONTAINS_NORM]->(norm)
        RETURN 
            doc.jurabk as law,
            norm.enbez as paragraph,
            amendment.amendment_date as date,
            amendment.artikel as artikel,
            amendment.gesetz_ref as gesetz,
            amendment.raw_text as description
        ORDER BY amendment.amendment_date DESC
        LIMIT 100
        """
    
    @staticmethod
    def get_amendment_timeline(doknr: str) -> str:
        """
        Get chronological timeline of amendments with superseded relationships
        
        Args:
            doknr: Document number
            
        Returns:
            Cypher query string
        """
        return """
        MATCH (norm:Norm {doknr: $doknr})-[:HAS_AMENDMENT]->(a1:Amendment)
        OPTIONAL MATCH (a1)-[:SUPERSEDED_BY*]->(a2:Amendment)
        RETURN 
            a1.amendment_date as original_date,
            a1.amendment_type as original_type,
            collect(DISTINCT {
                date: a2.amendment_date,
                type: a2.amendment_type,
                artikel: a2.artikel
            }) as superseding_amendments
        ORDER BY a1.amendment_date DESC
        """
    
    # ========== Law Impact Analysis Queries ==========
    
    @staticmethod
    def find_norms_by_gesetz(gesetz_ref: str) -> str:
        """
        Find all norms affected by a specific Gesetz
        
        Args:
            gesetz_ref: Gesetz reference (e.g., 'G v. 23.10.2024')
            
        Returns:
            Cypher query string
        """
        return """
        MATCH (norm:Norm)-[:HAS_AMENDMENT]->(amendment:Amendment)
        WHERE amendment.gesetz_ref CONTAINS $gesetz_ref
        OPTIONAL MATCH (doc:LegalDocument)-[:CONTAINS_NORM]->(norm)
        RETURN 
            doc.jurabk as law,
            norm.enbez as paragraph,
            norm.titel as title,
            amendment.amendment_date as date,
            amendment.artikel as artikel,
            amendment.gesetz_ref as gesetz,
            amendment.amendment_type as type
        ORDER BY doc.jurabk, norm.paragraph_nummer
        """
    
    @staticmethod
    def find_norms_by_artikel(artikel: str) -> str:
        """
        Find all norms affected by a specific Artikel
        
        Args:
            artikel: Artikel reference (e.g., 'Art. 66')
            
        Returns:
            Cypher query string
        """
        return """
        MATCH (norm:Norm)-[:HAS_AMENDMENT]->(amendment:Amendment {artikel: $artikel})
        OPTIONAL MATCH (doc:LegalDocument)-[:CONTAINS_NORM]->(norm)
        RETURN 
            doc.jurabk as law,
            norm.enbez as paragraph,
            norm.titel as title,
            amendment.amendment_date as date,
            amendment.gesetz_ref as gesetz
        ORDER BY amendment.amendment_date DESC
        """
    
    @staticmethod
    def get_law_impact_statistics() -> str:
        """
        Get statistics on which laws have been amended most
        
        Returns:
            Cypher query string
        """
        return """
        MATCH (doc:LegalDocument)-[:CONTAINS_NORM]->(norm:Norm)
        OPTIONAL MATCH (norm)-[:HAS_AMENDMENT]->(amendment:Amendment)
        WITH doc, COUNT(DISTINCT amendment) as amendment_count
        WHERE amendment_count > 0
        RETURN 
            doc.jurabk as law,
            doc.lange_titel as title,
            amendment_count,
            doc.ausfertigung_datum as original_date
        ORDER BY amendment_count DESC
        LIMIT 20
        """
    
    # ========== BGBl Queries ==========
    
    @staticmethod
    def get_norms_by_bgbl(bgbl_year: str, bgbl_issue: Optional[str] = None) -> str:
        """
        Find all norms published/amended in a specific BGBl issue
        
        Args:
            bgbl_year: Year of BGBl (e.g., '2024')
            bgbl_issue: Optional issue number (e.g., 'Nr. 323')
            
        Returns:
            Cypher query string
        """
        if bgbl_issue:
            return """
            MATCH (norm:Norm)-[:HAS_AMENDMENT]->(amendment:Amendment)
            WHERE amendment.bgbl_year = $bgbl_year 
              AND amendment.bgbl_issue = $bgbl_issue
            OPTIONAL MATCH (doc:LegalDocument)-[:CONTAINS_NORM]->(norm)
            RETURN 
                doc.jurabk as law,
                norm.enbez as paragraph,
                amendment.amendment_date as date,
                amendment.artikel as artikel,
                amendment.gesetz_ref as gesetz
            ORDER BY doc.jurabk, norm.paragraph_nummer
            """
        else:
            return """
            MATCH (norm:Norm)-[:HAS_AMENDMENT]->(amendment:Amendment {bgbl_year: $bgbl_year})
            OPTIONAL MATCH (doc:LegalDocument)-[:CONTAINS_NORM]->(norm)
            RETURN 
                doc.jurabk as law,
                norm.enbez as paragraph,
                amendment.amendment_date as date,
                amendment.bgbl_issue as issue,
                amendment.gesetz_ref as gesetz
            ORDER BY amendment.amendment_date DESC, doc.jurabk
            """
    
    @staticmethod
    def get_bgbl_references() -> str:
        """
        Get all BGBl reference nodes with counts
        
        Returns:
            Cypher query string
        """
        return """
        MATCH (bgbl:BGBl)
        OPTIONAL MATCH (norm:Norm)-[:PUBLISHED_IN]->(bgbl)
        WITH bgbl, COUNT(norm) as norm_count
        RETURN 
            bgbl.full_reference as reference,
            bgbl.year as year,
            bgbl.page as page,
            norm_count
        ORDER BY bgbl.year DESC, bgbl.page DESC
        """
    
    # ========== Version Tracking Queries ==========
    
    @staticmethod
    def get_norm_version_history(norm_doknr: str) -> str:
        """
        Get complete version history for a specific norm
        
        Args:
            norm_doknr: Norm document number
            
        Returns:
            Cypher query string
        """
        return """
        MATCH (norm:Norm {norm_doknr: $norm_doknr})
        OPTIONAL MATCH (norm)-[:HAS_AMENDMENT]->(amendment:Amendment)
        OPTIONAL MATCH (norm)-[:HAS_FUSSNOTE]->(fussnote:Fussnote)
        RETURN 
            norm.enbez as paragraph,
            norm.titel as title,
            collect(DISTINCT {
                date: amendment.amendment_date,
                type: amendment.amendment_type,
                description: amendment.raw_text
            }) as amendments,
            collect(DISTINCT {
                valid_from: fussnote.valid_from,
                in_kraft: fussnote.in_kraft,
                context: fussnote.context
            }) as version_notes
        ORDER BY amendment.amendment_date DESC
        """
    
    @staticmethod
    def get_active_norms_at_date(target_date: str) -> str:
        """
        Find which norms were active at a specific date
        
        Args:
            target_date: Date in ISO format (YYYY-MM-DD)
            
        Returns:
            Cypher query string
        """
        return """
        MATCH (norm:Norm)-[:HAS_FUSSNOTE]->(fussnote:Fussnote)
        WHERE fussnote.valid_from <= date($target_date)
          AND (fussnote.in_kraft IS NULL OR fussnote.in_kraft >= date($target_date))
        OPTIONAL MATCH (doc:LegalDocument)-[:CONTAINS_NORM]->(norm)
        RETURN 
            doc.jurabk as law,
            norm.enbez as paragraph,
            norm.titel as title,
            fussnote.valid_from as valid_from,
            fussnote.in_kraft as in_kraft
        ORDER BY doc.jurabk, norm.paragraph_nummer
        LIMIT 100
        """
    
    # ========== Search and Filter Queries ==========
    
    @staticmethod
    def search_amendments_by_text(search_term: str) -> str:
        """
        Full-text search across amendment descriptions
        
        Args:
            search_term: Term to search for
            
        Returns:
            Cypher query string
        """
        return """
        MATCH (norm:Norm)-[:HAS_AMENDMENT]->(amendment:Amendment)
        WHERE amendment.raw_text CONTAINS $search_term
           OR amendment.gesetz_ref CONTAINS $search_term
        OPTIONAL MATCH (doc:LegalDocument)-[:CONTAINS_NORM]->(norm)
        RETURN 
            doc.jurabk as law,
            norm.enbez as paragraph,
            amendment.amendment_date as date,
            amendment.raw_text as description
        ORDER BY amendment.amendment_date DESC
        LIMIT 50
        """
    
    @staticmethod
    def get_amendment_types_distribution() -> str:
        """
        Get distribution of amendment types across the knowledge graph
        
        Returns:
            Cypher query string
        """
        return """
        MATCH (amendment:Amendment)
        WITH amendment.amendment_type as type, COUNT(*) as count
        RETURN type, count
        ORDER BY count DESC
        """
    
    # ========== Validation Queries ==========
    
    @staticmethod
    def find_orphaned_amendments() -> str:
        """
        Find Amendment nodes not linked to any Norm
        
        Returns:
            Cypher query string
        """
        return """
        MATCH (amendment:Amendment)
        WHERE NOT (amendment)<-[:HAS_AMENDMENT]-()
        RETURN 
            amendment.amendment_date as date,
            amendment.raw_text as description
        ORDER BY amendment.amendment_date DESC
        LIMIT 50
        """
    
    @staticmethod
    def find_norms_without_amendments() -> str:
        """
        Find Norms that have no amendment history
        
        Returns:
            Cypher query string
        """
        return """
        MATCH (norm:Norm)
        WHERE NOT (norm)-[:HAS_AMENDMENT]->()
        OPTIONAL MATCH (doc:LegalDocument)-[:CONTAINS_NORM]->(norm)
        RETURN 
            doc.jurabk as law,
            norm.enbez as paragraph,
            norm.titel as title
        ORDER BY doc.jurabk, norm.paragraph_nummer
        LIMIT 100
        """
    
    @staticmethod
    def get_amendment_coverage_stats() -> str:
        """
        Get statistics on amendment coverage across the knowledge graph
        
        Returns:
            Cypher query string
        """
        return """
        MATCH (doc:LegalDocument)
        OPTIONAL MATCH (doc)-[:CONTAINS_NORM]->(norm:Norm)
        OPTIONAL MATCH (norm)-[:HAS_AMENDMENT]->(amendment:Amendment)
        WITH doc, 
             COUNT(DISTINCT norm) as total_norms,
             COUNT(DISTINCT amendment) as total_amendments,
             COUNT(DISTINCT CASE WHEN amendment IS NOT NULL THEN norm END) as norms_with_amendments
        RETURN 
            doc.jurabk as law,
            total_norms,
            norms_with_amendments,
            total_amendments,
            ROUND(100.0 * norms_with_amendments / total_norms, 2) as coverage_percent
        ORDER BY total_amendments DESC
        """


# Example usage
if __name__ == '__main__':
    from neo4j import GraphDatabase
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    print("=== Amendment Queries Module ===\n")
    
    # Example: Print some queries
    queries = AmendmentQueries()
    
    print("1. Get Amendment History Query:")
    print(queries.get_amendment_history("BJNR125410996"))
    print("\n" + "="*60 + "\n")
    
    print("2. Find Norms by Gesetz Query:")
    print(queries.find_norms_by_gesetz("G v. 23.10.2024"))
    print("\n" + "="*60 + "\n")
    
    print("3. Get Coverage Stats Query:")
    print(queries.get_amendment_coverage_stats())
    print("\n" + "="*60 + "\n")
    
    print("✅ All queries defined successfully!")
    print(f"\nTotal query methods: {len([m for m in dir(AmendmentQueries) if not m.startswith('_')])}")
