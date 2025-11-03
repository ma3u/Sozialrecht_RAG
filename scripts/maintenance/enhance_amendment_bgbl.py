#!/usr/bin/env python3
"""
Enhance existing amendments with BGBl references
Phase 1 of Amendment Improvement Strategy

This script extracts BGBl (Bundesgesetzblatt) references from existing
amendment standkommentar text and adds them as structured properties.

Examples:
    'durch Bek. v. 13.5.2011 I 850, 2094' → 'BGBl I 2011, 850'
    'durch Art. 2 G v. 24.2.2025 I Nr. 57' → 'BGBl I 2025, Nr. 57'
"""

import re
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from neo4j import GraphDatabase

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

load_dotenv()


def extract_bgbl_reference(text: str) -> tuple:
    """Extract BGBl reference from standkommentar text
    
    Args:
        text: Amendment standkommentar text
        
    Returns:
        Tuple of (bgbl_reference, fundstelle_periodikum) or (None, None)
        
    Examples:
        >>> extract_bgbl_reference('v. 13.5.2011 I 850, 2094')
        ('BGBl I 2011, 850', 'BGBl.2011.I')
        
        >>> extract_bgbl_reference('Art. 2 G v. 24.2.2025 I Nr. 57')
        ('BGBl I 2025, Nr. 57', 'BGBl.2025.I')
    """
    if not text:
        return None, None
    
    patterns = [
        # Pattern 1: "v. DD.MM.YYYY I \d+" (with page number)
        # Example: "v. 13.5.2011 I 850, 2094"
        (r'v\.\s*\d{1,2}\.\d{1,2}\.(\d{4})\s+I\s+(\d+)', 'page'),
        
        # Pattern 2: "v. DD.MM.YYYY I Nr. \d+" (with issue number)
        # Example: "v. 24.2.2025 I Nr. 57"
        (r'v\.\s*\d{1,2}\.\d{1,2}\.(\d{4})\s+I\s+Nr\.\s+(\d+)', 'issue'),
        
        # Pattern 3: "BGBl I YYYY, \d+" (direct BGBl reference)
        # Example: "BGBl I 2023, 1234"
        (r'BGBl\.?\s+I\s+(\d{4}),?\s+(\d+)', 'page'),
        
        # Pattern 4: "BGBl I YYYY Nr. \d+" (direct with Nr.)
        # Example: "BGBl I 2024 Nr. 245"
        (r'BGBl\.?\s+I\s+(\d{4})\s+Nr\.\s+(\d+)', 'issue'),
    ]
    
    for pattern, ref_type in patterns:
        match = re.search(pattern, text)
        if match:
            year = match.group(1)
            page_or_nr = match.group(2)
            
            if ref_type == 'issue':
                bgbl_ref = f"BGBl I {year}, Nr. {page_or_nr}"
            else:
                bgbl_ref = f"BGBl I {year}, {page_or_nr}"
            
            periodikum = f"BGBl.{year}.I"
            
            return bgbl_ref, periodikum
    
    return None, None


def extract_article_reference(text: str) -> str:
    """Extract article reference (e.g., 'Art. 2') from standkommentar
    
    Args:
        text: Amendment standkommentar text
        
    Returns:
        Article reference or None
        
    Examples:
        >>> extract_article_reference('Art. 2 G v. 24.2.2025 I Nr. 57')
        'Art. 2'
        
        >>> extract_article_reference('durch Art. 60 G v. 23.10.2024')
        'Art. 60'
    """
    if not text:
        return None
    
    pattern = r'Art\.\s+(\d+[a-z]*)'
    match = re.search(pattern, text)
    
    if match:
        return f"Art. {match.group(1)}"
    
    return None


def main():
    """Main execution function"""
    print("=" * 80)
    print("PHASE 1: Enhance Amendments with BGBl References")
    print("=" * 80)
    print()
    
    # Connect to Neo4j
    driver = GraphDatabase.driver(
        os.getenv('NEO4J_URI', 'bolt://localhost:7687'),
        auth=(
            os.getenv('NEO4J_USERNAME', 'neo4j'),
            os.getenv('NEO4J_PASSWORD', 'password')
        )
    )
    
    try:
        with driver.session() as session:
            # Get current statistics
            print("📊 Current Amendment Statistics:")
            result = session.run("""
                MATCH (a:Amendment)
                RETURN count(a) as total,
                       count(a.bgbl_reference) as with_bgbl,
                       count(a.fundstelle_periodikum) as with_periodikum
            """)
            stats = result.single()
            
            print(f"  Total Amendments: {stats['total']}")
            print(f"  With BGBl Reference: {stats['with_bgbl']}")
            print(f"  With Periodikum: {stats['with_periodikum']}")
            print()
            
            if stats['total'] == 0:
                print("⚠️  No amendments found in database!")
                print("   Run complete_knowledge_graph_import.py first")
                return
            
            # Get all amendments
            print("🔍 Processing amendments...")
            print()
            
            result = session.run("""
                MATCH (a:Amendment)
                RETURN elementId(a) as id, 
                       a.standkommentar as comment,
                       a.bgbl_reference as existing_bgbl
            """)
            
            amendments = list(result)
            enhanced = 0
            already_had = 0
            no_match = 0
            
            for record in amendments:
                comment = record['comment']
                element_id = record['id']
                existing_bgbl = record['existing_bgbl']
                
                # Skip if already has BGBl reference
                if existing_bgbl:
                    already_had += 1
                    continue
                
                # Extract BGBl reference
                bgbl_ref, periodikum = extract_bgbl_reference(comment)
                
                if bgbl_ref:
                    # Extract article reference
                    article_ref = extract_article_reference(comment)
                    
                    # Update amendment
                    session.run("""
                        MATCH (a:Amendment)
                        WHERE elementId(a) = $id
                        SET a.bgbl_reference = $bgbl_ref,
                            a.fundstelle_periodikum = $periodikum,
                            a.article_reference = $article_ref,
                            a.enhanced_at = datetime()
                    """, 
                    id=element_id, 
                    bgbl_ref=bgbl_ref, 
                    periodikum=periodikum,
                    article_ref=article_ref)
                    
                    enhanced += 1
                    print(f"✅ Enhanced: {bgbl_ref}")
                    if article_ref:
                        print(f"   Article: {article_ref}")
                    print(f"   Comment: {comment[:80]}...")
                    print()
                else:
                    no_match += 1
                    print(f"⚠️  No BGBl found: {comment[:80]}...")
                    print()
            
            print("=" * 80)
            print("📊 ENHANCEMENT SUMMARY")
            print("=" * 80)
            print(f"  ✅ Enhanced: {enhanced}")
            print(f"  ℹ️  Already had BGBl: {already_had}")
            print(f"  ⚠️  No match found: {no_match}")
            print(f"  📊 Total processed: {len(amendments)}")
            print()
            
            # Show final statistics
            result = session.run("""
                MATCH (a:Amendment)
                RETURN count(a) as total,
                       count(a.bgbl_reference) as with_bgbl,
                       count(a.fundstelle_periodikum) as with_periodikum,
                       count(a.article_reference) as with_article
            """)
            final_stats = result.single()
            
            print("📈 Final Statistics:")
            print(f"  Total Amendments: {final_stats['total']}")
            print(f"  With BGBl Reference: {final_stats['with_bgbl']} ({100*final_stats['with_bgbl']/final_stats['total']:.1f}%)")
            print(f"  With Periodikum: {final_stats['with_periodikum']} ({100*final_stats['with_periodikum']/final_stats['total']:.1f}%)")
            print(f"  With Article Ref: {final_stats['with_article']} ({100*final_stats['with_article']/final_stats['total']:.1f}%)")
            print()
            
            if enhanced > 0:
                print("🎉 SUCCESS! Phase 1 complete.")
                print()
                print("Next steps:")
                print("  1. Verify with: python scripts/evaluate_sachbearbeiter_use_cases.py")
                print("  2. Check UC20 (Änderungshistorie) for improvement")
                print("  3. Proceed to Phase 2 (Full XML re-scan)")
            else:
                print("ℹ️  All amendments already had BGBl references or no matches found.")
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        driver.close()


if __name__ == '__main__':
    main()
