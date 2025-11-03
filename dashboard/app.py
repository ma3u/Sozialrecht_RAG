#!/usr/bin/env python3
"""
Coverage Dashboard - 14 Use Cases
Flask Web Dashboard für Neo4j Sozialrecht RAG

Usage:
    python dashboard/app.py
    
    # Custom Port
    DASHBOARD_PORT=8080 python dashboard/app.py
"""

import os
from flask import Flask, render_template, jsonify
from neo4j import GraphDatabase
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

# Config
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")
DASHBOARD_PORT = int(os.getenv("DASHBOARD_PORT", "8080"))

app = Flask(__name__)

# Neo4j Driver
driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))


def get_use_case_coverage():
    """Holt Coverage für alle 14 Use Cases"""
    
    use_cases = [
        {"uc": "UC01", "name": "Regelbedarfsermittlung", "sgb": "II", "paragraphs": ["20", "21", "22", "23"]},
        {"uc": "UC02", "name": "Sanktionsprüfung", "sgb": "II", "paragraphs": ["32"]},
        {"uc": "UC03", "name": "Einkommensanrechnung", "sgb": "II", "paragraphs": ["11", "11b"]},
        {"uc": "UC06", "name": "Bedarfsgemeinschaft", "sgb": "II", "paragraphs": ["7"]},
        {"uc": "UC08", "name": "Erstausstattung", "sgb": "II", "paragraphs": ["24"]},
        {"uc": "UC10", "name": "Widerspruchsverfahren", "sgb": "X", "paragraphs": ["79", "80", "84", "85"]},
        {"uc": "UC14", "name": "Datenschutz-Compliance", "sgb": "X", "paragraphs": ["67", "68", "69", "70", "71", "72", "73", "74", "75", "76"]},
    ]
    
    results = []
    
    with driver.session() as session:
        for uc in use_cases:
            query = """
                MATCH (doc:LegalDocument {sgb_nummer: $sgb})
                      -[:CONTAINS_NORM]->(norm:LegalNorm)
                WHERE norm.paragraph_nummer IN $paragraphs
                OPTIONAL MATCH (norm)-[:HAS_CHUNK]->(chunk:Chunk)
                RETURN 
                    count(DISTINCT norm) as normen,
                    count(DISTINCT chunk) as chunks,
                    $expected as expected
            """
            
            result = session.run(query, sgb=uc["sgb"], paragraphs=uc["paragraphs"], expected=len(uc["paragraphs"]))
            record = result.single()
            
            normen = record["normen"]
            chunks = record["chunks"]
            expected = record["expected"]
            
            status = "✅" if normen == expected and chunks > 0 else ("⚠️" if chunks > 0 else "❌")
            
            results.append({
                "uc": uc["uc"],
                "name": uc["name"],
                "sgb": uc["sgb"],
                "normen": normen,
                "expected": expected,
                "chunks": chunks,
                "status": status,
                "coverage": f"{normen}/{expected}"
            })
    
    return results


def get_sgb_statistics():
    """Holt Statistiken pro SGB"""
    
    with driver.session() as session:
        query = """
            MATCH (doc:LegalDocument)
            OPTIONAL MATCH (doc)-[:CONTAINS_NORM]->(norm:LegalNorm)
            OPTIONAL MATCH (norm)-[:HAS_CHUNK]->(chunk:Chunk)
            WITH doc.sgb_nummer as sgb,
                 doc.title as titel,
                 count(DISTINCT norm) as normen,
                 count(DISTINCT chunk) as chunks,
                 count(DISTINCT CASE WHEN chunk IS NOT NULL THEN norm END) as normen_mit_chunks
            WHERE sgb IN ['II', 'X']
            RETURN 
                sgb,
                titel,
                normen,
                chunks,
                normen_mit_chunks,
                round(toFloat(normen_mit_chunks) / normen * 100, 1) as coverage_percent
            ORDER BY sgb
        """
        
        result = session.run(query)
        return [dict(record) for record in result]


def get_system_health():
    """Prüft System Health"""
    
    with driver.session() as session:
        # Total stats
        stats_query = """
            MATCH (doc:LegalDocument)
            OPTIONAL MATCH (doc)-[:CONTAINS_NORM]->(norm:LegalNorm)
            OPTIONAL MATCH (norm)-[:HAS_CHUNK]->(chunk:Chunk)
            RETURN 
                count(DISTINCT doc) as documents,
                count(DISTINCT norm) as norms,
                count(DISTINCT chunk) as chunks
        """
        
        stats = session.run(stats_query).single()
        
        # Embeddings
        embeddings_query = """
            MATCH (c:Chunk)
            WHERE c.embedding IS NOT NULL
            RETURN count(c) as chunks_with_embeddings
        """
        
        embeddings = session.run(embeddings_query).single()
        
        # Indexes
        indexes_query = "SHOW INDEXES"
        indexes = session.run(indexes_query)
        index_count = sum(1 for _ in indexes)
        
        return {
            "documents": stats["documents"],
            "norms": stats["norms"],
            "chunks": stats["chunks"],
            "embeddings": embeddings["chunks_with_embeddings"],
            "indexes": index_count,
            "timestamp": datetime.now().isoformat()
        }


@app.route("/")
def index():
    """Dashboard Homepage"""
    return render_template("dashboard.html")


@app.route("/api/use_cases")
def api_use_cases():
    """API: Use Case Coverage"""
    try:
        data = get_use_case_coverage()
        return jsonify({"success": True, "data": data})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/sgb_stats")
def api_sgb_stats():
    """API: SGB Statistiken"""
    try:
        data = get_sgb_statistics()
        return jsonify({"success": True, "data": data})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/health")
def api_health():
    """API: System Health"""
    try:
        data = get_system_health()
        return jsonify({"success": True, "data": data})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/health")
def health_check():
    """Health Check Endpoint"""
    try:
        driver.verify_connectivity()
        return jsonify({"status": "healthy", "neo4j": "connected"})
    except Exception as e:
        return jsonify({"status": "unhealthy", "error": str(e)}), 503


if __name__ == "__main__":
    print("\n" + "="*80)
    print("📊 Coverage Dashboard - 14 Use Cases")
    print("="*80)
    print(f"\n🚀 Starting Dashboard on http://localhost:{DASHBOARD_PORT}")
    print(f"📊 Neo4j: {NEO4J_URI}")
    print("\n" + "="*80)
    print("API Endpoints:")
    print(f"  http://localhost:{DASHBOARD_PORT}/api/use_cases")
    print(f"  http://localhost:{DASHBOARD_PORT}/api/sgb_stats")
    print(f"  http://localhost:{DASHBOARD_PORT}/api/health")
    print("="*80 + "\n")
    
    app.run(host="0.0.0.0", port=DASHBOARD_PORT, debug=True)
