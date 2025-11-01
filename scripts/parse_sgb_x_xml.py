#!/usr/bin/env python3
"""
Parse SGB X XML und extrahiere §§ 67-76

Liest die offizielle XML-Datei von gesetze-im-internet.de
und extrahiert die benötigten Paragraphen für UC14.

Usage:
    python scripts/parse_sgb_x_xml.py temp_data/BJNR114690980.xml
"""

import sys
import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path

class SGBXParser:
    """Parser für SGB X XML-Datei"""
    
    # Ziel-Paragraphen für UC14
    TARGET_PARAGRAPHS = [
        '67', '68', '69', '70', '71', '71a', '72', '73', '74', '75', '76'
    ]
    
    def __init__(self, xml_file: str):
        self.xml_file = xml_file
        self.tree = ET.parse(xml_file)
        self.root = self.tree.getroot()
    
    def clean_text(self, text: str) -> str:
        """Bereinigt XML-Text von überflüssigen Whitespaces"""
        if not text:
            return ""
        # Entferne mehrfache Leerzeichen und Zeilenumbrüche
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
    
    def extract_paragraph_text(self, norm_element) -> str:
        """Extrahiert den vollständigen Text eines Paragraphen"""
        textdaten = norm_element.find('.//textdaten')
        if textdaten is None:
            return ""
        
        # Extrahiere alle <P> Tags
        content = textdaten.find('.//Content')
        if content is None:
            return ""
        
        paragraphs = []
        for p in content.findall('.//P'):
            text = ''.join(p.itertext())
            text = self.clean_text(text)
            if text:
                paragraphs.append(text)
        
        return '\n\n'.join(paragraphs)
    
    def parse_paragraph_number(self, enbez: str) -> str:
        """Extrahiert Paragraph-Nummer aus enbez (z.B. '§ 67' -> '67')"""
        match = re.search(r'§\s*(\d+[a-z]?)', enbez)
        if match:
            return match.group(1)
        return ""
    
    def extract_paragraphs(self) -> list:
        """Extrahiert alle Ziel-Paragraphen aus der XML"""
        paragraphs = []
        
        for norm in self.root.findall('.//norm'):
            metadaten = norm.find('.//metadaten')
            if metadaten is None:
                continue
            
            enbez_elem = metadaten.find('enbez')
            if enbez_elem is None or enbez_elem.text is None:
                continue
            
            enbez = enbez_elem.text
            para_num = self.parse_paragraph_number(enbez)
            
            if para_num in self.TARGET_PARAGRAPHS:
                # Extrahiere Titel
                titel_elem = metadaten.find('titel')
                titel = titel_elem.text if titel_elem is not None else ""
                
                # Extrahiere Text
                text = self.extract_paragraph_text(norm)
                
                # doknr für Identifikation
                doknr = norm.get('builddate', '')
                
                paragraph_data = {
                    'paragraph': para_num,
                    'enbez': enbez,
                    'titel': titel,
                    'text': text,
                    'doknr': 'BJNR114690980',  # SGB X DOKNR
                    'sgb': 'X'
                }
                
                paragraphs.append(paragraph_data)
                print(f"✅ Extrahiert: {enbez} - {titel}")
                print(f"   Text-Länge: {len(text)} Zeichen")
        
        return paragraphs
    
    def save_as_json(self, paragraphs: list, output_file: str):
        """Speichert Paragraphen als JSON"""
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(paragraphs, f, indent=2, ensure_ascii=False)
        print(f"\n💾 Gespeichert: {output_file}")

def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/parse_sgb_x_xml.py <xml_file>")
        print("Example: python scripts/parse_sgb_x_xml.py temp_data/BJNR114690980.xml")
        sys.exit(1)
    
    xml_file = sys.argv[1]
    
    if not Path(xml_file).exists():
        print(f"❌ Datei nicht gefunden: {xml_file}")
        sys.exit(1)
    
    print("="*80)
    print("📖 SGB X XML Parser - Paragraphen 67-76")
    print("="*80)
    print(f"\n📄 Lese: {xml_file}")
    
    parser = SGBXParser(xml_file)
    
    print(f"\n🔍 Extrahiere Paragraphen {', '.join(['§'+p for p in parser.TARGET_PARAGRAPHS])}...")
    paragraphs = parser.extract_paragraphs()
    
    print(f"\n📊 Ergebnis:")
    print(f"   Gefunden: {len(paragraphs)}/{len(parser.TARGET_PARAGRAPHS)} Paragraphen")
    
    # Speichere als JSON
    output_file = "temp_data/sgb_x_paragraphs_67-76.json"
    parser.save_as_json(paragraphs, output_file)
    
    print(f"\n✅ Fertig! Daten bereit für Import.")
    print(f"\nNächster Schritt:")
    print(f"   python scripts/import_sgb_x_from_json.py {output_file}")

if __name__ == '__main__':
    main()
