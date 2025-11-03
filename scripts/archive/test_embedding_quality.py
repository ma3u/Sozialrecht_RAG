#!/usr/bin/env python3
"""
Test Embedding Quality Comparison
Compares local embeddings vs Azure OpenAI text-embedding-3-large

Tests semantic similarity for German legal queries across both models
"""

import os
import sys
import time
from typing import List, Tuple
from pathlib import Path
import numpy as np
from dotenv import load_dotenv

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

load_dotenv()

# Local model
from sentence_transformers import SentenceTransformer

# Azure OpenAI
from openai import AzureOpenAI

# Neo4j for getting real chunks
from neo4j import GraphDatabase


class EmbeddingTester:
    def __init__(self):
        # Local model
        print("Loading local embedding model...")
        self.local_model = SentenceTransformer('paraphrase-multilingual-mpnet-base-v2')
        
        # Azure OpenAI
        print("Initializing Azure OpenAI client...")
        self.azure_client = AzureOpenAI(
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-08-01-preview"),
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
        )
        self.azure_deployment = os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT", "text-embedding-3-large")
        
        # Neo4j
        self.driver = GraphDatabase.driver(
            os.getenv("NEO4J_URI", "bolt://localhost:7687"),
            auth=(os.getenv("NEO4J_USERNAME", "neo4j"), 
                  os.getenv("NEO4J_PASSWORD", "password"))
        )
        
    def get_local_embedding(self, text: str) -> np.ndarray:
        """Get embedding from local model"""
        return self.local_model.encode([text])[0]
    
    def get_azure_embedding(self, text: str) -> np.ndarray:
        """Get embedding from Azure OpenAI"""
        response = self.azure_client.embeddings.create(
            model=self.azure_deployment,
            input=text
        )
        return np.array(response.data[0].embedding)
    
    def cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """Calculate cosine similarity between two vectors"""
        return np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))
    
    def get_sample_chunks(self, limit: int = 10) -> List[str]:
        """Get sample legal text chunks from Neo4j"""
        query = """
        MATCH (chunk:Chunk)
        WHERE chunk.text IS NOT NULL 
          AND size(chunk.text) > 100
        RETURN chunk.text as text
        LIMIT $limit
        """
        
        with self.driver.session() as session:
            result = session.run(query, limit=limit)
            return [record['text'] for record in result]
    
    def test_semantic_search_quality(self, queries: List[str], corpus: List[str]) -> dict:
        """
        Test semantic search quality by finding relevant documents
        Returns precision metrics for both models
        """
        results = {
            'local': {'similarities': [], 'time': 0},
            'azure': {'similarities': [], 'time': 0}
        }
        
        print(f"\n{'='*80}")
        print("Semantic Search Quality Test")
        print(f"{'='*80}\n")
        
        for query_idx, query in enumerate(queries, 1):
            print(f"Query {query_idx}: {query}")
            print("-" * 80)
            
            # Local embeddings
            start = time.time()
            query_emb_local = self.get_local_embedding(query)
            corpus_emb_local = [self.get_local_embedding(text) for text in corpus]
            
            local_sims = [self.cosine_similarity(query_emb_local, doc_emb) 
                         for doc_emb in corpus_emb_local]
            local_time = time.time() - start
            
            results['local']['similarities'].append(local_sims)
            results['local']['time'] += local_time
            
            # Azure embeddings
            start = time.time()
            query_emb_azure = self.get_azure_embedding(query)
            time.sleep(0.5)  # Rate limiting
            
            corpus_emb_azure = []
            for text in corpus:
                corpus_emb_azure.append(self.get_azure_embedding(text))
                time.sleep(0.5)  # Rate limiting
            
            azure_sims = [self.cosine_similarity(query_emb_azure, doc_emb) 
                         for doc_emb in corpus_emb_azure]
            azure_time = time.time() - start
            
            results['azure']['similarities'].append(azure_sims)
            results['azure']['time'] += azure_time
            
            # Show top 3 results for each
            local_top3 = sorted(enumerate(local_sims), key=lambda x: x[1], reverse=True)[:3]
            azure_top3 = sorted(enumerate(azure_sims), key=lambda x: x[1], reverse=True)[:3]
            
            print("\nLocal Model (768 dim) - Top 3:")
            for rank, (idx, score) in enumerate(local_top3, 1):
                print(f"  {rank}. [{score:.4f}] {corpus[idx][:80]}...")
            
            print("\nAzure 3-large (3072 dim) - Top 3:")
            for rank, (idx, score) in enumerate(azure_top3, 1):
                print(f"  {rank}. [{score:.4f}] {corpus[idx][:80]}...")
            
            print("\n")
        
        return results
    
    def test_embedding_speed(self, texts: List[str]) -> dict:
        """Test embedding generation speed"""
        print(f"\n{'='*80}")
        print("Embedding Speed Test")
        print(f"{'='*80}\n")
        
        # Local
        start = time.time()
        for text in texts:
            _ = self.get_local_embedding(text)
        local_time = time.time() - start
        local_speed = len(texts) / local_time
        
        # Azure
        start = time.time()
        for text in texts:
            _ = self.get_azure_embedding(text)
            time.sleep(0.1)  # Rate limiting
        azure_time = time.time() - start
        azure_speed = len(texts) / azure_time
        
        print(f"Local Model (768 dim):")
        print(f"  Total time: {local_time:.2f}s")
        print(f"  Speed: {local_speed:.1f} embeddings/sec")
        print(f"  Avg time per embedding: {local_time/len(texts)*1000:.1f}ms")
        
        print(f"\nAzure 3-large (3072 dim):")
        print(f"  Total time: {azure_time:.2f}s")
        print(f"  Speed: {azure_speed:.1f} embeddings/sec")
        print(f"  Avg time per embedding: {azure_time/len(texts)*1000:.1f}ms")
        
        print(f"\nSpeedup: {local_speed/azure_speed:.1f}x faster (local)")
        
        return {
            'local': {'time': local_time, 'speed': local_speed},
            'azure': {'time': azure_time, 'speed': azure_speed}
        }
    
    def test_retrieval_precision(self, queries_and_expected: List[Tuple[str, List[int]]], 
                                 corpus: List[str]) -> dict:
        """
        Test retrieval precision with known relevant documents
        queries_and_expected: List of (query, list of expected relevant indices)
        """
        print(f"\n{'='*80}")
        print("Retrieval Precision Test")
        print(f"{'='*80}\n")
        
        local_precisions = []
        azure_precisions = []
        
        for query, expected_indices in queries_and_expected:
            print(f"Query: {query}")
            print(f"Expected relevant indices: {expected_indices}")
            
            # Get embeddings
            query_emb_local = self.get_local_embedding(query)
            query_emb_azure = self.get_azure_embedding(query)
            
            corpus_emb_local = [self.get_local_embedding(text) for text in corpus]
            corpus_emb_azure = []
            for text in corpus:
                corpus_emb_azure.append(self.get_azure_embedding(text))
                time.sleep(0.5)
            
            # Calculate similarities
            local_sims = [self.cosine_similarity(query_emb_local, doc_emb) 
                         for doc_emb in corpus_emb_local]
            azure_sims = [self.cosine_similarity(query_emb_azure, doc_emb) 
                         for doc_emb in corpus_emb_azure]
            
            # Get top K predictions (K = number of expected relevant docs)
            k = len(expected_indices)
            local_top_k = [idx for idx, _ in sorted(enumerate(local_sims), 
                                                     key=lambda x: x[1], reverse=True)[:k]]
            azure_top_k = [idx for idx, _ in sorted(enumerate(azure_sims), 
                                                     key=lambda x: x[1], reverse=True)[:k]]
            
            # Calculate precision
            local_hits = len(set(local_top_k) & set(expected_indices))
            azure_hits = len(set(azure_top_k) & set(expected_indices))
            
            local_precision = local_hits / k
            azure_precision = azure_hits / k
            
            local_precisions.append(local_precision)
            azure_precisions.append(azure_precision)
            
            print(f"  Local P@{k}: {local_precision:.2%} (retrieved: {local_top_k})")
            print(f"  Azure P@{k}: {azure_precision:.2%} (retrieved: {azure_top_k})")
            print()
        
        avg_local = np.mean(local_precisions)
        avg_azure = np.mean(azure_precisions)
        
        print(f"Average Precision:")
        print(f"  Local: {avg_local:.2%}")
        print(f"  Azure: {avg_azure:.2%}")
        print(f"  Improvement: {(avg_azure - avg_local) / avg_local * 100:+.1f}%")
        
        return {
            'local': local_precisions,
            'azure': azure_precisions,
            'avg_local': avg_local,
            'avg_azure': avg_azure
        }


def main():
    print("\n" + "="*80)
    print("EMBEDDING QUALITY COMPARISON TEST")
    print("Local (768 dim) vs Azure OpenAI text-embedding-3-large (3072 dim)")
    print("="*80)
    
    # Check Azure credentials
    if not os.getenv("AZURE_OPENAI_API_KEY"):
        print("\n❌ AZURE_OPENAI_API_KEY not set!")
        print("Run: source setup_azure_openai.sh")
        return 1
    
    tester = EmbeddingTester()
    
    # Test 1: Speed comparison
    print("\n📊 TEST 1: Speed Comparison")
    sample_texts = tester.get_sample_chunks(limit=10)
    speed_results = tester.test_embedding_speed(sample_texts[:5])
    
    # Test 2: Semantic search on legal queries
    print("\n📊 TEST 2: Semantic Search Quality")
    
    legal_queries = [
        "Wie beantrage ich Arbeitslosengeld?",
        "Welche Fristen gelten für einen Widerspruch?",
        "Krankenversicherung für Selbstständige"
    ]
    
    corpus = sample_texts
    search_results = tester.test_semantic_search_quality(legal_queries, corpus)
    
    # Test 3: Retrieval precision with curated examples
    print("\n📊 TEST 3: Retrieval Precision")
    
    # Create a small curated test set
    test_corpus = [
        "Der Antrag auf Arbeitslosengeld ist schriftlich zu stellen.",
        "Die Frist für einen Widerspruch beträgt einen Monat.",
        "Selbstständige können sich freiwillig versichern.",
        "Die Krankenversicherung ist für alle Bürger verpflichtend.",
        "Arbeitslose haben Anspruch auf Vermittlungsleistungen.",
    ]
    
    test_queries = [
        ("Arbeitslosengeld beantragen", [0, 4]),  # Indices 0 and 4 are relevant
        ("Widerspruch Frist", [1]),  # Index 1 is relevant
        ("Selbstständige Krankenversicherung", [2, 3]),  # Indices 2 and 3 are relevant
    ]
    
    precision_results = tester.test_retrieval_precision(test_queries, test_corpus)
    
    # Summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    
    print("\n📈 Speed:")
    print(f"  Local: {speed_results['local']['speed']:.1f} embeddings/sec")
    print(f"  Azure: {speed_results['azure']['speed']:.1f} embeddings/sec")
    print(f"  Winner: Local ({speed_results['local']['speed']/speed_results['azure']['speed']:.1f}x faster)")
    
    print("\n🎯 Retrieval Precision:")
    print(f"  Local: {precision_results['avg_local']:.1%}")
    print(f"  Azure: {precision_results['avg_azure']:.1%}")
    improvement = (precision_results['avg_azure'] - precision_results['avg_local']) / precision_results['avg_local'] * 100
    if improvement > 5:
        print(f"  Winner: Azure ({improvement:+.1f}% better)")
    elif improvement < -5:
        print(f"  Winner: Local ({abs(improvement):.1f}% better)")
    else:
        print(f"  Winner: Tie (difference: {improvement:+.1f}%)")
    
    print("\n💰 Cost for 41,781 chunks:")
    print(f"  Local: $0.00")
    print(f"  Azure: ~$0.82")
    
    print("\n⏱️  Time for 41,781 chunks:")
    print(f"  Local: ~7 minutes")
    print(f"  Azure: ~17 minutes (batch mode)")
    
    print("\n📊 Dimensions:")
    print(f"  Local: 768")
    print(f"  Azure: 3072 (4x more)")
    
    print("\n" + "="*80)
    print("RECOMMENDATION")
    print("="*80)
    
    if precision_results['avg_azure'] > precision_results['avg_local'] * 1.1:
        print("\n✅ Azure OpenAI shows significant quality improvement (>10%)")
        print("   Consider using Azure for production if budget allows.")
    elif precision_results['avg_azure'] > precision_results['avg_local'] * 1.05:
        print("\n⚖️  Azure OpenAI shows marginal quality improvement (5-10%)")
        print("   Local is sufficient unless you need the extra edge.")
    else:
        print("\n✅ Local embeddings perform equivalently to Azure")
        print("   Stick with local: faster, free, same quality!")
    
    print("\n")
    tester.driver.close()
    
    return 0


if __name__ == "__main__":
    exit(main())
