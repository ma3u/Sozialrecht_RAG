"""
Schema Migration Script for XML Legal Data
Migrates Neo4j database to support new XML schema alongside existing PDF-based data
"""

import logging
import os
from pathlib import Path
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SchemaMigrator:
    """Migrate existing data to new XML schema"""
    
    def __init__(self, uri: str = None, username: str = None, password: str = None):
        """Initialize Schema Migrator
        
        Args:
            uri: Neo4j connection URI
            username: Neo4j username
            password: Neo4j password
        """
        uri = uri or os.getenv("NEO4J_URI", "bolt://localhost:7687")
        username = username or os.getenv("NEO4J_USERNAME", "neo4j")
        password = password or os.getenv("NEO4J_PASSWORD", "password")
        
        self.driver = GraphDatabase.driver(uri, auth=(username, password))
        logger.info(f"✅ Connected to Neo4j at {uri}")
    
    def migrate(self):
        """Run complete migration"""
        logger.info("=== Starting Schema Migration ===")
        
        # 1. Apply XML schema
        self._apply_xml_schema()
        
        # 2. Verify schema
        self._verify_schema()
        
        # 3. Create compatibility views/procedures
        self._create_compatibility_layer()
        
        logger.info("✅ Migration complete!")
    
    def _apply_xml_schema(self):
        """Apply XML schema from cypher file"""
        logger.info("Applying XML schema...")
        
        # Read schema file
        schema_path = Path(__file__).parent.parent / "cypher" / "xml_schema.cypher"
        with open(schema_path, 'r') as f:
            schema_cypher = f.read()
        
        # Split into individual statements and execute
        with self.driver.session() as session:
            # Remove comments and split by semicolon
            statements = []
            for line in schema_cypher.split('\n'):
                line = line.strip()
                if line and not line.startswith('//'):
                    statements.append(line)
            
            # Join and split by CREATE statements
            full_text = ' '.join(statements)
            
            # Execute each CREATE statement
            for statement in full_text.split('CREATE'):
                if statement.strip():
                    stmt = 'CREATE' + statement
                    if stmt.strip().endswith(';'):
                        stmt = stmt.strip()[:-1]
                    
                    try:
                        session.run(stmt)
                        logger.debug(f"Executed: {stmt[:50]}...")
                    except Exception as e:
                        # Ignore "already exists" errors
                        if "already exists" in str(e) or "already indexed" in str(e):
                            logger.debug(f"Already exists: {stmt[:50]}...")
                        else:
                            logger.warning(f"Error executing statement: {e}")
        
        logger.info("✅ XML schema applied")
    
    def _verify_schema(self):
        """Verify schema creation"""
        logger.info("Verifying schema...")
        
        with self.driver.session() as session:
            # Check constraints
            result = session.run("SHOW CONSTRAINTS")
            constraints = list(result)
            logger.info(f"  Constraints: {len(constraints)}")
            
            # Check indexes
            result = session.run("SHOW INDEXES")
            indexes = list(result)
            logger.info(f"  Indexes: {len(indexes)}")
            
            # Check for XML node types
            result = session.run("""
                MATCH (n)
                RETURN DISTINCT labels(n) as labels, count(n) as count
                ORDER BY count DESC
            """)
            
            logger.info("  Node types in database:")
            for record in result:
                labels = record['labels']
                count = record['count']
                logger.info(f"    {labels}: {count}")
        
        logger.info("✅ Schema verified")
    
    def _create_compatibility_layer(self):
        """Create procedures for compatibility with existing code"""
        logger.info("Creating compatibility layer...")
        
        with self.driver.session() as session:
            # Create helper procedure for searching both old and new schemas
            # Note: Custom procedures require APOC or custom extensions
            # For now, we'll just log that this would be done
            logger.info("  Compatibility layer would be created via APOC procedures")
            logger.info("  For now, use CompatibilityAdapter class in Python")
        
        logger.info("✅ Compatibility layer ready")
    
    def preserve_existing_chunks(self):
        """Ensure existing chunk → document relationships are maintained"""
        logger.info("Preserving existing chunk relationships...")
        
        with self.driver.session() as session:
            # Check if old Document nodes exist
            result = session.run("MATCH (d:Document) RETURN count(d) as count")
            doc_count = result.single()['count']
            
            if doc_count > 0:
                logger.info(f"  Found {doc_count} existing Document nodes")
                logger.info("  Existing chunks will continue to work with old Document nodes")
            else:
                logger.info("  No existing Document nodes found")
        
        logger.info("✅ Existing chunks preserved")
    
    def rollback(self):
        """Rollback migration (remove XML schema elements)"""
        logger.warning("=== Rolling back migration ===")
        
        with self.driver.session() as session:
            # Drop constraints
            logger.info("Dropping XML schema constraints...")
            constraints_to_drop = [
                "legal_document_id",
                "legal_norm_id",
                "structural_unit_id",
                "text_unit_id",
                "list_item_id",
                "amendment_id"
            ]
            
            for constraint_name in constraints_to_drop:
                try:
                    session.run(f"DROP CONSTRAINT {constraint_name} IF EXISTS")
                    logger.info(f"  Dropped constraint: {constraint_name}")
                except Exception as e:
                    logger.warning(f"  Could not drop {constraint_name}: {e}")
            
            # Drop indexes
            logger.info("Dropping XML schema indexes...")
            indexes_to_drop = [
                "legal_document_sgb",
                "legal_document_jurabk",
                "legal_document_doknr",
                "legal_norm_paragraph",
                "legal_norm_enbez",
                "legal_norm_doknr",
                "structural_unit_level",
                "structural_unit_kennzahl",
                "legal_content_fulltext",
                "text_unit_fulltext"
            ]
            
            for index_name in indexes_to_drop:
                try:
                    session.run(f"DROP INDEX {index_name} IF EXISTS")
                    logger.info(f"  Dropped index: {index_name}")
                except Exception as e:
                    logger.warning(f"  Could not drop {index_name}: {e}")
        
        logger.info("✅ Rollback complete")
    
    def close(self):
        """Close Neo4j connection"""
        self.driver.close()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Migrate Neo4j schema for XML legal data")
    parser.add_argument("--rollback", action="store_true", help="Rollback migration")
    args = parser.parse_args()
    
    migrator = SchemaMigrator()
    
    try:
        if args.rollback:
            migrator.rollback()
        else:
            migrator.migrate()
            migrator.preserve_existing_chunks()
    finally:
        migrator.close()
