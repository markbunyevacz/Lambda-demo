#!/bin/bash
# This script removes binary files and large directories from the Git index.
# It does NOT delete the files from your local disk.
# After running this script, you should manually upload these files to your object storage.

echo "Untracking binary files and directories from Git..."

# Remove PDF directories
git rm -r --cached src/downloads
git rm -r --cached src/backend/data
git rm -r --cached downloads

# Remove database files
git rm --cached --ignore-unmatch *.sqlite3
git rm --cached --ignore-unmatch *.db
git rm -r --cached --ignore-unmatch chromadb_data
git rm -r --cached --ignore-unmatch src/backend/chromadb_data

# Remove log directories
git rm -r --cached --ignore-unmatch leier_scraping_reports
git rm -r --cached --ignore-unmatch src/backend/leier_scraping_reports

# Remove individual log files
git rm --cached --ignore-unmatch *.log

# Remove Celery schedule file
git rm --cached --ignore-unmatch celerybeat-schedule

echo "Done."
echo "Please add the following to your .gitignore file:"
echo ""
echo "# Data and downloaded assets"
echo "/src/downloads/"
echo "/src/backend/data/"
echo "/downloads/"
echo ""
echo "# Local databases"
echo "*.sqlite3"
echo "*.db"
echo "/chromadb_data/"
echo "/src/backend/chromadb_data/"
echo ""
echo "# Log files and reports"
echo "/leier_scraping_reports/"
echo "/src/backend/leier_scraping_reports/"
echo "*.log"
echo ""
echo "# Celery artifacts"
echo "celerybeat-schedule"
