#!/usr/bin/env python3
"""
ChromaDB Vector Search Verification Script
Tests vector embeddings, search functionality, and retrieval quality
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import chromadb
from chromadb.config import Settings

# Add backend to path
sys.path.append('.')

def test_chromadb_connection():
    """Test ChromaDB connectivity and collection status"""
    
    print("🔍 CHROMADB VECTOR SEARCH VERIFICATION")
    print("=" * 60)
    
    try:
        # Connect to ChromaDB
        client = chromadb.PersistentClient(path='./chromadb_data')
        print("✅ ChromaDB client connected successfully")
        
        # List collections
        collections = client.list_collections()
        print(f"📋 Available collections: {len(collections)}")
        
        for collection in collections:
            print(f"   📁 {collection.name}")
            
        return client, collections
        
    except Exception as e:
        print(f"❌ ChromaDB connection failed: {e}")
        return None, None

def test_vector_search(client, collection_name="pdf_products"):
    """Test vector search functionality with real queries"""
    
    if not client:
        print("❌ No ChromaDB client available")
        return False
        
    print(f"\n🔍 TESTING VECTOR SEARCH")
    print("=" * 40)
    
    try:
        # Get collection
        collection = client.get_collection(collection_name)
        
        # Check collection stats
        count = collection.count()
        print(f"📊 Documents in collection: {count}")
        
        if count == 0:
            print("⚠️ No documents in collection to search")
            return False
            
        # Peek at some documents
        peek_results = collection.peek(3)
        print(f"📄 Sample documents available: {len(peek_results['documents'])}")
        
        # Test search queries
        test_queries = [
            "hőszigetelés homlokzat",  # Hungarian: facade insulation
            "thermal conductivity",    # English technical term
            "kőzetgyapot",            # Hungarian: rock wool
            "building insulation",     # General building term
            "ROCKWOOL",               # Brand name
            "density kg/m3"           # Technical specification
        ]
        
        search_results = {}
        
        for query in test_queries:
            print(f"\n🔍 Testing query: '{query}'")
            
            try:
                # Perform vector search
                results = collection.query(
                    query_texts=[query],
                    n_results=3,
                    include=['documents', 'metadatas', 'distances']
                )
                
                if results['documents'] and results['documents'][0]:
                    print(f"   ✅ Found {len(results['documents'][0])} results")
                    
                    # Show top result
                    top_doc = results['documents'][0][0]
                    top_metadata = results['metadatas'][0][0] if results['metadatas'][0] else {}
                    top_distance = results['distances'][0][0] if results['distances'][0] else 'N/A'
                    
                    print(f"   📄 Top result:")
                    print(f"      Product: {top_metadata.get('product_name', 'Unknown')}")
                    print(f"      Distance: {top_distance}")
                    print(f"      Content preview: {top_doc[:100]}...")
                    
                    search_results[query] = {
                        'found_results': len(results['documents'][0]),
                        'top_distance': top_distance,
                        'top_product': top_metadata.get('product_name', 'Unknown')
                    }
                    
                else:
                    print(f"   ⚠️ No results found")
                    search_results[query] = {'found_results': 0}
                    
            except Exception as e:
                print(f"   ❌ Search failed: {e}")
                search_results[query] = {'error': str(e)}
        
        # Analyze search quality
        print(f"\n📊 SEARCH QUALITY ANALYSIS")
        print("=" * 30)
        
        successful_searches = [q for q, r in search_results.items() 
                             if 'error' not in r and r.get('found_results', 0) > 0]
        
        print(f"✅ Successful searches: {len(successful_searches)}/{len(test_queries)}")
        
        if successful_searches:
            # Calculate average distance (lower is better)
            distances = [r['top_distance'] for q, r in search_results.items() 
                        if 'top_distance' in r and isinstance(r['top_distance'], (int, float))]
            
            if distances:
                avg_distance = sum(distances) / len(distances)
                print(f"📈 Average search distance: {avg_distance:.3f} (lower is better)")
            
            # Show best performing queries
            print(f"\n🏆 Best performing queries:")
            for query in successful_searches[:3]:
                result = search_results[query]
                print(f"   '{query}' → {result['top_product']}")
        
        return len(successful_searches) > 0
        
    except Exception as e:
        print(f"❌ Vector search test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_semantic_search_quality(client, collection_name="pdf_products"):
    """Test semantic search quality with specific building material queries"""
    
    if not client:
        return False
        
    print(f"\n🧠 TESTING SEMANTIC SEARCH QUALITY")
    print("=" * 40)
    
    try:
        collection = client.get_collection(collection_name)
        
        # Advanced semantic queries
        semantic_tests = [
            {
                'query': 'What insulation is good for facades?',
                'expected_terms': ['homlokzat', 'facade', 'insulation', 'hőszigetelés']
            },
            {
                'query': 'Low thermal conductivity materials',
                'expected_terms': ['thermal', 'conductivity', 'hővezetés']
            },
            {
                'query': 'Fire resistant building materials',
                'expected_terms': ['fire', 'tűz', 'resistant', 'álló']
            }
        ]
        
        semantic_scores = []
        
        for test in semantic_tests:
            query = test['query']
            expected_terms = test['expected_terms']
            
            print(f"\n🔍 Semantic test: '{query}'")
            
            results = collection.query(
                query_texts=[query],
                n_results=5,
                include=['documents', 'metadatas', 'distances']
            )
            
            if results['documents'] and results['documents'][0]:
                # Check if results contain expected terms
                all_text = ' '.join(results['documents'][0]).lower()
                
                found_terms = [term for term in expected_terms 
                             if term.lower() in all_text]
                
                relevance_score = len(found_terms) / len(expected_terms)
                semantic_scores.append(relevance_score)
                
                print(f"   📊 Relevance score: {relevance_score:.2f}")
                print(f"   ✅ Found terms: {found_terms}")
                print(f"   📄 Top result: {results['metadatas'][0][0].get('product_name', 'Unknown')}")
                
            else:
                print(f"   ❌ No results found")
                semantic_scores.append(0)
        
        # Overall semantic quality
        if semantic_scores:
            avg_semantic_score = sum(semantic_scores) / len(semantic_scores)
            print(f"\n🎯 Overall semantic quality: {avg_semantic_score:.2f}")
            
            if avg_semantic_score > 0.6:
                print("   ✅ Excellent semantic search quality")
            elif avg_semantic_score > 0.4:
                print("   ⚠️ Good semantic search quality")
            else:
                print("   ❌ Poor semantic search quality - needs improvement")
                
            return avg_semantic_score > 0.4
        
        return False
        
    except Exception as e:
        print(f"❌ Semantic search test failed: {e}")
        return False

def test_embeddings_quality(client, collection_name="pdf_products"):
    """Test embedding quality by checking document similarity"""
    
    if not client:
        return False
        
    print(f"\n🔗 TESTING EMBEDDINGS QUALITY")
    print("=" * 30)
    
    try:
        collection = client.get_collection(collection_name)
        
        # Get some sample documents
        peek_results = collection.peek(10)
        
        if not peek_results['documents']:
            print("⚠️ No documents available for embeddings test")
            return False
            
        print(f"📄 Testing with {len(peek_results['documents'])} documents")
        
        # Test document similarity
        sample_doc = peek_results['documents'][0]
        sample_metadata = peek_results['metadatas'][0] if peek_results['metadatas'] else {}
        
        print(f"🔍 Using reference document: {sample_metadata.get('product_name', 'Unknown')}")
        
        # Search for similar documents using the document content
        similarity_results = collection.query(
            query_texts=[sample_doc[:500]],  # Use first 500 chars
            n_results=5,
            include=['documents', 'metadatas', 'distances']
        )
        
        if similarity_results['documents'] and similarity_results['documents'][0]:
            print(f"   ✅ Found {len(similarity_results['documents'][0])} similar documents")
            
            # Check if the same document is the top result (should be distance ~0)
            top_distance = similarity_results['distances'][0][0]
            print(f"   📊 Self-similarity distance: {top_distance:.6f}")
            
            if top_distance < 0.1:
                print("   ✅ Excellent embedding quality (low self-distance)")
                return True
            elif top_distance < 0.3:
                print("   ⚠️ Good embedding quality")
                return True
            else:
                print("   ❌ Poor embedding quality (high self-distance)")
                return False
        
        return False
        
    except Exception as e:
        print(f"❌ Embeddings quality test failed: {e}")
        return False

def main():
    """Main verification function"""
    
    print("🚀 CHROMADB VECTOR SEARCH VERIFICATION")
    print("Testing embeddings, search functionality, and retrieval quality")
    print()
    
    # Load environment
    load_dotenv("../../.env")
    
    # Test ChromaDB connection
    client, collections = test_chromadb_connection()
    
    if not client or not collections:
        print("\n❌ ChromaDB verification failed - no connection or collections")
        return
    
    # Test vector search
    search_success = test_vector_search(client)
    
    # Test semantic search quality
    semantic_success = test_semantic_search_quality(client)
    
    # Test embeddings quality
    embeddings_success = test_embeddings_quality(client)
    
    # Final assessment
    print(f"\n🎉 CHROMADB VERIFICATION RESULTS")
    print("=" * 40)
    print(f"   ✅ Connection: {'PASS' if client else 'FAIL'}")
    print(f"   ✅ Vector Search: {'PASS' if search_success else 'FAIL'}")
    print(f"   ✅ Semantic Quality: {'PASS' if semantic_success else 'FAIL'}")
    print(f"   ✅ Embeddings Quality: {'PASS' if embeddings_success else 'FAIL'}")
    
    if all([client, search_success, semantic_success, embeddings_success]):
        print(f"\n🚀 ChromaDB is PRODUCTION READY for vector search!")
    elif client and search_success:
        print(f"\n⚠️ ChromaDB basic functionality works, quality needs improvement")
    else:
        print(f"\n❌ ChromaDB needs debugging before production use")

if __name__ == "__main__":
    main() 