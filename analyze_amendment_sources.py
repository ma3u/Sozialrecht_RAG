#!/usr/bin/env python3
"""
Comprehensive XML Amendment Source Analysis

This script scans all XML files in xml_cache to identify and catalog
all locations where amendment information might be stored, including:
- standangabe/standkommentar
- fussnoten content
- enbez (possibly contains amendment references)
- metadaten fields
- any BGBl references

Purpose: Prepare for Phase 2 comprehensive re-scan to improve amendment coverage
"""

import os
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path
import re

def analyze_xml_file(filepath):
    """Extract all amendment-related information from an XML file"""
    try:
        tree = ET.parse(filepath)
        root = tree.getroot()
        
        findings = {
            'filepath': filepath,
            'standangabe_count': 0,
            'standkommentar_texts': [],
            'fussnoten_count': 0,
            'fussnoten_samples': [],
            'bgbl_references': [],
            'enbez_samples': [],
            'metadaten_count': 0
        }
        
        # Find standangabe elements
        for standangabe in root.findall('.//standangabe'):
            findings['standangabe_count'] += 1
            standkommentar = standangabe.find('standkommentar')
            if standkommentar is not None and standkommentar.text:
                findings['standkommentar_texts'].append(standkommentar.text)
        
        # Find fussnoten
        for fussnote in root.findall('.//fussnoten'):
            findings['fussnoten_count'] += 1
            # Get text content
            for content in fussnote.findall('.//Content'):
                if content.text:
                    text = ET.tostring(content, encoding='unicode', method='text')
                    if len(text) < 500:  # Only sample short fussnoten
                        findings['fussnoten_samples'].append(text[:200])
        
        # Find BGBl references
        for fundstelle in root.findall('.//fundstelle'):
            periodikum = fundstelle.find('periodikum')
            zitstelle = fundstelle.find('zitstelle')
            if periodikum is not None and 'BGBl' in (periodikum.text or ''):
                bgbl_ref = f"{periodikum.text} {zitstelle.text if zitstelle is not None else ''}"
                findings['bgbl_references'].append(bgbl_ref)
        
        # Find enbez (section titles that might reference amendments)
        for enbez in root.findall('.//enbez')[:5]:  # Sample first 5
            if enbez.text:
                findings['enbez_samples'].append(enbez.text)
        
        # Count metadaten sections
        findings['metadaten_count'] = len(root.findall('.//metadaten'))
        
        return findings
    
    except Exception as e:
        return {
            'filepath': filepath,
            'error': str(e)
        }

def main():
    xml_cache_dir = Path('/Users/ma3u/projects/sozialgesetze/Sozialrecht_RAG/xml_cache')
    
    if not xml_cache_dir.exists():
        print(f"Error: {xml_cache_dir} does not exist")
        return
    
    print("Scanning XML files for amendment data sources...")
    print("=" * 80)
    
    all_findings = []
    file_count = 0
    
    # Scan all XML files
    for xml_file in xml_cache_dir.rglob('*.xml'):
        file_count += 1
        findings = analyze_xml_file(xml_file)
        all_findings.append(findings)
        
        if file_count % 10 == 0:
            print(f"Processed {file_count} files...")
    
    print(f"\nTotal files processed: {file_count}")
    print("=" * 80)
    
    # Aggregate statistics
    total_standangabe = sum(f.get('standangabe_count', 0) for f in all_findings)
    total_fussnoten = sum(f.get('fussnoten_count', 0) for f in all_findings)
    total_bgbl = sum(len(f.get('bgbl_references', [])) for f in all_findings)
    total_metadaten = sum(f.get('metadaten_count', 0) for f in all_findings)
    
    print("\n📊 AGGREGATE STATISTICS")
    print("-" * 80)
    print(f"Total standangabe elements:     {total_standangabe}")
    print(f"Total fussnoten elements:       {total_fussnoten}")
    print(f"Total BGBl references:          {total_bgbl}")
    print(f"Total metadaten sections:       {total_metadaten}")
    
    # Sample standkommentar texts
    print("\n📝 SAMPLE STANDKOMMENTAR TEXTS (first 10)")
    print("-" * 80)
    standkommentar_samples = []
    for f in all_findings:
        standkommentar_samples.extend(f.get('standkommentar_texts', []))
    
    for i, text in enumerate(standkommentar_samples[:10], 1):
        print(f"{i}. {text}")
    
    # Sample BGBl references
    print("\n📚 SAMPLE BGBl REFERENCES (first 20)")
    print("-" * 80)
    bgbl_samples = []
    for f in all_findings:
        bgbl_samples.extend(f.get('bgbl_references', []))
    
    for i, ref in enumerate(bgbl_samples[:20], 1):
        print(f"{i}. {ref}")
    
    # Files with richest amendment data
    print("\n🏆 TOP 10 FILES BY AMENDMENT DATA RICHNESS")
    print("-" * 80)
    richness_scores = []
    for f in all_findings:
        if 'error' not in f:
            score = (
                f.get('standangabe_count', 0) * 10 +
                f.get('fussnoten_count', 0) * 5 +
                len(f.get('bgbl_references', [])) * 3
            )
            richness_scores.append((score, f['filepath']))
    
    richness_scores.sort(reverse=True)
    for i, (score, filepath) in enumerate(richness_scores[:10], 1):
        print(f"{i}. {Path(filepath).name} (score: {score})")
    
    # Detailed sample from richest file
    if richness_scores:
        richest_file = richness_scores[0][1]
        print(f"\n🔍 DETAILED SAMPLE FROM RICHEST FILE:")
        print(f"   {Path(richest_file).name}")
        print("-" * 80)
        
        for f in all_findings:
            if f.get('filepath') == richest_file:
                print(f"Standangabe count: {f.get('standangabe_count', 0)}")
                print(f"Fussnoten count: {f.get('fussnoten_count', 0)}")
                print(f"BGBl references: {len(f.get('bgbl_references', []))}")
                print("\nStandkommentar texts:")
                for text in f.get('standkommentar_texts', []):
                    print(f"  - {text}")
                print("\nBGBl references:")
                for ref in f.get('bgbl_references', []):
                    print(f"  - {ref}")
                break
    
    # Analysis of standkommentar patterns
    print("\n🔬 STANDKOMMENTAR PATTERN ANALYSIS")
    print("-" * 80)
    
    pattern_stats = {
        'has_date': 0,
        'has_artikel': 0,
        'has_gesetz': 0,
        'has_bgbl': 0,
        'has_geaendert': 0
    }
    
    for f in all_findings:
        for text in f.get('standkommentar_texts', []):
            if re.search(r'\d{1,2}\.\d{1,2}\.\d{4}', text):
                pattern_stats['has_date'] += 1
            if re.search(r'Art\.?\s*\d+', text, re.IGNORECASE):
                pattern_stats['has_artikel'] += 1
            if 'gesetz' in text.lower() or 'g v.' in text.lower():
                pattern_stats['has_gesetz'] += 1
            if 'bgbl' in text.lower():
                pattern_stats['has_bgbl'] += 1
            if 'geändert' in text.lower() or 'änder' in text.lower():
                pattern_stats['has_geaendert'] += 1
    
    print(f"Standkommentar texts with dates:     {pattern_stats['has_date']}")
    print(f"Standkommentar texts with Artikel:   {pattern_stats['has_artikel']}")
    print(f"Standkommentar texts with Gesetz:    {pattern_stats['has_gesetz']}")
    print(f"Standkommentar texts with BGBl:      {pattern_stats['has_bgbl']}")
    print(f"Standkommentar texts with 'geändert': {pattern_stats['has_geaendert']}")
    
    print("\n✅ Analysis complete!")
    print("=" * 80)
    print("\n💡 RECOMMENDATIONS FOR PHASE 2:")
    print("1. Parse standkommentar with regex to extract:")
    print("   - Amendment dates (DD.MM.YYYY format)")
    print("   - Artikel numbers (Art. X)")
    print("   - BGBl references")
    print("   - Law names (Gesetz vom...)")
    print("2. Parse fussnoten for historical context and version info")
    print("3. Cross-reference BGBl entries to build amendment timeline")
    print("4. Create explicit Amendment nodes with parsed metadata")
    print("5. Link amendments to affected norms with AMENDED_BY relationships")

if __name__ == '__main__':
    main()
