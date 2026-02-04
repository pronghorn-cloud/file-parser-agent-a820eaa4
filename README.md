# File Parser Agent

# File Parser Agent

A document processing tool that extracts structured content from business documents and converts them into machine-readable formats.

## What It Does

Upload PDF, Word, Excel, or PowerPoint files and get back clean, structured data in JSON or Markdown format. The agent extracts text, tables, metadata, and can describe images using AI vision.

## Supported Formats

| Input | Output |
|-------|--------|
| PDF (.pdf) | JSON |
| Word (.docx, .doc) | Markdown |
| Excel (.xlsx, .xls) | CSV |
| PowerPoint (.pptx, .ppt) | Plain text |

## Key Capabilities

- **Text Extraction** - Pull all text content while preserving structure (pages, slides, sheets)
- **Table Detection** - Extract tables with row/column data intact
- **Metadata Capture** - Get document properties (author, title, dates, etc.)
- **Image Analysis** - AI-powered descriptions of images and charts in presentations
- **Multiple Outputs** - Choose JSON for data processing or Markdown for readability

## How to Use

Ask me to:
- "Parse this PDF and give me the text"
- "Extract tables from this Excel file"
- "Summarize this PowerPoint presentation"
- "Convert this Word document to Markdown"
- "Describe the charts in this presentation"

## Available Tools

| Tool | Purpose |
|------|---------|
| `parse_document` | Extract content from any supported file |
| `analyze_image` | Get AI descriptions of images/charts |
| `format_output` | Convert to JSON or Markdown |
| `extract_tables` | Pull only table data |
| `save_output` | Save results to file |
| `list_outputs` | See previously parsed files |

## Limitations

- Maximum file size: 50MB
- No OCR (scanned documents won't extract text)
- No password-protected files
- Images are described, not extracted

## Example Output

**PDF → JSON:**
```json
{
  "filename": "report.pdf",
  "file_type": "pdf",
  "total_pages": 12,
  "pages": [
    {"page_number": 1, "text": "..."}
  ]
}
```

**PowerPoint → Markdown:**
```markdown
# Presentation Title

## Slide 1: Introduction
Welcome to the quarterly review...

## Slide 2: Key Metrics
[Image: Bar chart showing 15% revenue growth]
```

## Getting Started

Simply upload a document or provide a file path, and tell me what format you'd like the output in. I'll handle the rest.
