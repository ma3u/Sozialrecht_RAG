"""
XML Downloader for gesetze-im-internet.de
Downloads and caches legal XML files from the official German legal database
"""

import os
import logging
import requests
import zipfile
from pathlib import Path
from typing import List, Dict, Optional
from lxml import etree
import hashlib
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GIIXMLDownloader:
    """Download and cache XML from gesetze-im-internet.de"""
    
    BASE_URL = "https://www.gesetze-im-internet.de"
    TOC_URL = f"{BASE_URL}/gii-toc.xml"
    
    # SGB mapping to gesetze-im-internet.de identifiers
    SGB_MAPPING = {
        "I": "sgb_1",
        "II": "sgb_2",
        "III": "sgb_3",
        "IV": "sgb_4",
        "V": "sgb_5",
        "VI": "sgb_6",
        "VII": "sgb_7",
        "VIII": "sgb_8",
        "IX": "sgb_9",
        "X": "sgb_10",
        "XI": "sgb_11",
        "XII": "sgb_12",
        "XIV": "sgb_14"
    }
    
    def __init__(self, cache_dir: str = "./xml_cache"):
        """Initialize XML downloader
        
        Args:
            cache_dir: Directory to cache downloaded XML files
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.toc_cache_path = self.cache_dir / "gii-toc.xml"
        self._toc_data = None
        
        logger.info(f"✅ XML Downloader initialized with cache: {self.cache_dir}")
    
    def download_toc(self, force_refresh: bool = False) -> List[Dict]:
        """Download and parse gii-toc.xml
        
        Args:
            force_refresh: Force download even if cached
            
        Returns:
            List of law catalog entries with title and link
        """
        # Use cache if available and not forcing refresh
        if not force_refresh and self.toc_cache_path.exists():
            logger.info(f"Using cached TOC from {self.toc_cache_path}")
            with open(self.toc_cache_path, 'rb') as f:
                xml_content = f.read()
        else:
            logger.info(f"Downloading TOC from {self.TOC_URL}")
            response = requests.get(self.TOC_URL, timeout=30)
            response.raise_for_status()
            xml_content = response.content
            
            # Cache the TOC
            with open(self.toc_cache_path, 'wb') as f:
                f.write(xml_content)
            logger.info(f"✅ TOC cached to {self.toc_cache_path}")
        
        # Parse XML
        root = etree.fromstring(xml_content)
        
        catalog = []
        for item in root.findall('.//item'):
            title_elem = item.find('title')
            link_elem = item.find('link')
            
            if title_elem is not None and link_elem is not None:
                catalog.append({
                    'title': title_elem.text,
                    'link': link_elem.text
                })
        
        self._toc_data = catalog
        logger.info(f"✅ Parsed {len(catalog)} laws from TOC")
        return catalog
    
    def get_sgb_xml_urls(self) -> Dict[str, str]:
        """Map SGB I-XIV to their XML URLs
        
        Returns:
            Dictionary mapping SGB number to XML.zip URL
        """
        if self._toc_data is None:
            self.download_toc()
        
        sgb_urls = {}
        
        for sgb_num, gii_id in self.SGB_MAPPING.items():
            # Construct expected URL
            url = f"{self.BASE_URL}/{gii_id}/xml.zip"
            sgb_urls[sgb_num] = url
        
        logger.info(f"✅ Mapped {len(sgb_urls)} SGB laws to URLs")
        return sgb_urls
    
    def download_law_xml(self, sgb_nummer: str, force_refresh: bool = False) -> Path:
        """Download and extract XML.zip for specific law
        
        Args:
            sgb_nummer: SGB number (I, II, III, etc.)
            force_refresh: Force download even if cached
            
        Returns:
            Path to extracted XML file
        """
        if sgb_nummer not in self.SGB_MAPPING:
            raise ValueError(f"Unknown SGB number: {sgb_nummer}. Valid: {list(self.SGB_MAPPING.keys())}")
        
        gii_id = self.SGB_MAPPING[sgb_nummer]
        xml_zip_url = f"{self.BASE_URL}/{gii_id}/xml.zip"
        
        # Cache paths
        zip_cache_path = self.cache_dir / f"{gii_id}.xml.zip"
        xml_extract_dir = self.cache_dir / gii_id
        xml_extract_dir.mkdir(parents=True, exist_ok=True)
        
        # Check if already cached
        existing_xml = list(xml_extract_dir.glob("*.xml"))
        if not force_refresh and existing_xml:
            logger.info(f"Using cached XML for SGB {sgb_nummer}: {existing_xml[0]}")
            return existing_xml[0]
        
        # Download ZIP
        logger.info(f"Downloading XML for SGB {sgb_nummer} from {xml_zip_url}")
        try:
            response = requests.get(xml_zip_url, timeout=60)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to download SGB {sgb_nummer}: {e}")
            raise
        
        # Save ZIP
        with open(zip_cache_path, 'wb') as f:
            f.write(response.content)
        logger.info(f"✅ Downloaded {len(response.content)} bytes to {zip_cache_path}")
        
        # Extract XML
        with zipfile.ZipFile(zip_cache_path, 'r') as zip_ref:
            zip_ref.extractall(xml_extract_dir)
        
        # Find extracted XML file
        xml_files = list(xml_extract_dir.glob("*.xml"))
        if not xml_files:
            raise FileNotFoundError(f"No XML file found in {xml_extract_dir}")
        
        xml_path = xml_files[0]
        logger.info(f"✅ Extracted XML for SGB {sgb_nummer}: {xml_path} ({xml_path.stat().st_size} bytes)")
        
        return xml_path
    
    def download_all_sgbs(self, force_refresh: bool = False) -> Dict[str, Path]:
        """Download all SGB I-XIV XML files
        
        Args:
            force_refresh: Force download even if cached
            
        Returns:
            Dictionary mapping SGB number to XML file path
        """
        results = {}
        
        for sgb_num in self.SGB_MAPPING.keys():
            try:
                xml_path = self.download_law_xml(sgb_num, force_refresh)
                results[sgb_num] = xml_path
            except Exception as e:
                logger.error(f"Failed to download SGB {sgb_num}: {e}")
                results[sgb_num] = None
        
        success_count = sum(1 for v in results.values() if v is not None)
        logger.info(f"✅ Downloaded {success_count}/{len(self.SGB_MAPPING)} SGB XML files")
        
        return results
    
    def get_xml_metadata(self, xml_path: Path) -> Dict:
        """Extract metadata from XML file
        
        Args:
            xml_path: Path to XML file
            
        Returns:
            Dictionary with builddate, doknr, etc.
        """
        with open(xml_path, 'rb') as f:
            xml_content = f.read()
        
        root = etree.fromstring(xml_content)
        
        metadata = {
            'builddate': root.get('builddate'),
            'doknr': root.get('doknr'),
            'file_size': xml_path.stat().st_size,
            'file_path': str(xml_path),
            'downloaded_at': datetime.now().isoformat()
        }
        
        # Try to extract jurabk from first norm
        first_norm = root.find('.//norm')
        if first_norm is not None:
            metadaten = first_norm.find('metadaten')
            if metadaten is not None:
                jurabk = metadaten.find('jurabk')
                if jurabk is not None:
                    metadata['jurabk'] = jurabk.text
        
        return metadata


if __name__ == "__main__":
    # Test the downloader
    downloader = GIIXMLDownloader()
    
    # Download TOC
    print("\n=== Downloading TOC ===")
    catalog = downloader.download_toc()
    print(f"Found {len(catalog)} laws in catalog")
    
    # Get SGB URLs
    print("\n=== SGB XML URLs ===")
    sgb_urls = downloader.get_sgb_xml_urls()
    for sgb, url in sgb_urls.items():
        print(f"SGB {sgb}: {url}")
    
    # Download SGB II as test
    print("\n=== Downloading SGB II ===")
    xml_path = downloader.download_law_xml("II")
    print(f"XML path: {xml_path}")
    
    # Get metadata
    print("\n=== XML Metadata ===")
    metadata = downloader.get_xml_metadata(xml_path)
    for key, value in metadata.items():
        print(f"{key}: {value}")
