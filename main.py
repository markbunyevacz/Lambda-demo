"""
Lambda.hu Építőanyag AI Rendszer - Entry Point
============================================

Ez a fő belépési pont a Lambda.hu AI rendszer számára.
Használja a backend/run_demo_scrape.py-t a demo funkcionalitáshoz.
"""

import sys
import os

# Add backend to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))


def main():
    """
    Fő belépési pont a Lambda.hu AI rendszerhez.
    """
    print("🏗️  Lambda.hu Építőanyag AI Rendszer")
    print("=" * 50)
    print("📋 Elérhető parancsok:")
    print("   🚀 uv run lambda-demo    - Demo scraping futtatása")
    print("   🔧 docker-compose up    - Teljes rendszer indítása")
    print("   📖 http://localhost:8000/docs - API dokumentáció")
    print()
    print("💡 További információ: README.md")


if __name__ == "__main__":
    main()
