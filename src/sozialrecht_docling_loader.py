"""
Sozialrecht Docling Loader
Spezialisierter Document Loader für SGB-PDFs mit Metadaten-Extraktion

Basiert auf: ms-agentf-neo4j/neo4j-rag-demo/src/docling_loader.py
"""

from pathlib import Path
from typing import Dict, Optional
import re
import logging
from docling.document_converter import DocumentConverter

logger = logging.getLogger(__name__)


class SozialrechtDoclingLoader:
    """Docling Loader spezialisiert für Sozialrecht-Dokumente"""

    def __init__(self, neo4j_rag=None):
        """Initialize with Neo4j RAG instance"""
        self.rag = neo4j_rag
        self.converter = DocumentConverter()

    def load_sozialrecht_pdf(self, pdf_path: Path) -> Dict:
        """Load SGB PDF mit Sozialrecht-spezifischen Metadaten

        Args:
            pdf_path: Path zum PDF

        Returns:
            Result dictionary mit Status, Chunks, Metadaten
        """
        result = {
            'filename': pdf_path.name,
            'status': 'pending',
            'chunks': 0,
            'error': None
        }

        try:
            # Extract metadata from filename/path
            metadata = self._extract_sozialrecht_metadata(pdf_path)

            # Convert with Docling
            doc_result = self.converter.convert(str(pdf_path))

            # Extract text
            text = doc_result.document.export_to_markdown() if hasattr(doc_result.document, 'export_to_markdown') else str(doc_result.document)

            # Add to Neo4j
            if self.rag:
                doc_id = self.rag.add_sgb_document(
                    content=text,
                    sgb_nummer=metadata['sgb_nummer'],
                    document_type=metadata['document_type'],
                    source_url=metadata['source_url'],
                    metadata={
                        'filename': pdf_path.name,
                        'file_size_mb': round(pdf_path.stat().st_size / (1024*1024), 2),
                        **metadata
                    }
                )

                result['status'] = 'success'
                result['chunks'] = text.count('\n\n')  # Estimate
                result['doc_id'] = doc_id

        except Exception as e:
            result['status'] = 'failed'
            result['error'] = str(e)
            logger.error(f"Error processing {pdf_path.name}: {e}")

        return result

    def _extract_sozialrecht_metadata(self, pdf_path: Path) -> Dict:
        """Extrahiere Metadaten aus Dateinamen und Pfad

        Erkennt:
        - SGB Nummer (I-XIV)
        - Document Type (Gesetz, Weisung, Rundschreiben)
        - Paragraph Nummer
        - Stand-Datum (wenn im Dateinamen)
        """
        filename = pdf_path.name
        parent_dir = pdf_path.parent.name

        metadata = {
            'sgb_nummer': 'Unknown',
            'document_type': 'Unknown',
            'paragraph_nummer': None,
            'stand_datum': None,
            'source_url': ''
        }

        # Extract SGB number from filename
        sgb_match = re.search(r'SGB[_\s]*(\d+|[IVX]+)', filename, re.IGNORECASE)
        if sgb_match:
            sgb_num = sgb_match.group(1)
            # Convert to Roman numerals if numeric
            if sgb_num.isdigit():
                roman_map = ['', 'I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX', 'X', 'XI', 'XII', 'XIII', 'XIV']
                sgb_num = roman_map[int(sgb_num)] if int(sgb_num) < len(roman_map) else sgb_num
            metadata['sgb_nummer'] = sgb_num

        # Determine document type
        if 'Gesetze' in str(pdf_path):
            metadata['document_type'] = 'Gesetz'
            metadata['source_url'] = f"https://www.gesetze-im-internet.de/sgb_{sgb_num.lower()}/"
        elif 'Fachliche_Weisungen' in str(pdf_path) or 'FW_' in filename:
            if 'harald' in filename.lower() or 'thome' in filename.lower():
                metadata['document_type'] = 'Harald_Thome'
                metadata['source_url'] = "https://harald-thome.de/"
            elif 'BIH' in filename or 'Uebersicht' in filename:
                metadata['document_type'] = 'Fachverband'
                metadata['source_url'] = "https://www.bih.de/"
            elif 'DGUV' in filename or 'Aerztevertrag' in filename:
                metadata['document_type'] = 'Fachverband'
                metadata['source_url'] = "https://www.dguv.de/"
            else:
                metadata['document_type'] = 'BA_Weisung'
                metadata['source_url'] = "https://www.arbeitsagentur.de/"
        elif 'Rundschreiben' in str(pdf_path) or 'RS_' in filename or 'BMAS' in filename:
            metadata['document_type'] = 'BMAS_Rundschreiben'
            metadata['source_url'] = "https://www.bmas.de/" if 'BMAS' in filename else "https://www.tacheles-sozialhilfe.de/"
        elif 'Folien' in filename or 'Thome' in filename:
            metadata['document_type'] = 'Harald_Thome'
            metadata['source_url'] = "https://harald-thome.de/"

        # Extract paragraph number
        para_match = re.search(r'Par[_\s]*(\d+[a-z]?(?:[-_]\d+[a-z]?)*)', filename, re.IGNORECASE)
        if para_match:
            metadata['paragraph_nummer'] = para_match.group(1).replace('_', '-')

        # Extract stand datum from filename
        date_match = re.search(r'(\d{2})[._](\d{2})[._](\d{4})', filename)
        if date_match:
            metadata['stand_datum'] = f"{date_match.group(3)}-{date_match.group(2)}-{date_match.group(1)}"
        elif '2025' in filename:
            metadata['stand_datum'] = '2025-01-01'
        elif '2024' in filename:
            metadata['stand_datum'] = '2024-01-01'
        elif '2023' in filename:
            metadata['stand_datum'] = '2023-01-01'

        return metadata

    def close(self):
        """Close Neo4j connection"""
        if self.rag:
            self.rag.close()


if __name__ == "__main__":
    exit(main())
