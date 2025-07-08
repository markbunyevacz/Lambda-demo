#!/usr/bin/env python3
"""
Lambda.hu Projekt Takarítási Script
===================================

Eltávolítja az ideiglenes fájlokat, tesztscripteket, debug fájlokat,
placeholder tartalmakat és szimuláció scripteket.

Kategóriák:
- Debug/teszt scriptek
- Extract/analyze scriptek  
- Show/list scriptek
- Rebuild/complete scriptek
- JSON report/adatfájlok
- Duplikált könyvtárak
- HTML debug fájlok
- Egyszer használt scriptek
"""

import os
import shutil
from pathlib import Path
from typing import List, Set

class ProjectCleaner:
    def __init__(self, dry_run: bool = True):
        self.dry_run = dry_run
        self.deleted_files: List[str] = []
        self.deleted_dirs: List[str] = []
        self.skipped_files: List[str] = []
        
    def clean_project(self):
        """Főfunkció - projekt teljes takarítása"""
        print("🧹 Lambda.hu Projekt Takarítás")
        print(f"{'🔍 DRY RUN MODE' if self.dry_run else '🚨 LIVE DELETION MODE'}")
        print("=" * 50)
        
        # Root könyvtár takarítása
        self._clean_root_directory()
        
        # Backend könyvtár takarítása
        self._clean_backend_directory()
        
        # Duplikált könyvtárak takarítása
        self._clean_duplicate_directories()
        
        # Eredmények kiírása
        self._print_summary()
    
    def _clean_root_directory(self):
        """Root könyvtár ideiglenes fájljainak takarítása"""
        print("\n📁 ROOT KÖNYVTÁR TAKARÍTÁSA")
        
        # Debug fájlok
        debug_files = [
            "debug_agent.py",
            "debug_env.py", 
            "debug_connect_args.py",
            "debug_live_database.py",
            "debug_database_utf8.py",
            "debug_utf8_position66.py",
            "debug_baumit_catalog.html"
        ]
        
        # Teszt fájlok
        test_files = [
            "test_agent.py",
            "test_leier_content.py", 
            "test_database_integration.py"
        ]
        
        # Extract/process scriptek
        extract_files = [
            "extract_pdf_data.py",
            "complete_pdf_extraction.py",
            "fix_pdf_metadata_extraction.py",
            "fix_metadata_extraction_docker.py",
            "fix_scraper_path.py"
        ]
        
        # Show/list/analyze scriptek
        show_files = [
            "show_real_pdf_results.py",
            "show_products.py",
            "create_products_list.py", 
            "simple_chromadb_list.py",
            "chromadb_products_list.py",
            "get_all_chroma_products.py",
            "list_all_chroma_products.py",
            "analyze_products.py"
        ]
        
        # Rebuild scriptek
        rebuild_files = [
            "rebuild_simple.py",
            "rebuild_chromadb_docker.py", 
            "rebuild_chromadb_with_specs.py"
        ]
        
        # Complete/demo/clean scriptek
        complete_files = [
            "complete_solution.py",
            "complete_duplicate_solution.py",
            "demo_database_integration.py",
            "clean_database_duplicates.py",
            "add_database_constraints.py",
            "verify_phase_2_completion.py",
            "database_analysis.py",
            "production_pdf_integration.py",
            "deduplication_manager.py"
        ]
        
        # Adatfájlok/reportok
        data_files = [
            "chromadb_products_list.csv",
            "chromadb_products_list.json", 
            "chromadb_products_list.txt",
            "real_pdf_tables_extracted.csv",
            "simple_processing_report_20250707_141058.json",
            "extraction_comparison_report.json",
            "scraper_output.log",
            "project_cleanup_report.txt",
            "rockwool_brightdata_mcp_results.json",
            "rockwool_prod_run.json",
            "rockwool_datasheets_summary.json",
            "rockwool_datasheets_complete.json",
            "termekadatlapok_components.json"
        ]
        
        # Összevonás és törlés
        all_root_files = (
            debug_files + test_files + extract_files + 
            show_files + rebuild_files + complete_files + data_files
        )
        
        for file_name in all_root_files:
            self._delete_file(file_name)
        
        # Könyvtárak törlése
        directories_to_remove = [
            "debug_baumit",
            "leier_scraping_reports",
            "reports",
            "factory",
            "shared"
        ]
        
        for dir_name in directories_to_remove:
            self._delete_directory(dir_name)
    
    def _clean_backend_directory(self):
        """Backend könyvtár ideiglenes fájljainak takarítása"""
        print("\n📁 BACKEND KÖNYVTÁR TAKARÍTÁSA")
        
        backend_path = Path("src/backend")
        
        # Debug/diagnose fájlok
        debug_files = [
            "debug_ai_analyzer.py",
            "diagnose_utf8.py",
            "diagnose_strategies.py"
        ]
        
        # Teszt/verify fájlok
        test_files = [
            "test_db.py",
            "test_rag_search.py",
            "test_recommendation_agent.py", 
            "verify_postgresql.py",
            "verify_chromadb_search.py"
        ]
        
        # Extract/show/analyze scriptek
        extract_show_files = [
            "extract_pdf_data.py",
            "show_real_pdf_results.py",
            "show_products.py",
            "create_products_list.py",
            "simple_chromadb_list.py", 
            "chromadb_products_list.py",
            "get_all_chroma_products.py",
            "list_all_chroma_products.py",
            "analyze_products.py"
        ]
        
        # Rebuild/complete scriptek
        rebuild_complete_files = [
            "rebuild_simple.py",
            "rebuild_chromadb_docker.py",
            "rebuild_chromadb_with_focused_data.py",
            "complete_pdf_extraction.py",
            "cleanup_test_data.py"
        ]
        
        # Check fájlok
        check_files = [
            "check_airrock_hd_fb1.py",
            "check_postgresql_data.py", 
            "check_chromadb.py"
        ]
        
        # Run scriptek
        run_files = [
            "run_brightdata_mcp.py",
            "run_brightdata_simple.py",
            "run_rag_pipeline_init.py"
        ]
        
        # Sync/fix fájlok
        sync_fix_files = [
            "sync_postgresql_to_chromadb.py",
            "fix_metadata_extraction_docker.py"
        ]
        
        # JSON adatfájlok/reportok
        json_data_files = [
            "raw_haiku_test_results.json",
            "complete_extraction_demo_results.json", 
            "openapi_debug.json",
            "production_pdf_report.json",
            "chromadb_products_list.txt",
            "chromadb_products_list.json",
            "chromadb_products_complete_list.json",
            "readable_products_report_20250701_113522.txt", 
            "complete_products_data_20250701_113522.json",
            "rockwool_brightdata_mcp_results.json",
            "rockwool_simple_mcp_results.json",
            "real_pdf_extraction_results.json"
        ]
        
        # HTML debug fájlok
        html_files = [
            "rockwool_datasheet_page.html"
        ]
        
        # Egyszer használt demo fájlok
        demo_files = [
            "simple_working_demo.py",
            "production_verification_report.py"
        ]
        
        # Dokumentáció (felesleges már)
        doc_files = [
            "DUPLICATE_CLEANUP_REPORT.md",
            "INSTALLATION_LOG.md",
            "README_BRIGHTDATA_MCP.md", 
            "BRIGHTDATA_MCP_COMPLETE_SETUP.md",
            "BRIGHTDATA_MCP_SETUP.md",
            "TROUBLESHOOTING.md"
        ]
        
        # Database fájlok
        db_files = [
            "test.db",
            "celerybeat-schedule"
        ]
        
        # Összevonás
        all_backend_files = (
            debug_files + test_files + extract_show_files + 
            rebuild_complete_files + check_files + run_files + 
            sync_fix_files + json_data_files + html_files + 
            demo_files + doc_files + db_files
        )
        
        for file_name in all_backend_files:
            self._delete_file(backend_path / file_name)
        
        # Backend könyvtárak törlése
        backend_directories = [
            "leier_scraping_reports",
            "reports", 
            "src",
            "chromadb_data",
            "data",
            "models",
            "processing",
            "tools"
        ]
        
        for dir_name in backend_directories:
            self._delete_directory(backend_path / dir_name)
    
    def _clean_duplicate_directories(self):
        """Duplikált könyvtárak takarítása"""
        print("\n📁 DUPLIKÁLT KÖNYVTÁRAK TAKARÍTÁSA")
        
        # Root szintű duplikált könyvtárak
        duplicate_dirs = [
            "chromadb_data",  # Van src/backend/chromadb_data is
            "__pycache__",
            ".mypy_cache"
        ]
        
        for dir_name in duplicate_dirs:
            self._delete_directory(dir_name)
    
    def _delete_file(self, file_path: Path | str):
        """Fájl törlése"""
        file_path = Path(file_path)
        
        if not file_path.exists():
            return
            
        if self.dry_run:
            print(f"   🗂️  [DRY RUN] Delete file: {file_path}")
            self.deleted_files.append(str(file_path))
        else:
            try:
                file_path.unlink()
                print(f"   ✅ Deleted file: {file_path}")
                self.deleted_files.append(str(file_path))
            except Exception as e:
                print(f"   ❌ Failed to delete {file_path}: {e}")
                self.skipped_files.append(str(file_path))
    
    def _delete_directory(self, dir_path: Path | str):
        """Könyvtár törlése"""
        dir_path = Path(dir_path)
        
        if not dir_path.exists() or not dir_path.is_dir():
            return
            
        if self.dry_run:
            print(f"   📁 [DRY RUN] Delete directory: {dir_path}")
            self.deleted_dirs.append(str(dir_path))
        else:
            try:
                shutil.rmtree(dir_path)
                print(f"   ✅ Deleted directory: {dir_path}")
                self.deleted_dirs.append(str(dir_path))
            except Exception as e:
                print(f"   ❌ Failed to delete {dir_path}: {e}")
                self.skipped_files.append(str(dir_path))
    
    def _print_summary(self):
        """Összefoglaló kiírása"""
        print("\n" + "=" * 50)
        print("📊 TAKARÍTÁSI ÖSSZEFOGLALÓ")
        print("=" * 50)
        print(f"📄 Fájlok törölve: {len(self.deleted_files)}")
        print(f"📁 Könyvtárak törölve: {len(self.deleted_dirs)}")
        print(f"⚠️  Sikertelen törlések: {len(self.skipped_files)}")
        
        if self.dry_run:
            print("\n🔍 DRY RUN MODE - Semmi sem lett ténylegesen törölve!")
            print("A tényleges törléshez futtasd: python cleanup_project_files.py --execute")
        else:
            print("\n✅ Takarítás befejezve!")
            
        # Részletes lista kérésre
        if len(self.deleted_files) > 0:
            print(f"\n📝 Törölt fájlok listája ({len(self.deleted_files)} db):")
            for file_path in sorted(self.deleted_files)[:20]:  # Első 20
                print(f"   - {file_path}")
            if len(self.deleted_files) > 20:
                print(f"   ... és még {len(self.deleted_files) - 20} fájl")

def main():
    import sys
    
    # Argumentum ellenőrzés
    dry_run = True
    if "--execute" in sys.argv:
        dry_run = False
        print("⚠️  LIVE DELETION MODE - Fájlok ténylegesen törlődni fognak!")
        confirmation = input("Biztos vagy benne? (igen/nem): ")
        if confirmation.lower() not in ['igen', 'yes', 'y']:
            print("❌ Törlés megszakítva.")
            return
    
    cleaner = ProjectCleaner(dry_run=dry_run)
    cleaner.clean_project()

if __name__ == "__main__":
    main() 