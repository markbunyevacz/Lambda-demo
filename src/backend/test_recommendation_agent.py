import asyncio
from app.agents.recommendation_agent import RecommendationAgent
import logging

logging.basicConfig(level=logging.INFO)

async def main():
    """Main function to test the recommendation agent."""
    print("🧪 Testing Recommendation Agent with RAG...")
    agent = RecommendationAgent()
    
    # Test 1: English Query
    query1 = 'high-performance thermal insulation for flat roofs'
    print(f"\n1. Querying for: '{query1}'")
    results1 = await agent.generate_recommendations(user_query=query1)
    
    print("\nRecommendations:")
    if results1 and results1.get('recommendations'):
        for rec in results1['recommendations']:
            product = rec.get('product_details', {})
            print(f"  - {product.get('name')} (Score: {rec.get('similarity_score', 0):.2f})")
    else:
        print("  No recommendations found.")

    # Test 2: Hungarian Query
    query2 = 'tűzálló szigetelés magas hőmérsékletre'
    print(f"\n2. Querying for: '{query2}'")
    results2 = await agent.generate_recommendations(user_query=query2)

    print("\nRecommendations:")
    if results2 and results2.get('recommendations'):
        for rec in results2['recommendations']:
            product = rec.get('product_details', {})
            print(f"  - {product.get('name')} (Score: {rec.get('similarity_score', 0):.2f})")
    else:
        print("  No recommendations found.")

if __name__ == "__main__":
    asyncio.run(main()) 