#!/usr/bin/env python3
"""
Enhanced Amendment Parser for Legal XML
Extracts comprehensive amendment metadata from standkommentar, fussnoten, and BGBl references
"""

import re
from datetime import datetime, date
from typing import Dict, Optional, List
from dataclasses import dataclass, field
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class ParsedAmendment:
    """Comprehensive amendment data"""
    raw_text: str
    amendment_type: Optional[str] = None  # 'last_amended', 'reissued', 'indirect_amendment'
    amendment_date: Optional[date] = None
    artikel: Optional[str] = None
    gesetz_ref: Optional[str] = None
    bgbl_issue: Optional[str] = None
    bgbl_year: Optional[str] = None
    bgbl_full_ref: Optional[str] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for Neo4j"""
        return {
            'raw_text': self.raw_text,
            'amendment_type': self.amendment_type,
            'amendment_date': self.amendment_date.isoformat() if self.amendment_date else None,
            'artikel': self.artikel,
            'gesetz_ref': self.gesetz_ref,
            'bgbl_issue': self.bgbl_issue,
            'bgbl_year': self.bgbl_year,
            'bgbl_full_ref': self.bgbl_full_ref
        }


@dataclass
class ParsedFussnote:
    """Parsed fussnote (footnote) data"""
    valid_from: Optional[date] = None
    in_kraft: Optional[date] = None
    context: str = ""
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for Neo4j"""
        return {
            'valid_from': self.valid_from.isoformat() if self.valid_from else None,
            'in_kraft': self.in_kraft.isoformat() if self.in_kraft else None,
            'context': self.context[:300]  # Limit context length
        }


@dataclass
class ParsedBGBl:
    """Parsed BGBl reference"""
    id: str
    periodikum: str  # "BGBl I" or "BGBl II"
    year: str
    page: str
    full_reference: str
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for Neo4j"""
        return {
            'id': self.id,
            'periodikum': self.periodikum,
            'year': self.year,
            'page': self.page,
            'full_reference': self.full_reference
        }


class AmendmentParser:
    """Parse amendment data from XML metadata with comprehensive extraction"""
    
    # Regex patterns
    DATE_PATTERN = re.compile(r'(\d{1,2})\.(\d{1,2})\.(\d{4})')
    ARTIKEL_PATTERN = re.compile(r'Art\.?\s*(\d+[a-z]?)', re.IGNORECASE)
    GESETZ_PATTERN = re.compile(r'G\s+v\.\s+[^;]+')
    BGBL_ISSUE_PATTERN = re.compile(r'I\s+Nr\.\s+(\d+)')
    BGBL_REF_PATTERN = re.compile(r'BGBl\s+(I{1,3})\s+(\d{4}),\s*(\d+)')
    
    @staticmethod
    def parse_standkommentar(text: str) -> Optional[ParsedAmendment]:
        """
        Parse standkommentar text to extract comprehensive amendment metadata
        
        Args:
            text: Standkommentar text from XML
            
        Returns:
            ParsedAmendment object or None
            
        Examples:
            >>> parser = AmendmentParser()
            >>> result = parser.parse_standkommentar("Zuletzt geändert durch Art. 66 G v. 23.10.2024 I Nr. 323")
            >>> result.amendment_date
            datetime.date(2024, 10, 23)
            >>> result.artikel
            'Art. 66'
        """
        if not text or not text.strip():
            return None
        
        result = ParsedAmendment(raw_text=text)
        
        # Determine amendment type
        text_lower = text.lower()
        if 'zuletzt geändert' in text_lower or 'zuletzt durch' in text_lower:
            result.amendment_type = 'last_amended'
        elif 'neugefasst' in text_lower or 'neuf' in text_lower:
            result.amendment_type = 'reissued'
        elif 'mittelbare änderung' in text_lower:
            result.amendment_type = 'indirect_amendment'
        elif 'ergänzung' in text_lower:
            result.amendment_type = 'supplement'
        else:
            result.amendment_type = 'other'
        
        # Extract date (DD.MM.YYYY)
        date_match = AmendmentParser.DATE_PATTERN.search(text)
        if date_match:
            day, month, year = date_match.groups()
            try:
                result.amendment_date = date(int(year), int(month), int(day))
                result.bgbl_year = year
            except ValueError as e:
                logger.warning(f"Invalid date in standkommentar: {date_match.group(0)} - {e}")
        
        # Extract Artikel
        artikel_match = AmendmentParser.ARTIKEL_PATTERN.search(text)
        if artikel_match:
            result.artikel = f"Art. {artikel_match.group(1)}"
        
        # Extract Gesetz reference
        gesetz_match = AmendmentParser.GESETZ_PATTERN.search(text)
        if gesetz_match:
            result.gesetz_ref = gesetz_match.group(0).strip()
        
        # Extract BGBl issue number
        issue_match = AmendmentParser.BGBL_ISSUE_PATTERN.search(text)
        if issue_match:
            result.bgbl_issue = f"Nr. {issue_match.group(1)}"
        
        # Extract full BGBl reference if present
        bgbl_match = AmendmentParser.BGBL_REF_PATTERN.search(text)
        if bgbl_match:
            periodikum_suffix = bgbl_match.group(1)
            year = bgbl_match.group(2)
            page = bgbl_match.group(3)
            result.bgbl_full_ref = f"BGBl {periodikum_suffix} {year}, {page}"
        
        return result
    
    @staticmethod
    def parse_fussnote(fussnote_text: str) -> Optional[ParsedFussnote]:
        """
        Parse fussnote text for version and historical info
        
        Args:
            fussnote_text: Text content from fussnoten element
            
        Returns:
            ParsedFussnote object or None
            
        Examples:
            >>> parser = AmendmentParser()
            >>> result = parser.parse_fussnote("Textnachweis ab: 21.8.1996")
            >>> result.valid_from
            datetime.date(1996, 8, 21)
        """
        if not fussnote_text or not fussnote_text.strip():
            return None
        
        result = ParsedFussnote(context=fussnote_text[:300])
        
        # Extract "ab: DD.MM.YYYY" patterns
        ab_match = re.search(r'ab:?\s*(\d{1,2})\.(\d{1,2})\.(\d{4})', fussnote_text)
        if ab_match:
            day, month, year = ab_match.groups()
            try:
                result.valid_from = date(int(year), int(month), int(day))
            except ValueError as e:
                logger.warning(f"Invalid 'valid_from' date in fussnote: {ab_match.group(0)} - {e}")
        
        # Extract "in Kraft" patterns
        kraft_match = re.search(r'in\s+Kraft.*?(\d{1,2})\.(\d{1,2})\.(\d{4})', fussnote_text, re.IGNORECASE)
        if kraft_match:
            day, month, year = kraft_match.groups()
            try:
                result.in_kraft = date(int(year), int(month), int(day))
            except ValueError as e:
                logger.warning(f"Invalid 'in_kraft' date in fussnote: {kraft_match.group(0)} - {e}")
        
        # Return None if no useful data extracted
        if result.valid_from is None and result.in_kraft is None:
            return None
        
        return result
    
    @staticmethod
    def parse_bgbl_reference(periodikum: str, zitstelle: str) -> Optional[ParsedBGBl]:
        """
        Parse BGBl reference into structured format
        
        Args:
            periodikum: "BGBl I" or "BGBl II"
            zitstelle: "1996, 1254"
            
        Returns:
            ParsedBGBl object or None
            
        Examples:
            >>> parser = AmendmentParser()
            >>> result = parser.parse_bgbl_reference("BGBl I", "1996, 1254")
            >>> result.id
            'bgbl_1996_1254'
        """
        if not periodikum or not zitstelle:
            return None
        
        # Parse year and page from zitstelle
        year_page_match = re.match(r'(\d{4}),\s*(\d+)', zitstelle)
        if not year_page_match:
            return None
        
        year, page = year_page_match.groups()
        
        return ParsedBGBl(
            id=f"bgbl_{year}_{page}",
            periodikum=periodikum,
            year=year,
            page=page,
            full_reference=f"{periodikum} {zitstelle}"
        )
    
    @staticmethod
    def extract_all_amendments_from_text(text: str) -> List[ParsedAmendment]:
        """
        Extract multiple amendments from text that may contain historical changes
        
        Args:
            text: Text potentially containing multiple amendment references
            
        Returns:
            List of ParsedAmendment objects
        """
        amendments = []
        
        # Split on semicolons which often separate multiple amendments
        parts = text.split(';')
        
        for part in parts:
            part = part.strip()
            if part:
                amendment = AmendmentParser.parse_standkommentar(part)
                if amendment and amendment.amendment_date:
                    amendments.append(amendment)
        
        # Sort by date (most recent first)
        amendments.sort(key=lambda a: a.amendment_date, reverse=True)
        
        return amendments


# Example usage and testing
if __name__ == '__main__':
    parser = AmendmentParser()
    
    print("=== Testing Amendment Parser ===\n")
    
    # Test 1: Standard amendment
    test1 = "Zuletzt geändert durch Art. 66 G v. 23.10.2024 I Nr. 323"
    print(f"Test 1: {test1}")
    result1 = parser.parse_standkommentar(test1)
    if result1:
        print(f"  Type: {result1.amendment_type}")
        print(f"  Date: {result1.amendment_date}")
        print(f"  Artikel: {result1.artikel}")
        print(f"  Gesetz: {result1.gesetz_ref}")
        print(f"  BGBl Issue: {result1.bgbl_issue}")
        print(f"  Dict: {result1.to_dict()}")
    print()
    
    # Test 2: Reissued
    test2 = "Neugefasst durch Bek. v. 19.2.2002 I 754, 1404, 3384"
    print(f"Test 2: {test2}")
    result2 = parser.parse_standkommentar(test2)
    if result2:
        print(f"  Type: {result2.amendment_type}")
        print(f"  Date: {result2.amendment_date}")
    print()
    
    # Test 3: Fussnote
    test3 = "(+++ Textnachweis ab: 21.8.1996 +++)"
    print(f"Test 3: {test3}")
    result3 = parser.parse_fussnote(test3)
    if result3:
        print(f"  Valid from: {result3.valid_from}")
        print(f"  Context: {result3.context}")
        print(f"  Dict: {result3.to_dict()}")
    print()
    
    # Test 4: BGBl reference
    test4_periodikum = "BGBl I"
    test4_zitstelle = "1996, 1254"
    print(f"Test 4: {test4_periodikum} {test4_zitstelle}")
    result4 = parser.parse_bgbl_reference(test4_periodikum, test4_zitstelle)
    if result4:
        print(f"  ID: {result4.id}")
        print(f"  Full ref: {result4.full_reference}")
        print(f"  Dict: {result4.to_dict()}")
    print()
    
    # Test 5: Multiple amendments
    test5 = "Zuletzt geändert durch Art. 11 G v. 18.12.2024 I Nr. 423; Neugefasst durch Bek. v. 19.2.2002 I 754"
    print(f"Test 5: Multiple amendments")
    results5 = parser.extract_all_amendments_from_text(test5)
    print(f"  Found {len(results5)} amendments:")
    for i, amend in enumerate(results5, 1):
        print(f"    {i}. {amend.amendment_date} - {amend.amendment_type}")
    
    print("\n✅ Amendment Parser tests complete!")
