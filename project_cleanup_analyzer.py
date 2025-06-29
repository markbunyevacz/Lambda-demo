import os
import ast
import hashlib
import json
import time
from collections import defaultdict
from datetime import datetime, timedelta

def analyze_project(root_dir):
    """Comprehensive project analysis for redundancy and outdated files"""
    results = {
        'duplicate_files': defaultdict(list),
        'similar_functions': defaultdict(list),
        'outdated_files': [],
        'empty_dirs': [],
        'unused_dirs': [],
        'potential_deps': defaultdict(list)
    }
    
    # Thresholds for analysis
    OUTDATED_DAYS = 90  # Files not modified in 90 days
    LARGE_FILE_SIZE = 1024 * 1024  # 1MB
    FUNCTION_SIMILARITY_THRESHOLD = 0.8
    
    # Track dependencies
    dependency_files = {
        'requirements.txt': 'Python',
        'package.json': 'JavaScript',
        'pyproject.toml': 'Python'
    }
    
    # Walk through project
    file_hashes = defaultdict(list)
    function_defs = defaultdict(list)
    dir_file_counts = defaultdict(int)
    total_files = 0
    now = time.time()
    
    for root, dirs, files in os.walk(root_dir):
        # Skip common directories
        if any(skip in root for skip in ['.git', '__pycache__', 'node_modules', 'venv']):
            continue
            
        # Check for empty directories
        if not files and not dirs:
            results['empty_dirs'].append(root)
            
        # Count files in directory
        dir_file_counts[root] = len(files)
        total_files += len(files)
        
        for file in files:
            filepath = os.path.join(root, file)
            rel_path = os.path.relpath(filepath, root_dir)
            
            # Check for outdated files
            mod_time = os.path.getmtime(filepath)
            if now - mod_time > OUTDATED_DAYS * 86400:
                results['outdated_files'].append({
                    'path': rel_path,
                    'last_modified': datetime.fromtimestamp(mod_time).strftime('%Y-%m-%d')
                })
            
            # Analyze code files
            if file.endswith('.py'):
                # Function analysis
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        tree = ast.parse(f.read())
                        for node in ast.walk(tree):
                            if isinstance(node, ast.FunctionDef):
                                func_name = f"{file}:{node.name}"
                                func_code = ast.unparse(node)
                                func_hash = hashlib.sha256(func_code.encode()).hexdigest()
                                function_defs[func_hash].append({
                                    'file': rel_path,
                                    'name': node.name,
                                    'line': node.lineno
                                })
                except:
                    pass
                    
            # Dependency analysis
            if file in dependency_files:
                dep_type = dependency_files[file]
                results['potential_deps'][dep_type].append(rel_path)
            
            # File content analysis
            if os.path.getsize(filepath) > 0:  # Skip empty files
                file_hash = hashlib.sha256(open(filepath, 'rb').read()).hexdigest()
                file_hashes[file_hash].append(rel_path)
    
    # Identify duplicate files
    for hash_val, paths in file_hashes.items():
        if len(paths) > 1:
            results['duplicate_files'][hash_val] = paths
            
    # Identify similar functions
    for func_hash, funcs in function_defs.items():
        if len(funcs) > 1:
            results['similar_functions'][func_hash] = funcs
    
    # Identify unused directories (less than 1% of total files)
    avg_files_per_dir = total_files / max(1, len(dir_file_counts))
    for dir_path, count in dir_file_counts.items():
        if count < avg_files_per_dir * 0.01:  # Less than 1% of average
            results['unused_dirs'].append(dir_path)
    
    return results

def generate_report(results):
    """Generate a comprehensive report"""
    report = []
    
    # Duplicate files section
    if results['duplicate_files']:
        report.append("\n=== DUPLICATE FILES ===")
        for hash_val, paths in results['duplicate_files'].items():
            report.append(f"\nDuplicate content (hash: {hash_val[:8]}):")
            for path in paths:
                report.append(f"  - {path}")
    
    # Similar functions section
    if results['similar_functions']:
        report.append("\n\n=== SIMILAR FUNCTIONS ===")
        for func_hash, funcs in results['similar_functions'].items():
            report.append(f"\nSimilar function (hash: {func_hash[:8]}):")
            for func in funcs:
                report.append(f"  - {func['file']}: {func['name']}() at line {func['line']}")
    
    # Outdated files section
    if results['outdated_files']:
        report.append("\n\n=== OUTDATED FILES (90+ days) ===")
        for file in results['outdated_files']:
            report.append(f"  - {file['path']} (last modified: {file['last_modified']})")
    
    # Empty directories section
    if results['empty_dirs']:
        report.append("\n\n=== EMPTY DIRECTORIES ===")
        for dir_path in results['empty_dirs']:
            report.append(f"  - {dir_path}")
    
    # Unused directories section
    if results['unused_dirs']:
        report.append("\n\n=== UNDERUTILIZED DIRECTORIES ===")
        for dir_path in results['unused_dirs']:
            report.append(f"  - {dir_path}")
    
    # Dependency analysis
    if results['potential_deps']:
        report.append("\n\n=== DEPENDENCY MANAGEMENT ===")
        for dep_type, files in results['potential_deps'].items():
            report.append(f"\n{dep_type} dependency files:")
            for file in files:
                report.append(f"  - {file}")
    
    return "\n".join(report)

if __name__ == "__main__":
    project_root = os.path.dirname(os.path.abspath(__file__))
    print("Analyzing project structure and content...")
    analysis_results = analyze_project(project_root)
    report = generate_report(analysis_results)
    
    # Save report
    report_path = os.path.join(project_root, "project_cleanup_report.txt")
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"Analysis complete! Report saved to: {report_path}")
    print(f"\nSummary of findings:\n{'-'*30}")
    print(f"- {len(analysis_results['duplicate_files'])} duplicate file groups")
    print(f"- {len(analysis_results['similar_functions'])} similar function groups")
    print(f"- {len(analysis_results['outdated_files'])} outdated files")
    print(f"- {len(analysis_results['empty_dirs'])} empty directories")
    print(f"- {len(analysis_results['unused_dirs'])} underutilized directories") 