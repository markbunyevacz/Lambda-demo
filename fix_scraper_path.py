import fileinput
from pathlib import Path

# The problematic file
file_path = Path("src/backend/app/scrapers/rockwool_final/datasheet_scraper.py")

# The text to find and replace
old_text = "Path(__file__).resolve().parents[5]"
new_text = "Path(__file__).resolve().parents[3]"

print(f"Attempting to patch {file_path}...")

# Read the file and perform the replacement
try:
    with fileinput.FileInput(file_path, inplace=True, encoding='utf-8') as file:
        for line in file:
            print(line.replace(old_text, new_text), end='')
    print("Patch successful!")
except FileNotFoundError:
    print(f"Error: {file_path} not found.")
except Exception as e:
    print(f"An error occurred: {e}") 