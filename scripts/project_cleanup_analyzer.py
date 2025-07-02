import hashlib
from pathlib import Path


class ProjectAnalyzer:
    """
    Analyzes a project directory to identify potential areas for cleanup.

    Detects duplicate files (by content), similarly named files,
    potentially outdated debug artifacts, and large files.
    """

    def __init__(self, root_path):
        """Initializes the analyzer."""
        self.root_path = Path(root_path)
        self.file_hashes = {}
        self.file_sizes = {}
        self.file_paths = []
        self.report = []

        self.exclude_patterns = [
            '__pycache__', '.git', '.idea', '.vscode', 'node_modules', '.venv',
            'celerybeat-schedule', '.cursor-cache', 'uv.lock', 'yarn.lock',
            'package.json', 'project_cleanup_report.txt',
            'project_cleanup_analyzer.py', '.mypy_cache', '.pytest_cache',
            '.next', 'build', 'dist'
        ]
        self.debug_patterns = [
            'debug_', 'test_', 'rockwool_', '_results.json', '.html'
        ]

    def _should_exclude(self, path):
        """Check if a path should be excluded from analysis."""
        path_str = str(path)
        return any(part in path.parts for part in self.exclude_patterns) or \
            any(path_str.endswith(p) for p in self.exclude_patterns)

    def _calculate_hash(self, filepath):
        """Calculates the SHA256 hash of a file."""
        h = hashlib.sha256()
        try:
            with open(filepath, 'rb') as f:
                while True:
                    chunk = f.read(8192)
                    if not chunk:
                        break
                    h.update(chunk)
            return h.hexdigest()
        except (IOError, OSError):
            return None  # Could not read file

    def analyze(self):
        """Performs a multi-pass analysis of the project directory."""
        print("Starting project analysis...")
        self._gather_file_info()
        self._find_content_duplicates()
        self._find_similarly_named_files()
        self._find_potentially_unnecessary_files()
        self._find_large_files()
        print(f"Analysis complete. Found {len(self.report)} potential issues.")

    def _gather_file_info(self):
        """Recursively walks the directory to gather file paths and sizes."""
        print("Pass 1: Gathering file paths and sizes...")
        for path in self.root_path.rglob('*'):
            if self._should_exclude(path):
                continue
            if path.is_file():
                self.file_paths.append(path)
                try:
                    self.file_sizes[str(path)] = path.stat().st_size
                except FileNotFoundError:
                    continue
        print(f"Found {len(self.file_paths)} files to analyze.")

    def _find_content_duplicates(self):
        """Finds files with identical content by comparing their hashes."""
        print("Pass 2: Finding content duplicates...")
        for path in self.file_paths:
            file_hash = self._calculate_hash(path)
            if file_hash:
                if file_hash in self.file_hashes:
                    self.file_hashes[file_hash].append(str(path))
                else:
                    self.file_hashes[file_hash] = [str(path)]

        for file_hash, paths in self.file_hashes.items():
            if len(paths) > 1:
                self.report.append({
                    'type': 'CONTENT DUPLICATE',
                    'files': paths,
                    'recommendation': 'Review and remove one or more versions.',
                    'details': (f'These {len(paths)} files have the exact '
                                f'same content.')
                })

    def _find_similarly_named_files(self):
        """Finds files with similar names, suggesting potential redundancy."""
        print("Pass 3: Finding similarly named files...")
        base_names = {}
        for path in self.file_paths:
            base_name = path.stem.replace(
                '_final', ''
            ).replace(
                '_simple', ''
            ).lower()
            if base_name in base_names:
                base_names[base_name].append(str(path))
            else:
                base_names[base_name] = [str(path)]

        for base_name, paths in base_names.items():
            if len(paths) > 1:
                if base_name == '__init__':  # Common, not an issue
                    continue
                self.report.append({
                    'type': 'SIMILAR FILENAMES',
                    'files': paths,
                    'recommendation': ('Review if these files serve a '
                                     'redundant purpose.'),
                    'details': f'Files with similar base name: "{base_name}"'
                })

    def _find_potentially_unnecessary_files(self):
        """Identifies files that are likely temporary or generated artifacts."""
        print("Pass 4: Identifying potentially unnecessary files...")
        for path in self.file_paths:
            if any(p in path.name.lower() for p in self.debug_patterns):
                if 'project_cleanup' in path.name:
                    continue
                self.report.append({
                    'type': 'POTENTIALLY UNNECESSARY',
                    'files': [str(path)],
                    'recommendation': ('Review and delete if temporary '
                                     'debug/result file.'),
                    'details': f'Filename matches patterns: {self.debug_patterns}'
                })

    def _find_large_files(self, threshold_mb=5):
        """Identifies large files for potential git-lfs or removal."""
        print("Pass 5: Finding large files...")
        threshold_bytes = threshold_mb * 1024 * 1024
        for path, size in self.file_sizes.items():
            if size > threshold_bytes:
                self.report.append({
                    'type': 'LARGE FILE',
                    'files': [path],
                    'recommendation': ('Consider Git LFS or check if needed in '
                                     'repository.'),
                    'details': f'File size is {size / 1024 / 1024:.2f} MB.'
                })

    def generate_report(self, output_file):
        """Writes the analysis findings to a structured text file."""
        print(f"Generating report at {output_file}...")
        sorted_report = sorted(self.report, key=lambda x: x['type'])

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("Project Cleanup Analysis Report\n")
            f.write("=" * 40 + "\n\n")
            f.write(f"Analyzed {len(self.file_paths)} files in "
                    f"'{self.root_path}'.\n")
            f.write(f"Found {len(self.report)} potential issues to review.\n\n")

            current_type = ""
            for item in sorted_report:
                if item['type'] != current_type:
                    current_type = item['type']
                    f.write(f"\n---------- {current_type} ----------\n\n")

                f.write("Files:\n")
                for file_path in item['files']:
                    size_mb = self.file_sizes.get(file_path, 0) / 1024 / 1024
                    f.write(f"  - {file_path} ({size_mb:.2f} MB)\n")

                f.write(f"Details: {item['details']}\n")
                f.write(f"Recommendation: {item['recommendation']}\n")
                f.write("---\n")
        print("Report generation complete.")


if __name__ == "__main__":
    analyzer = ProjectAnalyzer('.')
    analyzer.analyze()
    analyzer.generate_report('project_cleanup_report.txt') 