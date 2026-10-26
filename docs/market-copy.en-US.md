# wangbin AI Document Assistant — Market Copy

## Name

wangbin AI Document Assistant

## Description

Helps everyday office users read, organize, and export common documents. It extracts content from PDF, Word, Excel, PowerPoint, HTML, TXT, and Markdown files, supports batch processing and spreadsheet deduplication, and reports failures and layout limitations honestly. Complex layouts, scans, and protected documents may require manual review.

## Audience

Office workers, administrative and finance teams, operations staff, and small and medium-sized businesses.

## Key features

- Single-file extraction with basic metadata and section information.
- Batch processing with per-file status and partial-failure reporting.
- XLSX worksheet inspection, duplicate detection, null counts, and safe export to a new file.
- Structured organization into source facts, key points, action items, and limitations.
- Read-only input, isolated output, path and size controls.

## Example prompts

- Organize the contents of this PDF.
- Deduplicate this Excel file and export a new file.
- Extract the key action items from this Word document.
- Create separate summaries for these documents.
- Extract tables from this PDF.
- Organize these materials into one report.

## Privacy

The assistant processes only files explicitly selected by the user, does not execute macros or dangerous formulas, and does not send documents to an unauthorized external service by default. The local candidate writes results to an isolated output directory and redacts sensitive paths and credentials from reports.

## Status

This is a local release candidate. It has not been uploaded to or approved by the WorkBuddy platform. Platform installation, runtime compatibility, and live conversation verification remain blocked pending authorized manual access.
