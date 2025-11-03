# Amendment Improvement Strategy

**Date:** November 3, 2025  
**Current Coverage:** 0.5% (21 amendments for 4,223 norms)  
**Target Coverage:** 80%+ (3,378+ amendments)  
**Priority:** P2 (Medium-High)

---

## 📊 Current Situation Analysis

### What We Have Now

| Metric | Count | Coverage |
|--------|-------|----------|
| **Total Legal Norms** | 4,223 | 100% |
| **Norms with Amendments** | 13 | 0.3% |
| **Total Amendments** | 21 | - |
| **Amendments with Dates** | 21 | 100% |
| **Amendments with BGBl Refs** | 0 | 0% |

### Quality of Existing Data

✅ **Good:**
- All 21 amendments have dates
- All have standkommentar (description text)
- Dates are properly parsed and structured

❌ **Missing:**
- **BGBl references** (Bundesgesetzblatt - official legal gazette)
- **Coverage** is extremely low (99.7% of norms have no amendment data)
- **Historical version chains** (SUPERSEDES relationships)

### Sample Amendment Data

```
§ Norm 0: "Neugefasst durch Bek. v. 13.5.2011 I 850, 2094"
Date: 2011-05-13

§ Norm 0: "zuletzt geändert durch Art. 2 G v. 24.2.2025 I Nr. 57"
Date: 2025-02-24

§ Norm 0: "Zuletzt geändert durch Art. 60 G v. 23.10.2024 I Nr. 323"
Date: 2024-10-23
```

**Observation:** The standkommentar contains BGBl references but they're not extracted!
- `"I 850"` = BGBl I, Page 850
- `"I Nr. 57"` = BGBl I, Number 57
- `"I Nr. 323"` = BGBl I, Number 323

---

## 🎯 Root Cause Analysis

### Why Coverage is Only 0.5%

#### 1. **XML Source Limitation** (Primary Cause)
The gesetze-im-internet.de XML files only contain **current valid text**, not historical versions.

**Evidence:**
- Each SGB XML file = current snapshot
- `<standangabe>` elements are sparse
- Only major amendments are documented in XML

**Impact:** We can only extract amendments that are explicitly documented in the `<metadaten><standangabe>` tags.

#### 2. **Incomplete Parsing** (Secondary Cause)
The current parser (`xml_legal_parser.py`) extracts amendments, but:
- BGBl references are not being extracted (regex missing)
- Only processes `<standangabe>` elements
- Doesn't look in other XML locations where dates might be

#### 3. **No External Data Source**
We're not leveraging external amendment databases:
- BGBl online archive (https://www.bgbl.de)
- Dokumentations- und Informationssystem (DIP) of Bundestag
- buzer.de API (commercial but comprehensive)

---

## 🚀 Improvement Strategy

### Phase 1: Extract BGBl References from Existing Data (Quick Win)

**Goal:** Enhance 21 existing amendments with BGBl references  
**Effort:** 2-3 hours  
**Impact:** Better amendment quality, foundation for linking

#### Implementation

1. **Update `xml_legal_parser.py`** to extract BGBl references:

```python
def _extract_bgbl_reference(self, text: str) -> Optional[str]:
    """Extract BGBl reference from standkommentar
    
    Examples:
        'durch Bek. v. 13.5.2011 I 850, 2094' → 'BGBl I 2011, 850'
        'durch Art. 2 G v. 24.2.2025 I Nr. 57' → 'BGBl I 2025, Nr. 57'
        'Art. 60 G v. 23.10.2024 I Nr. 323' → 'BGBl I 2024, Nr. 323'
    """
    import re
    
    patterns = [
        # Pattern: "v. DD.MM.YYYY I \d+"
        r'v\.\s*(\d{1,2})\.(\d{1,2})\.(\d{4})\s+I\s+(\d+)',
        # Pattern: "v. DD.MM.YYYY I Nr. \d+"
        r'v\.\s*(\d{1,2})\.(\d{1,2})\.(\d{4})\s+I\s+Nr\.\s+(\d+)',
        # Pattern: "BGBl I YYYY, \d+"
        r'BGBl\.?\s+I\s+(\d{4}),?\s+(\d+)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            groups = match.groups()
            if len(groups) == 4:
                # DD.MM.YYYY I NNN format
                day, month, year, page_or_nr = groups
                return f"BGBl I {year}, {page_or_nr}"
            elif len(groups) == 2:
                # BGBl I YYYY, NNN format
                year, page_or_nr = groups
                return f"BGBl I {year}, {page_or_nr}"
    
    return None
```

2. **Update Amendment model** with fundstelle_periodikum:

```python
@dataclass
class Amendment:
    id: str
    standtyp: str
    standkommentar: str
    amendment_date: Optional[date] = None
    bgbl_reference: Optional[str] = None  # Add this
    fundstelle_periodikum: Optional[str] = None  # Add this
    fundstelle_zitstelle: Optional[str] = None  # Add this
```

3. **Create migration script** to update existing amendments:

```bash
python scripts/maintenance/enhance_amendment_bgbl.py
```

**Expected Outcome:** 21 amendments with proper BGBl references

---

### Phase 2: Full XML Re-scan for Amendment Data (Medium Effort)

**Goal:** Find all amendments hidden in XML  
**Effort:** 1-2 days  
**Impact:** Could increase coverage to 5-10%

#### Strategy

XML files contain amendments in multiple locations:

1. **`<norm><metadaten><standangabe>`** ← Currently parsed
2. **`<norm><metadaten><enbez>` attributes** ← Contains dates
3. **`<textdaten><fussnoten>`** ← Often reference amendments
4. **Document-level `<metadaten><standangabe>`** ← We might be missing these

#### Implementation Steps

1. **Analyze XML structure comprehensively:**
```bash
# Find all standangabe locations
grep -r "standangabe" xml_cache/ | wc -l

# Check document-level vs norm-level
python scripts/maintenance/analyze_amendment_locations.py
```

2. **Update parser to check all locations:**
```python
def extract_all_amendments(self, xml_root) -> List[Amendment]:
    """Extract amendments from all XML locations"""
    amendments = []
    
    # 1. Document-level amendments
    doc_meta = xml_root.find('metadaten')
    if doc_meta:
        amendments.extend(self.extract_amendments(doc_meta))
    
    # 2. Norm-level amendments (current)
    for norm in xml_root.findall('.//norm'):
        meta = norm.find('metadaten')
        if meta:
            amendments.extend(self.extract_amendments(meta))
    
    # 3. Footnotes that reference amendments
    for fussnote in xml_root.findall('.//fussnote'):
        # Parse footnote text for amendment references
        pass
    
    return amendments
```

**Expected Outcome:** 200-400 amendments (5-10% coverage)

---

### Phase 3: External BGBl Database Integration (High Impact)

**Goal:** Comprehensive amendment coverage  
**Effort:** 1-2 weeks  
**Impact:** 80-95% coverage (3,378-4,012 amendments)

#### Data Sources

##### Option A: BGBl XML Archive (Free, Official)
**Source:** https://www.bgbl.de/  
**Format:** XML files for each BGBl issue  
**Coverage:** Complete since 1949

**Process:**
1. Download BGBl metadata catalog
2. Search for SGB amendments by law name (e.g., "SGB II")
3. Parse amendment articles (e.g., "Artikel 2 ändert § 20 SGB II")
4. Link to our norms by paragraph number

**Advantages:**
- ✅ Official, authoritative source
- ✅ Free
- ✅ Complete historical coverage
- ✅ Includes full legal texts

**Challenges:**
- ⚠️ Complex XML structure
- ⚠️ Requires parsing amendment logic
- ⚠️ Need to match article references to norm IDs

##### Option B: Buzer.de API (Commercial)
**Source:** https://www.buzer.de/  
**Format:** JSON REST API  
**Coverage:** All German laws with full amendment history

**Pricing:** ~€500-1000/month for API access

**Advantages:**
- ✅ Pre-parsed, structured data
- ✅ Direct norm-to-amendment mapping
- ✅ Includes unofficial amendments

**Challenges:**
- ❌ Cost
- ⚠️ Requires API integration

##### Option C: Bundestag DIP (Dokumentations- und Informationssystem)
**Source:** https://dip.bundestag.de/  
**Format:** REST API (free)  
**Coverage:** All Bundestag documents, including amendment laws

**Advantages:**
- ✅ Free
- ✅ Official source
- ✅ Searchable by law name

**Challenges:**
- ⚠️ Doesn't provide direct paragraph-level mapping
- ⚠️ Requires cross-referencing

#### Recommended Approach: BGBl XML Archive

**Implementation Plan:**

1. **Download BGBl metadata catalog**
```python
# scripts/import_bgbl_amendments.py
import requests
from bs4 import BeautifulSoup

def download_bgbl_catalog():
    """Download BGBl metadata for years 2000-2025"""
    base_url = "https://www.bgbl.de/xaver/bgbl/start.xav"
    # Parse catalog pages
    # Download relevant issue XMLs
    pass
```

2. **Parse amendment articles**
```python
def parse_amendment_article(bgbl_xml):
    """Extract which SGBs are affected
    
    Example BGBl entry:
    'Artikel 2: Änderung des Zweiten Buches Sozialgesetzbuch'
    
    Returns: {
        'affected_law': 'SGB II',
        'paragraphs_changed': ['§ 20', '§ 21'],
        'effective_date': '2024-01-01',
        'bgbl_ref': 'BGBl I 2023, 1234'
    }
    """
    pass
```

3. **Match to existing norms**
```python
def link_amendments_to_norms(driver, amendments):
    """Create HAS_AMENDMENT relationships"""
    with driver.session() as session:
        for amendment in amendments:
            for para in amendment['paragraphs_changed']:
                # Find norm by paragraph number
                session.run("""
                    MATCH (norm:LegalNorm)
                    WHERE norm.paragraph_nummer = $para
                      AND norm.enbez CONTAINS $sgb
                    MERGE (amend:Amendment {
                        id: $amend_id,
                        bgbl_reference: $bgbl_ref,
                        effective_date: date($effective_date),
                        amendment_type: $type,
                        source: 'BGBl'
                    })
                    MERGE (norm)-[:HAS_AMENDMENT]->(amend)
                """, 
                para=para, 
                sgb=amendment['affected_law'],
                amend_id=amendment['id'],
                bgbl_ref=amendment['bgbl_ref'],
                effective_date=amendment['effective_date'],
                type=amendment['type'])
```

**Expected Outcome:** 3,000-4,000 amendments (70-95% coverage)

---

## 📈 Implementation Roadmap

### Timeline

| Phase | Duration | Outcome |
|-------|----------|---------|
| **Phase 1: Extract BGBl** | 1 day | 21 enhanced amendments |
| **Phase 2: Full XML Scan** | 3 days | 200-400 amendments (5-10%) |
| **Phase 3: BGBl Integration** | 10 days | 3,000+ amendments (70-95%) |
| **Total** | **2 weeks** | **80%+ coverage** |

### Detailed Schedule

#### Week 1
- **Day 1-2:** Phase 1 implementation
  - Update parser with BGBl regex
  - Create migration script
  - Test on 21 existing amendments
  
- **Day 3-5:** Phase 2 implementation
  - Analyze XML comprehensively
  - Update parser for all locations
  - Re-import all SGBs
  - Validate new amendments

#### Week 2
- **Day 1-3:** BGBl data source research
  - Download BGBl catalog
  - Analyze XML structure
  - Identify SGB-related issues
  
- **Day 4-7:** BGBl integration
  - Parse amendment articles
  - Extract paragraph mappings
  - Create import script
  - Link to existing norms
  
- **Day 8:** Testing & validation
  - Verify amendment accuracy
  - Check coverage statistics
  - Update UC20 test

- **Day 9-10:** Documentation & cleanup
  - Update README
  - Create amendment query guide
  - Archive old scripts

---

## 🎯 Success Metrics

### Coverage Targets

| Metric | Current | Phase 1 | Phase 2 | Phase 3 (Target) |
|--------|---------|---------|---------|------------------|
| **Norms with Amendments** | 13 (0.3%) | 13 | 200 (5%) | 3,378 (80%) |
| **Total Amendments** | 21 | 21 | 400 | 6,000+ |
| **With BGBl References** | 0 (0%) | 21 (100%) | 400 (100%) | 6,000+ (100%) |
| **With Effective Dates** | 21 (100%) | 21 (100%) | 400 (100%) | 6,000+ (100%) |

### Use Case Impact

**UC20: Änderungshistorie** will improve from:
- Current: ❌ Fails (only 1 amendment found)
- Phase 1: ⚠️ Still fails (data quality improved but coverage low)
- Phase 2: ⚠️ Partially works (5-10% coverage)
- Phase 3: ✅ **Fully functional (80%+ coverage)**

---

## 💡 Additional Enhancements

### 1. Amendment Type Classification

Classify amendments by type:
- **CHANGED** - Text modification
- **INSERTED** - New paragraph added
- **REPEALED** - Paragraph removed
- **RENUMBERED** - Paragraph number changed
- **REPLACED** - Complete replacement

### 2. Historical Version Chains

Create `SUPERSEDES` relationships:
```cypher
MATCH (norm:LegalNorm {paragraph_nummer: "20"})-[:HAS_AMENDMENT]->(a1:Amendment)
WITH norm, a1 ORDER BY a1.effective_date
WITH norm, collect(a1) as amendments
UNWIND range(0, size(amendments)-2) as i
WITH amendments[i] as older, amendments[i+1] as newer
MERGE (newer)-[:SUPERSEDES]->(older)
```

### 3. Amendment Impact Analysis

Track which paragraphs change most frequently:
```cypher
MATCH (norm:LegalNorm)-[:HAS_AMENDMENT]->(a:Amendment)
WITH norm, count(a) as amendment_count
ORDER BY amendment_count DESC
RETURN norm.enbez, norm.titel, amendment_count
```

---

## 🚀 Quick Start: Phase 1 Implementation

### Script: `scripts/maintenance/enhance_amendment_bgbl.py`

```python
#!/usr/bin/env python3
"""
Enhance existing amendments with BGBl references
Phase 1 of Amendment Improvement Strategy
"""

import re
import os
from dotenv import load_dotenv
from neo4j import GraphDatabase

load_dotenv()

def extract_bgbl_reference(text: str) -> tuple:
    """Extract BGBl reference from standkommentar"""
    patterns = [
        (r'v\.\s*\d{1,2}\.\d{1,2}\.(\d{4})\s+I\s+(\d+)', r'BGBl I \1, \2'),
        (r'v\.\s*\d{1,2}\.\d{1,2}\.(\d{4})\s+I\s+Nr\.\s+(\d+)', r'BGBl I \1, Nr. \2'),
    ]
    
    for pattern, replacement in patterns:
        match = re.search(pattern, text)
        if match:
            year = match.group(1)
            page_or_nr = match.group(2)
            return f"BGBl I {year}, {page_or_nr}", f"BGBl.{year}.I"
    
    return None, None

def main():
    driver = GraphDatabase.driver(
        os.getenv('NEO4J_URI'),
        auth=(os.getenv('NEO4J_USERNAME'), os.getenv('NEO4J_PASSWORD'))
    )
    
    with driver.session() as session:
        # Get all amendments
        result = session.run("""
            MATCH (a:Amendment)
            RETURN elementId(a) as id, a.standkommentar as comment
        """)
        
        enhanced = 0
        for record in result:
            comment = record['comment']
            bgbl_ref, periodikum = extract_bgbl_reference(comment)
            
            if bgbl_ref:
                session.run("""
                    MATCH (a:Amendment)
                    WHERE elementId(a) = $id
                    SET a.bgbl_reference = $bgbl_ref,
                        a.fundstelle_periodikum = $periodikum
                """, id=record['id'], bgbl_ref=bgbl_ref, periodikum=periodikum)
                
                enhanced += 1
                print(f"✅ {bgbl_ref}: {comment[:60]}...")
        
        print(f"\n✅ Enhanced {enhanced}/21 amendments with BGBl references")
    
    driver.close()

if __name__ == '__main__':
    main()
```

---

## 📚 References

- **BGBl Online:** https://www.bgbl.de/
- **DIP Bundestag:** https://dip.bundestag.de/
- **Gesetze im Internet:** https://www.gesetze-im-internet.de/
- **Buzer.de:** https://www.buzer.de/

---

**Status:** Ready for Implementation  
**Priority:** P2 (Medium-High)  
**Estimated ROI:** High (enables UC20, better legal traceability)  
**Risks:** Low (existing data remains functional)

