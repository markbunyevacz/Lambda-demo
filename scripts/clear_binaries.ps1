# PowerShell script to remove binary files and large directories from Git index
# It does NOT delete the files from your local disk.
# After running this script, you should manually upload these files to your object storage.

Write-Host "Untracking binary files and directories from Git..."

# Remove PDF directories
try { git rm -r --cached src/downloads } catch { Write-Host "src/downloads not tracked" }
try { git rm -r --cached src/backend/data } catch { Write-Host "src/backend/data not tracked" }
try { git rm -r --cached downloads } catch { Write-Host "downloads not tracked" }

# Remove database files
try { git rm --cached --ignore-unmatch *.sqlite3 } catch { Write-Host "No .sqlite3 files tracked" }
try { git rm --cached --ignore-unmatch *.db } catch { Write-Host "No .db files tracked" }
try { git rm -r --cached --ignore-unmatch chromadb_data } catch { Write-Host "chromadb_data not tracked" }
try { git rm -r --cached --ignore-unmatch src/backend/chromadb_data } catch { Write-Host "src/backend/chromadb_data not tracked" }

# Remove log directories
try { git rm -r --cached --ignore-unmatch leier_scraping_reports } catch { Write-Host "leier_scraping_reports not tracked" }
try { git rm -r --cached --ignore-unmatch src/backend/leier_scraping_reports } catch { Write-Host "src/backend/leier_scraping_reports not tracked" }

# Remove individual log files
try { git rm --cached --ignore-unmatch *.log } catch { Write-Host "No .log files tracked" }

# Remove Celery schedule file
try { git rm --cached --ignore-unmatch celerybeat-schedule } catch { Write-Host "celerybeat-schedule not tracked" }
try { git rm --cached --ignore-unmatch src/backend/celerybeat-schedule } catch { Write-Host "src/backend/celerybeat-schedule not tracked" }

# Remove Chrome data files
try { git rm --cached --ignore-unmatch src/backend/chromadb_products_list.json } catch { Write-Host "chromadb_products_list.json not tracked" }
try { git rm --cached --ignore-unmatch src/backend/chromadb_products_list.txt } catch { Write-Host "chromadb_products_list.txt not tracked" }

Write-Host "Done."
Write-Host "Binary files have been untracked from Git. The .gitignore file has already been updated."
Write-Host "Consider uploading these files to your object storage provider."