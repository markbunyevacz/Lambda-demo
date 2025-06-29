import os
import hashlib
from collections import defaultdict
from difflib import SequenceMatcher

def file_hash(filepath):
    """Compute SHA-256 hash of file content"""
    hasher = hashlib.sha256()
    with open(filepath, 'rb') as f:
        while chunk := f.read(4096):
            hasher.update(chunk)
    return hasher.hexdigest()

def similar(a, b):
    """Check if files are substantially similar (75%+ match)"""
    with open(a, 'r', encoding='utf-8', errors='ignore') as f1, \
         open(b, 'r', encoding='utf-8', errors='ignore') as f2:
        content1 = f1.read()
        content2 = f2.read()
        return SequenceMatcher(None, content1, content2).ratio() > 0.75

def scan_project(root_dir):
    """Scan project for duplicate and redundant files"""
    hash_groups = defaultdict(list)
    all_files = []
    
    for root, _, files in os.walk(root_dir):
        # Skip common directories that shouldn't be scanned
        if any(skip in root for skip in ['.git', '__pycache__', 'node_modules', 'venv']):
            continue
            
        for file in files:
            filepath = os.path.join(root, file)
            if os.path.getsize(filepath) == 0:  # Skip empty files
                continue
            all_files.append(filepath)
            file_id = f"{os.path.getsize(filepath)}-{file}"
            hash_groups[file_id].append(filepath)
    
    # Find exact duplicates
    exact_duplicates = {k: v for k, v in hash_groups.items() if len(v) > 1}
    
    # Find similar files
    similar_files = []
    file_ids = list(hash_groups.keys())
    for i in range(len(file_ids)):
        for j in range(i+1, len(file_ids)):
            group1 = hash_groups[file_ids[i]]
            group2 = hash_groups[file_ids[j]]
            for file1 in group1:
                for file2 in group2:
                    if similar(file1, file2):
                        similar_files.append((file1, file2))
    
    return exact_duplicates, similar_files

if __name__ == "__main__":
    project_root = os.path.dirname(os.path.abspath(__file__))
    duplicates, similar = scan_project(project_root)
    
    print("\nExact duplicates found:")
    for key, paths in duplicates.items():
        print(f"\n{key.split('-')[0]} byte files:")
        for path in paths:
            print(f"  - {os.path.relpath(path, project_root)}")
    
    print("\nSimilar files found:")
    for file1, file2 in similar:
        print(f"  - {os.path.relpath(file1, project_root)}")
        print(f"  - {os.path.relpath(file2, project_root)}")
        print() 