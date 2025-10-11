#!/usr/bin/env python3
"""
Upload alle Sozialrecht-Dokumente zu Neo4j
Verarbeitet: Gesetze, Fachliche Weisungen, BMAS Rundschreiben

Basiert auf: ms-agentf-neo4j/neo4j-rag-demo/scripts/upload_pdfs_to_neo4j.py
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent.parent))

from src.sozialrecht_docling_loader import SozialrechtDoclingLoader
from src.sozialrecht_neo4j_rag import SozialrechtNeo4jRAG
import argparse
from tqdm import tqdm
import logging

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(description='Upload Sozialrecht-Dokumente zu Neo4j')
    parser.add_argument('--dry-run', action='store_true', help='Zeige nur was hochgeladen würde')
    parser.add_argument('--skip-existing', action='store_true', default=True, help='Überspringe existierende Dokumente')
    parser.add_argument('--categories', nargs='+', choices=['Gesetze', 'Fachliche_Weisungen', 'Rundschreiben_BMAS'],
                       help='Nur spezifische Kategorien verarbeiten')
    parser.add_argument('--limit', type=int, help='Begrenze Anzahl Uploads (Testing)')

    args = parser.parse_args()

    # Project root
    project_root = Path(__file__).parent.parent

    print("\n📚 Sozialrecht Neo4j Upload System")
    print("=" * 60)

    # Find all PDFs
    pdf_categories = {
        'Gesetze': list((project_root / 'Gesetze').glob('*.pdf')),
        'Fachliche_Weisungen': list((project_root / 'Fachliche_Weisungen').rglob('*.pdf')),
        'Rundschreiben_BMAS': list((project_root / 'Rundschreiben_BMAS').rglob('*.pdf'))
    }

    # Filter by categories if specified
    if args.categories:
        pdf_categories = {k: v for k, v in pdf_categories.items() if k in args.categories}

    total_pdfs = sum(len(pdfs) for pdfs in pdf_categories.values())

    print(f"\n📊 Gefundene Dokumente:")
    for cat, pdfs in pdf_categories.items():
        print(f"  {cat}: {len(pdfs)} PDFs")
    print(f"  Gesamt: {total_pdfs} PDFs")

    if args.limit:
        print(f"\n🎯 Limit: {args.limit} Dokumente")

    if args.dry_run:
        print("\n🔍 DRY RUN MODE - Keine Verarbeitung")
        return 0

    # Connect to Neo4j
    print("\n🔗 Verbinde zu Neo4j...")
    try:
        rag = SozialrechtNeo4jRAG()
        loader = SozialrechtDoclingLoader(rag)
        print("✅ Verbunden mit Neo4j")

        stats_before = rag.get_stats()
        print(f"📊 Datenbank: {stats_before['documents']} Dokumente, {stats_before['chunks']} Chunks")

    except Exception as e:
        logger.error(f"❌ Neo4j Verbindung fehlgeschlagen: {e}")
        return 1

    # Process all PDFs
    print(f"\n🚀 Starte Upload...")
    print("=" * 60 + "\n")

    results = []
    count = 0

    for category, pdfs in pdf_categories.items():
        print(f"\n📁 Kategorie: {category}")

        for pdf_path in tqdm(pdfs, desc=category):
            if args.limit and count >= args.limit:
                break

            try:
                result = loader.load_sozialrecht_pdf(pdf_path)
                results.append(result)
                count += 1

                if result['status'] == 'success':
                    logger.info(f"  ✅ {pdf_path.name}: {result['chunks']} chunks")
                elif result['status'] == 'skipped':
                    logger.info(f"  ⏭️ {pdf_path.name}: Existiert bereits")
                else:
                    logger.error(f"  ❌ {pdf_path.name}: {result.get('error', 'Unknown')}")

            except Exception as e:
                logger.error(f"  ❌ {pdf_path.name}: {str(e)[:100]}")
                results.append({'filename': pdf_path.name, 'status': 'failed', 'error': str(e)})

    # Final stats
    stats_after = rag.get_stats()

    print(f"\n{'='*60}")
    print(f"📊 Upload Zusammenfassung:\n")

    successful = sum(1 for r in results if r['status'] == 'success')
    skipped = sum(1 for r in results if r['status'] == 'skipped')
    failed = sum(1 for r in results if r['status'] == 'failed')

    print(f"  ✅ Erfolgreich: {successful}")
    print(f"  ⏭️ Übersprungen: {skipped}")
    print(f"  ❌ Fehlgeschlagen: {failed}")
    print(f"  📄 Gesamt: {len(results)}")

    print(f"\n📈 Datenbank Änderungen:")
    print(f"  Dokumente: {stats_before['documents']} → {stats_after['documents']} (+{stats_after['documents'] - stats_before['documents']})")
    print(f"  Chunks: {stats_before['chunks']} → {stats_after['chunks']} (+{stats_after['chunks'] - stats_before['chunks']})")
    print(f"  Paragraphen: {stats_after.get('paragraphs', 0)}")
    print(f"  SGBs abgedeckt: {', '.join(stats_after.get('sgbs_covered', []))}")

    # Cleanup
    loader.close()
    rag.close()

    print(f"\n✨ Upload abgeschlossen!")
    print(f"🔍 Teste Suche mit: python scripts/test_sozialrecht_rag.py")

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    exit(main())
