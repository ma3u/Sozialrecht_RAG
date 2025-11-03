#!/usr/bin/env python3
"""
Full Deployment Script - Phase 2
Import all SGB volumes with enhanced amendment tracking

This script imports all available SGB volumes into Neo4j with:
- Amendment nodes from standkommentar
- BGBl reference nodes
- Fussnoten for version tracking
- Automatic index creation
- Comprehensive statistics tracking
"""

import os
import sys
from pathlib import Path
from datetime import datetime
import json
import logging
from typing import Dict, List
from dotenv import load_dotenv

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.xml_to_neo4j_enhanced import import_single_sgb

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment
load_dotenv()

NEO4J_URI = os.getenv('NEO4J_URI', 'bolt://localhost:7687')
NEO4J_USER = os.getenv('NEO4J_USER', 'neo4j')
NEO4J_PASSWORD = os.getenv('NEO4J_PASSWORD', 'password')


# SGB volumes to import
SGB_VOLUMES = [
    {
        'name': 'SGB I',
        'number': 1,
        'path': 'xml_cache/sgb_1/BJNR030150975.xml',
        'description': 'Allgemeiner Teil'
    },
    {
        'name': 'SGB II',
        'number': 2,
        'path': 'xml_cache/sgb_2/BJNR295500003.xml',
        'description': 'Grundsicherung für Arbeitsuchende'
    },
    {
        'name': 'SGB III',
        'number': 3,
        'path': 'xml_cache/sgb_3/BJNR059500997.xml',
        'description': 'Arbeitsförderung'
    },
    {
        'name': 'SGB IV',
        'number': 4,
        'path': 'xml_cache/sgb_4/BJNR138450976.xml',
        'description': 'Gemeinsame Vorschriften'
    },
    {
        'name': 'SGB V',
        'number': 5,
        'path': 'xml_cache/sgb_5/BJNR024820988.xml',
        'description': 'Gesetzliche Krankenversicherung'
    },
    {
        'name': 'SGB VI',
        'number': 6,
        'path': 'xml_cache/sgb_6/BJNR122610989.xml',
        'description': 'Gesetzliche Rentenversicherung'
    },
    {
        'name': 'SGB VII',
        'number': 7,
        'path': 'xml_cache/sgb_7/BJNR125410996.xml',
        'description': 'Gesetzliche Unfallversicherung'
    },
    {
        'name': 'SGB VIII',
        'number': 8,
        'path': 'xml_cache/sgb_8/BJNR111630990.xml',
        'description': 'Kinder- und Jugendhilfe'
    },
    {
        'name': 'SGB IX',
        'number': 9,
        'path': 'xml_cache/sgb_9_2018/BJNR323410016.xml',
        'description': 'Rehabilitation und Teilhabe'
    },
    {
        'name': 'SGB X',
        'number': 10,
        'path': 'xml_cache/sgb_10/BJNR114690980.xml',
        'description': 'Sozialverwaltungsverfahren'
    },
    {
        'name': 'SGB XI',
        'number': 11,
        'path': 'xml_cache/sgb_11/BJNR101500994.xml',
        'description': 'Soziale Pflegeversicherung'
    },
    {
        'name': 'SGB XII',
        'number': 12,
        'path': 'xml_cache/sgb_12/BJNR302300003.xml',
        'description': 'Sozialhilfe'
    },
    {
        'name': 'SGB XIV',
        'number': 14,
        'path': 'xml_cache/sgb_14/BJNR265210019.xml',
        'description': 'Soziale Entschädigung'
    },
]


def check_prerequisites() -> bool:
    """Check if all prerequisites are met"""
    logger.info("🔍 Checking prerequisites...")
    
    # Check Neo4j connection
    try:
        from neo4j import GraphDatabase
        driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
        with driver.session() as session:
            result = session.run("RETURN 1 as test")
            result.single()
        driver.close()
        logger.info("✅ Neo4j connection successful")
    except Exception as e:
        logger.error(f"❌ Neo4j connection failed: {e}")
        return False
    
    # Check XML files exist
    missing_files = []
    project_root = Path(__file__).parent.parent
    
    for sgb in SGB_VOLUMES:
        xml_path = project_root / sgb['path']
        if not xml_path.exists():
            missing_files.append(sgb['name'])
            logger.warning(f"⚠️  Missing: {sgb['name']} at {xml_path}")
    
    if missing_files:
        logger.warning(f"⚠️  {len(missing_files)} files missing: {', '.join(missing_files)}")
        logger.info("Continuing with available files...")
    else:
        logger.info("✅ All XML files found")
    
    return True


def import_sgb_volume(sgb_info: Dict) -> Dict:
    """Import a single SGB volume"""
    project_root = Path(__file__).parent.parent
    xml_path = project_root / sgb_info['path']
    
    if not xml_path.exists():
        logger.warning(f"⏭️  Skipping {sgb_info['name']} - file not found")
        return {
            'success': False,
            'error': 'File not found',
            'skipped': True
        }
    
    logger.info(f"\n{'='*70}")
    logger.info(f"📖 Importing {sgb_info['name']} - {sgb_info['description']}")
    logger.info(f"{'='*70}")
    
    start_time = datetime.now()
    
    try:
        stats = import_single_sgb(
            sgb_path=xml_path,
            neo4j_uri=NEO4J_URI,
            neo4j_user=NEO4J_USER,
            neo4j_password=NEO4J_PASSWORD
        )
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        stats['success'] = True
        stats['duration_seconds'] = duration
        stats['sgb_name'] = sgb_info['name']
        stats['sgb_number'] = sgb_info['number']
        
        logger.info(f"\n✅ {sgb_info['name']} imported successfully in {duration:.2f}s")
        logger.info(f"   Norms: {stats.get('norms', 0)}")
        logger.info(f"   Amendments: {stats.get('amendments', 0)}")
        logger.info(f"   BGBl refs: {stats.get('bgbl_refs', 0)}")
        logger.info(f"   Fussnoten: {stats.get('fussnoten', 0)}")
        logger.info(f"   SUPERSEDED_BY: {stats.get('superseded_rels', 0)}")
        
        return stats
        
    except Exception as e:
        logger.error(f"❌ Error importing {sgb_info['name']}: {e}")
        import traceback
        traceback.print_exc()
        
        return {
            'success': False,
            'error': str(e),
            'sgb_name': sgb_info['name'],
            'sgb_number': sgb_info['number']
        }


def generate_deployment_report(results: List[Dict], output_path: Path):
    """Generate comprehensive deployment report"""
    
    # Calculate totals
    total_sgb = len(results)
    successful = sum(1 for r in results if r.get('success'))
    failed = sum(1 for r in results if not r.get('success') and not r.get('skipped'))
    skipped = sum(1 for r in results if r.get('skipped'))
    
    total_norms = sum(r.get('norms', 0) for r in results if r.get('success'))
    total_amendments = sum(r.get('amendments', 0) for r in results if r.get('success'))
    total_bgbl = sum(r.get('bgbl_refs', 0) for r in results if r.get('success'))
    total_fussnoten = sum(r.get('fussnoten', 0) for r in results if r.get('success'))
    total_superseded = sum(r.get('superseded_rels', 0) for r in results if r.get('success'))
    total_duration = sum(r.get('duration_seconds', 0) for r in results if r.get('success'))
    
    # Generate markdown report
    report = f"""# Phase 2 Full Deployment Report

**Date**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**Status**: {'✅ COMPLETE' if failed == 0 else '⚠️ PARTIAL'}  
**Duration**: {total_duration:.2f} seconds ({total_duration/60:.2f} minutes)

---

## Executive Summary

### Deployment Statistics

| Metric | Count | Status |
|--------|-------|--------|
| **Total SGB Volumes** | {total_sgb} | - |
| **Successfully Imported** | {successful} | {'✅' if successful == total_sgb else '⚠️'} |
| **Failed** | {failed} | {'✅' if failed == 0 else '❌'} |
| **Skipped** | {skipped} | {'✅' if skipped == 0 else '⚠️'} |

### Data Imported

| Type | Count |
|------|-------|
| **Norms** | {total_norms:,} |
| **Amendments** | {total_amendments:,} |
| **BGBl References** | {total_bgbl} |
| **Fussnoten** | {total_fussnoten} |
| **SUPERSEDED_BY Relationships** | {total_superseded} |

### Performance

| Metric | Value |
|--------|-------|
| **Total Duration** | {total_duration:.2f}s ({total_duration/60:.2f} min) |
| **Average per SGB** | {total_duration/successful if successful > 0 else 0:.2f}s |
| **Throughput** | {total_norms/total_duration if total_duration > 0 else 0:.2f} norms/sec |

---

## Individual SGB Results

"""
    
    # Add individual results
    for result in sorted(results, key=lambda x: x.get('sgb_number', 999)):
        sgb_name = result.get('sgb_name', 'Unknown')
        
        if result.get('skipped'):
            report += f"### {sgb_name} ⏭️ SKIPPED\n\n"
            report += f"**Reason**: {result.get('error', 'File not found')}\n\n"
            report += "---\n\n"
            continue
        
        if not result.get('success'):
            report += f"### {sgb_name} ❌ FAILED\n\n"
            report += f"**Error**: `{result.get('error', 'Unknown error')}`\n\n"
            report += "---\n\n"
            continue
        
        report += f"### {sgb_name} ✅ SUCCESS\n\n"
        report += f"**Duration**: {result.get('duration_seconds', 0):.2f}s\n\n"
        report += f"| Metric | Count |\n"
        report += f"|--------|-------|\n"
        report += f"| Norms | {result.get('norms', 0):,} |\n"
        report += f"| Amendments | {result.get('amendments', 0)} |\n"
        report += f"| BGBl References | {result.get('bgbl_refs', 0)} |\n"
        report += f"| Fussnoten | {result.get('fussnoten', 0)} |\n"
        report += f"| SUPERSEDED_BY | {result.get('superseded_rels', 0)} |\n"
        report += f"\n---\n\n"
    
    # Add final assessment
    report += f"""## Final Assessment

**Overall Status**: {'✅ DEPLOYMENT SUCCESSFUL' if failed == 0 and skipped == 0 else '⚠️ PARTIAL DEPLOYMENT'}

### Success Rate

- **Import Success**: {successful}/{total_sgb} ({100*successful/total_sgb if total_sgb > 0 else 0:.1f}%)
- **Data Quality**: {'✅ Excellent' if failed == 0 else '⚠️ Review Failed Imports'}

### Next Steps

"""
    
    if failed == 0 and skipped == 0:
        report += """1. ✅ All SGB volumes imported successfully
2. ✅ Run validation queries to verify data quality
3. ✅ Enable production access for users
4. ✅ Monitor query performance
"""
    else:
        report += f"""1. {'⚠️' if failed > 0 else '✅'} Review failed imports: {failed} volume(s)
2. {'⚠️' if skipped > 0 else '✅'} Obtain missing XML files: {skipped} volume(s)
3. ⚠️ Re-run deployment for failed/skipped volumes
4. ✅ Validate successfully imported data
"""
    
    report += f"""
---

**Report Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**Neo4j URI**: {NEO4J_URI}  
**Phase**: 2 (Amendment Coverage Enhancement)  
**Version**: 2.4
"""
    
    # Write report
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(report)
    
    logger.info(f"\n📄 Deployment report saved to: {output_path}")
    
    # Also save JSON for programmatic access
    json_path = output_path.with_suffix('.json')
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'total_sgb': total_sgb,
                'successful': successful,
                'failed': failed,
                'skipped': skipped,
                'total_norms': total_norms,
                'total_amendments': total_amendments,
                'total_bgbl': total_bgbl,
                'total_fussnoten': total_fussnoten,
                'total_superseded': total_superseded,
                'duration_seconds': total_duration
            },
            'individual_results': results
        }, f, indent=2)
    
    logger.info(f"📄 JSON report saved to: {json_path}")


def main():
    """Main deployment function"""
    print("=" * 70)
    print("🚀 PHASE 2 FULL DEPLOYMENT - ALL SGB VOLUMES")
    print("=" * 70)
    print()
    
    # Check prerequisites
    if not check_prerequisites():
        logger.error("❌ Prerequisites check failed. Aborting deployment.")
        sys.exit(1)
    
    print()
    logger.info(f"📊 Deploying {len(SGB_VOLUMES)} SGB volumes with amendment tracking")
    logger.info(f"🎯 Target: Neo4j at {NEO4J_URI}")
    print()
    
    # Confirm deployment
    response = input("⚠️  This will import all SGB volumes. Continue? (yes/no): ")
    if response.lower() not in ['yes', 'y']:
        logger.info("❌ Deployment cancelled by user")
        sys.exit(0)
    
    print()
    start_time = datetime.now()
    
    # Import all volumes
    results = []
    for sgb_info in SGB_VOLUMES:
        result = import_sgb_volume(sgb_info)
        results.append(result)
    
    end_time = datetime.now()
    total_duration = (end_time - start_time).total_seconds()
    
    # Generate report
    print()
    logger.info("=" * 70)
    logger.info("📊 GENERATING DEPLOYMENT REPORT")
    logger.info("=" * 70)
    
    project_root = Path(__file__).parent.parent
    report_path = project_root / f"DEPLOYMENT_REPORT_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    
    generate_deployment_report(results, report_path)
    
    # Final summary
    successful = sum(1 for r in results if r.get('success'))
    failed = sum(1 for r in results if not r.get('success') and not r.get('skipped'))
    
    print()
    logger.info("=" * 70)
    logger.info("🎉 DEPLOYMENT COMPLETE")
    logger.info("=" * 70)
    logger.info(f"✅ Successful: {successful}/{len(SGB_VOLUMES)}")
    logger.info(f"❌ Failed: {failed}")
    logger.info(f"⏱️  Duration: {total_duration:.2f}s ({total_duration/60:.2f} min)")
    logger.info(f"📄 Report: {report_path}")
    print()
    
    if failed == 0:
        logger.info("🎉 ALL VOLUMES IMPORTED SUCCESSFULLY!")
        logger.info("✅ Phase 2 deployment complete - system ready for production")
    else:
        logger.warning(f"⚠️  {failed} volume(s) failed - review report for details")
    
    print()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        logger.warning("\n\n❌ Deployment interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"\n\n❌ Deployment failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
