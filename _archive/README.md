# Archive Directory

This directory contains archived code, documentation, scripts, and data that have been moved during cleanup and refactoring operations.

## Purpose

Instead of deleting files, we archive them here with full documentation of:
- **What** was archived
- **Why** it was archived
- **Where** it was moved from
- **When** it was archived
- **Replacement** (if applicable)

## Structure

```
_archive/
├── README.md                          # This file
├── code/                              # Archived code modules
│   └── YYYY-MM-DD-cleanup/
│       ├── ARCHIVE_LOG.md             # Detailed log of what/why/where
│       └── [archived files]
├── docs/                              # Archived documentation
│   └── YYYY-MM-DD-cleanup/
│       ├── ARCHIVE_LOG.md
│       └── [archived docs]
├── scripts/                           # Archived scripts
│   └── YYYY-MM-DD-cleanup/
│       ├── ARCHIVE_LOG.md
│       └── [archived scripts]
└── data/                              # Archived data files
    └── YYYY-MM-DD-cleanup/
        ├── ARCHIVE_LOG.md
        └── [archived data]
```

## Archive Log Format

Each archive operation creates an `ARCHIVE_LOG.md` file with the following structure:

```markdown
# Archive Log: [Operation Name]

**Date:** YYYY-MM-DD
**PR:** #N
**Branch:** devin/timestamp-branch-name

## Summary
Brief description of the archive operation.

## Archived Items

### [Item Name]
- **Original Path:** path/to/original/file
- **Archived Path:** _archive/category/date/file
- **Reason:** Why it was archived
- **Replacement:** New location or alternative (if applicable)
- **Safe to Delete:** Yes/No (after X time period)
```

## Retention Policy

- **Code:** Keep for 6 months, then review
- **Docs:** Keep for 3 months, then review
- **Scripts:** Keep for 6 months, then review
- **Data:** Keep for 1 month, then review

## Recovery

To recover an archived file:
1. Check the `ARCHIVE_LOG.md` in the relevant date folder
2. Copy the file back to its original location (or new location)
3. Update imports/references as needed
4. Document the recovery in the archive log
