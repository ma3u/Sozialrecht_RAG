"""
Legal XML Parser for gesetze-im-internet.de XML format
Parses legal XML structure into Python objects for Neo4j import
"""

import logging
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass, field
from lxml import etree
from datetime import datetime, date
import hashlib
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class Amendment:
    """Amendment history entry"""
    id: str
    standtyp: str  # "Neuf" or "Stand"
    standkommentar: str
    amendment_date: Optional[date] = None
    bgbl_reference: Optional[str] = None


@dataclass
class ListItem:
    """List item (enumeration)"""
    id: str
    list_type: str  # "arabic", "alpha", "roman"
    term: str  # DT content
    definition: str  # DD/LA content
    order_index: int


@dataclass
class TextUnit:
    """Text content unit (Absatz, paragraph)"""
    id: str
    type: str  # "Paragraph", "List", "Table"
    text: str
    absatz_nummer: Optional[str] = None
    order_index: int = 0
    list_items: List[ListItem] = field(default_factory=list)


@dataclass
class LegalNorm:
    """Legal Norm (§ paragraph)"""
    id: str
    norm_doknr: str
    enbez: str  # § label
    paragraph_nummer: str  # Normalized number
    titel: str
    content_text: str
    has_footnotes: bool
    order_index: int
    text_units: List[TextUnit] = field(default_factory=list)
    amendments: List[Amendment] = field(default_factory=list)
    gliederung: Optional[Dict] = None


@dataclass
class StructuralUnit:
    """Structural unit (Chapter, Section)"""
    id: str
    gliederungskennzahl: str
    gliederungsbez: str
    gliederungstitel: str
    level: int
    order_index: int


@dataclass
class LegalDocument:
    """Root legal document"""
    id: str
    doknr: str
    builddate: datetime
    jurabk: str
    lange_titel: Optional[str] = None
    sgb_nummer: Optional[str] = None
    ausfertigung_datum: Optional[date] = None
    fundstelle: Optional[str] = None
    trust_score: int = 100
    source_type: str = "XML_OFFICIAL"
    xml_source_url: Optional[str] = None
    norms: List[LegalNorm] = field(default_factory=list)
    structures: List[StructuralUnit] = field(default_factory=list)


class LegalXMLParser:
    """Parse legal XML structure using neo4j-graphrag"""
    
    def __init__(self):
        """Initialize parser"""
        logger.info("✅ Legal XML Parser initialized")
    
    def parse_dokument(self, xml_path: Path) -> LegalDocument:
        """Extract root document metadata
        
        Args:
            xml_path: Path to XML file
            
        Returns:
            LegalDocument object
        """
        with open(xml_path, 'rb') as f:
            xml_content = f.read()
        
        root = etree.fromstring(xml_content)
        
        # Extract root attributes
        doknr = root.get('doknr', 'UNKNOWN')
        builddate_str = root.get('builddate', '')
        builddate = self._parse_builddate(builddate_str)
        
        # Generate document ID
        doc_id = hashlib.sha256(f"{doknr}_{builddate_str}".encode()).hexdigest()[:16]
        
        # Extract jurabk from first norm
        jurabk = None
        lange_titel = None
        ausfertigung_datum = None
        fundstelle = None
        
        first_norm = root.find('.//norm')
        if first_norm is not None:
            metadaten = first_norm.find('metadaten')
            if metadaten is not None:
                jurabk_elem = metadaten.find('jurabk')
                if jurabk_elem is not None:
                    jurabk = jurabk_elem.text
                
                titel_elem = metadaten.find('langue')
                if titel_elem is not None:
                    lange_titel = titel_elem.text
                
                ausf_datum = metadaten.find('ausfertigung-datum')
                if ausf_datum is not None:
                    ausfertigung_datum = self._parse_date(ausf_datum.get('manuell') or ausf_datum.text)
                
                fundst = metadaten.find('fundstelle')
                if fundst is not None:
                    periodikum = fundst.find('periodikum')
                    zitstelle = fundst.find('zitstelle')
                    if periodikum is not None and zitstelle is not None:
                        fundstelle = f"{periodikum.text} {zitstelle.text}"
        
        # Extract SGB number from jurabk
        sgb_nummer = self._extract_sgb_nummer(jurabk)
        
        # Construct source URL
        xml_source_url = None
        if sgb_nummer:
            # Construct URL directly without xml_downloader dependency
            xml_source_url = f"https://www.gesetze-im-internet.de/sgb_{sgb_nummer.lower()}/xml.zip"
        
        document = LegalDocument(
            id=doc_id,
            doknr=doknr,
            builddate=builddate,
            jurabk=jurabk or "UNKNOWN",
            lange_titel=lange_titel,
            sgb_nummer=sgb_nummer,
            ausfertigung_datum=ausfertigung_datum,
            fundstelle=fundstelle,
            xml_source_url=xml_source_url
        )
        
        # Parse all norms
        document.norms = self.parse_norms(root)
        
        # Parse structures
        document.structures = self._extract_structures(root)
        
        logger.info(f"✅ Parsed document: {jurabk} ({len(document.norms)} norms, {len(document.structures)} structures)")
        
        return document
    
    def parse_norms(self, xml_root) -> List[LegalNorm]:
        """Extract all <norm> elements with structure
        
        Args:
            xml_root: XML root element
            
        Returns:
            List of LegalNorm objects
        """
        norms = []
        
        for idx, norm_elem in enumerate(xml_root.findall('.//norm')):
            norm_doknr = norm_elem.get('doknr', f'NORM_{idx}')
            
            metadaten = norm_elem.find('metadaten')
            if metadaten is None:
                continue
            
            # Extract basic metadata
            enbez_elem = metadaten.find('enbez')
            enbez = enbez_elem.text if enbez_elem is not None else f"Norm {idx}"
            
            titel_elem = metadaten.find('titel')
            titel = titel_elem.text if titel_elem is not None else ""
            
            # Extract paragraph number
            paragraph_nummer = self._extract_paragraph_nummer(enbez)
            
            # Extract gliederung
            gliederung = self.extract_gliederung(metadaten)
            
            # Extract amendments
            amendments = self.extract_amendments(metadaten)
            
            # Parse text content
            textdaten = norm_elem.find('textdaten')
            text_units = []
            content_text = ""
            has_footnotes = False
            
            if textdaten is not None:
                text_units = self.parse_textdaten(textdaten, norm_doknr)
                content_text = " ".join(tu.text for tu in text_units)
                
                # Check for footnotes
                fussnoten = textdaten.find('fussnoten')
                has_footnotes = fussnoten is not None
            
            # Generate norm ID
            norm_id = hashlib.sha256(f"{norm_doknr}_{enbez}".encode()).hexdigest()[:16]
            
            norm = LegalNorm(
                id=norm_id,
                norm_doknr=norm_doknr,
                enbez=enbez,
                paragraph_nummer=paragraph_nummer,
                titel=titel,
                content_text=content_text,
                has_footnotes=has_footnotes,
                order_index=idx,
                text_units=text_units,
                amendments=amendments,
                gliederung=gliederung
            )
            
            norms.append(norm)
        
        logger.info(f"✅ Parsed {len(norms)} norms")
        return norms
    
    def extract_gliederung(self, metadaten) -> Optional[Dict]:
        """Parse <gliederungseinheit> hierarchy
        
        Args:
            metadaten: metadaten XML element
            
        Returns:
            Dictionary with gliederung info or None
        """
        gliederung_elem = metadaten.find('gliederungseinheit')
        if gliederung_elem is None:
            return None
        
        kennzahl = gliederung_elem.find('gliederungskennzahl')
        bez = gliederung_elem.find('gliederungsbez')
        titel = gliederung_elem.find('gliederungstitel')
        
        return {
            'kennzahl': kennzahl.text if kennzahl is not None else None,
            'bez': bez.text if bez is not None else None,
            'titel': titel.text if titel is not None else None
        }
    
    def parse_textdaten(self, textdaten, norm_doknr: str) -> List[TextUnit]:
        """Extract <Content><P>, <DL>, <table> elements
        
        Args:
            textdaten: textdaten XML element
            norm_doknr: Parent norm doknr
            
        Returns:
            List of TextUnit objects
        """
        text_units = []
        
        text_elem = textdaten.find('text')
        if text_elem is None:
            return text_units
        
        content_elem = text_elem.find('Content')
        if content_elem is None:
            return text_units
        
        order_idx = 0
        
        for child in content_elem:
            if child.tag == 'P':
                # Paragraph
                text = self._extract_text_recursive(child)
                if text.strip():
                    text_unit_id = hashlib.sha256(f"{norm_doknr}_P_{order_idx}".encode()).hexdigest()[:16]
                    text_units.append(TextUnit(
                        id=text_unit_id,
                        type="Paragraph",
                        text=text,
                        order_index=order_idx
                    ))
                    order_idx += 1
            
            elif child.tag == 'DL':
                # Definition/Enumeration List
                list_type = child.get('Type', 'arabic')
                list_items = self._parse_list_items(child, norm_doknr, order_idx)
                
                # Create text unit for the list
                list_text = " ".join(f"{item.term} {item.definition}" for item in list_items)
                text_unit_id = hashlib.sha256(f"{norm_doknr}_DL_{order_idx}".encode()).hexdigest()[:16]
                
                text_units.append(TextUnit(
                    id=text_unit_id,
                    type="List",
                    text=list_text,
                    order_index=order_idx,
                    list_items=list_items
                ))
                order_idx += 1
            
            elif child.tag == 'table':
                # Table (simplified extraction)
                table_text = self._extract_text_recursive(child)
                if table_text.strip():
                    text_unit_id = hashlib.sha256(f"{norm_doknr}_TABLE_{order_idx}".encode()).hexdigest()[:16]
                    text_units.append(TextUnit(
                        id=text_unit_id,
                        type="Table",
                        text=table_text,
                        order_index=order_idx
                    ))
                    order_idx += 1
        
        return text_units
    
    def _parse_list_items(self, dl_elem, norm_doknr: str, base_idx: int) -> List[ListItem]:
        """Parse DL/DT/DD list items"""
        list_items = []
        list_type = dl_elem.get('Type', 'arabic')
        
        dt_elements = dl_elem.findall('DT')
        dd_elements = dl_elem.findall('DD')
        
        for idx, (dt, dd) in enumerate(zip(dt_elements, dd_elements)):
            term = self._extract_text_recursive(dt)
            definition = self._extract_text_recursive(dd)
            
            item_id = hashlib.sha256(f"{norm_doknr}_LIST_{base_idx}_{idx}".encode()).hexdigest()[:16]
            
            list_items.append(ListItem(
                id=item_id,
                list_type=list_type,
                term=term,
                definition=definition,
                order_index=idx
            ))
        
        return list_items
    
    def extract_amendments(self, metadaten) -> List[Amendment]:
        """Parse amendment history
        
        Args:
            metadaten: metadaten XML element
            
        Returns:
            List of Amendment objects
        """
        amendments = []
        
        for standangabe in metadaten.findall('standangabe'):
            checked = standangabe.get('checked') == 'ja'
            
            standtyp_elem = standangabe.find('standtyp')
            standkommentar_elem = standangabe.find('standkommentar')
            
            if standtyp_elem is None or standkommentar_elem is None:
                continue
            
            standtyp = standtyp_elem.text
            standkommentar = standkommentar_elem.text
            
            # Try to extract date from standkommentar
            amendment_date = self._extract_date_from_text(standkommentar)
            
            # Try to extract BGBl reference
            bgbl_ref = self._extract_bgbl_reference(standkommentar)
            
            amendment_id = hashlib.sha256(f"{standtyp}_{standkommentar}".encode()).hexdigest()[:16]
            
            amendments.append(Amendment(
                id=amendment_id,
                standtyp=standtyp,
                standkommentar=standkommentar,
                amendment_date=amendment_date,
                bgbl_reference=bgbl_ref
            ))
        
        return amendments
    
    def _extract_structures(self, xml_root) -> List[StructuralUnit]:
        """Extract structural units (chapters, sections)"""
        structures = []
        seen_structures = set()
        
        for idx, norm_elem in enumerate(xml_root.findall('.//norm')):
            metadaten = norm_elem.find('metadaten')
            if metadaten is None:
                continue
            
            gliederung = metadaten.find('gliederungseinheit')
            if gliederung is None:
                continue
            
            kennzahl_elem = gliederung.find('gliederungskennzahl')
            bez_elem = gliederung.find('gliederungsbez')
            titel_elem = gliederung.find('gliederungstitel')
            
            if kennzahl_elem is None:
                continue
            
            kennzahl = kennzahl_elem.text
            bez = bez_elem.text if bez_elem is not None else ""
            titel = titel_elem.text if titel_elem is not None else ""
            
            # Avoid duplicates
            struct_key = f"{kennzahl}_{bez}"
            if struct_key in seen_structures:
                continue
            seen_structures.add(struct_key)
            
            # Determine level from bez (Kapitel=1, Abschnitt=2, etc.)
            level = self._determine_structure_level(bez)
            
            struct_id = hashlib.sha256(struct_key.encode()).hexdigest()[:16]
            
            structures.append(StructuralUnit(
                id=struct_id,
                gliederungskennzahl=kennzahl,
                gliederungsbez=bez,
                gliederungstitel=titel,
                level=level,
                order_index=len(structures)
            ))
        
        return structures
    
    # Helper methods
    
    def _extract_text_recursive(self, elem) -> str:
        """Recursively extract all text from element"""
        texts = []
        if elem.text:
            texts.append(elem.text)
        for child in elem:
            texts.append(self._extract_text_recursive(child))
            if child.tail:
                texts.append(child.tail)
        return " ".join(texts).strip()
    
    def _parse_builddate(self, builddate_str: str) -> datetime:
        """Parse builddate from YYYYMMDDHHMMSS format"""
        try:
            return datetime.strptime(builddate_str, "%Y%m%d%H%M%S")
        except (ValueError, TypeError):
            return datetime.now()
    
    def _parse_date(self, date_str: str) -> Optional[date]:
        """Parse date from YYYY-MM-DD format"""
        if not date_str:
            return None
        try:
            return datetime.strptime(date_str, "%Y-%m-%d").date()
        except (ValueError, TypeError):
            return None
    
    def _extract_sgb_nummer(self, jurabk: Optional[str]) -> Optional[str]:
        """Extract SGB number (I-XIV) from jurabk"""
        if not jurabk:
            return None
        
        # Match "SGB 2", "SGB II", "SGB-2", etc.
        match = re.search(r'SGB\s*([IVX]+|\d+)', jurabk, re.IGNORECASE)
        if match:
            num_str = match.group(1)
            # Convert Arabic to Roman if needed
            arabic_to_roman = {
                '1': 'I', '2': 'II', '3': 'III', '4': 'IV', '5': 'V',
                '6': 'VI', '7': 'VII', '8': 'VIII', '9': 'IX', '10': 'X',
                '11': 'XI', '12': 'XII', '14': 'XIV'
            }
            return arabic_to_roman.get(num_str, num_str.upper())
        
        return None
    
    def _extract_paragraph_nummer(self, enbez: str) -> str:
        """Extract normalized paragraph number from enbez"""
        # Remove § and whitespace
        cleaned = enbez.replace('§', '').strip()
        # Extract number part (handles "20", "11a", etc.)
        match = re.match(r'(\d+[a-z]?)', cleaned)
        if match:
            return match.group(1)
        return cleaned
    
    def _extract_date_from_text(self, text: str) -> Optional[date]:
        """Extract date from text like 'Neufassung durch Art. 1 G v. 24.12.2003'"""
        # Match German date format DD.MM.YYYY
        match = re.search(r'(\d{1,2})\.(\d{1,2})\.(\d{4})', text)
        if match:
            try:
                day, month, year = match.groups()
                return date(int(year), int(month), int(day))
            except ValueError:
                return None
        return None
    
    def _extract_bgbl_reference(self, text: str) -> Optional[str]:
        """Extract BGBl reference from text"""
        match = re.search(r'BGBl\s+[^\s]+\s+[\d,\s]+', text)
        if match:
            return match.group(0)
        return None
    
    def _determine_structure_level(self, bez: str) -> int:
        """Determine hierarchy level from gliederungsbez"""
        bez_lower = bez.lower()
        if 'kapitel' in bez_lower:
            return 1
        elif 'abschnitt' in bez_lower:
            return 2
        elif 'unterabschnitt' in bez_lower:
            return 3
        elif 'titel' in bez_lower:
            return 4
        else:
            return 5


if __name__ == "__main__":
    # Test the parser
    from xml_downloader import GIIXMLDownloader
    
    print("\n=== Testing Legal XML Parser ===")
    
    # Download SGB II
    downloader = GIIXMLDownloader()
    xml_path = downloader.download_law_xml("II")
    
    # Parse
    parser = LegalXMLParser()
    document = parser.parse_dokument(xml_path)
    
    print(f"\nDocument: {document.jurabk}")
    print(f"SGB Number: {document.sgb_nummer}")
    print(f"Doknr: {document.doknr}")
    print(f"Build Date: {document.builddate}")
    print(f"Norms: {len(document.norms)}")
    print(f"Structures: {len(document.structures)}")
    
    # Show first norm
    if document.norms:
        norm = document.norms[0]
        print(f"\nFirst Norm: {norm.enbez} - {norm.titel}")
        print(f"Paragraph: {norm.paragraph_nummer}")
        print(f"Text Units: {len(norm.text_units)}")
        print(f"Amendments: {len(norm.amendments)}")
