# File Parser Agent

A document processing tool that extracts structured content from business documents and converts them into machine-readable formats.

## Features

- **Multi-format Support**: Parse PDF, Word (.docx), Excel (.xlsx), and PowerPoint (.pptx) files
- **Structured Output**: Convert to JSON, Markdown, CSV, or plain text
- **Text Extraction**: Pull all text content while preserving structure
- **Table Detection**: Extract tables with row/column data intact
- **Metadata Capture**: Get document properties (author, title, dates)
- **AI Vision Integration**: Describe images and charts using Claude API
- **Multiple Interfaces**: Web UI, CLI, Python API, and MCP Server for Claude Desktop

## Installation

```bash
# Basic installation
pip install -e .

# With AI vision support
pip install -e ".[vision]"

# With MCP server support
pip install -e ".[mcp]"

# Full installation with all features
pip install -e ".[all]"
```

## Quick Start

### Python API

```python
from src.api import FileParserAgent

# Initialize agent
agent = FileParserAgent()

# Parse a document
result = agent.parse_document('report.pdf')

# Extract just text
text = agent.extract_text('document.docx')

# Extract tables
tables = agent.extract_tables('data.xlsx')

# Save output as Markdown
agent.save_output(result, format='markdown')
```

### Command Line Interface

```bash
# Parse a document
file-parser-cli parse document.pdf

# Parse and output as Markdown
file-parser-cli parse report.docx --format markdown

# Extract text only
file-parser-cli extract-text presentation.pptx

# Extract tables as CSV
file-parser-cli extract-tables data.xlsx --format csv

# Interactive mode
file-parser-cli chat

# List saved outputs
file-parser-cli list

# Show supported formats
file-parser-cli info
```

### Web Interface

```bash
# Start web server
python run_web.py

# Or using the module
python -m src web

# Open http://localhost:5000 in your browser
```

### MCP Server (Claude Desktop)

Add to your Claude Desktop configuration (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "file-parser-agent": {
      "command": "python",
      "args": ["-m", "src", "mcp"],
      "env": {
        "ANTHROPIC_API_KEY": "your-api-key-here"
      }
    }
  }
}
```

Then ask Claude to parse documents using the available tools:
- `parse_document` - Extract content from any supported file
- `extract_text` - Get plain text from document
- `extract_tables` - Pull only table data
- `analyze_image` - Get AI descriptions of images
- `format_output` - Convert to JSON or Markdown
- `save_output` - Save results to file
- `list_outputs` - See previously parsed files

## Project Structure

```
file-parser-agent/
├── src/
│   ├── api/                # Python API wrapper
│   │   └── wrapper.py      # FileParserAgent class
│   ├── cli/                # Command-line interface
│   │   └── commands.py     # CLI commands
│   ├── mcp/                # MCP Server
│   │   └── server.py       # Claude Desktop integration
│   ├── parsers/            # Document parsers
│   │   ├── base.py         # Base parser class
│   │   ├── pdf_parser.py   # PDF parsing
│   │   ├── word_parser.py  # Word parsing
│   │   ├── excel_parser.py # Excel parsing
│   │   └── powerpoint_parser.py # PowerPoint parsing
│   ├── services/           # Core services
│   │   ├── parsing_engine.py # Orchestration
│   │   └── vision.py       # AI image analysis
│   ├── utils/              # Utilities
│   │   ├── validation.py   # File validation
│   │   └── output_manager.py # Output handling
│   ├── web/                # Flask web app
│   │   ├── app.py          # Flask application
│   │   └── templates/      # HTML templates
│   └── config.py           # Configuration
├── uploads/                # Temporary uploads
├── outputs/                # Saved outputs
├── logs/                   # Application logs
├── requirements.txt        # Dependencies
├── setup.py               # Package setup
└── pyproject.toml         # Project configuration
```

## Supported Formats

| Input Format | Extensions | Output Formats |
|-------------|------------|----------------|
| PDF | .pdf | JSON, Markdown, TXT |
| Word | .docx, .doc | JSON, Markdown, TXT |
| Excel | .xlsx, .xls | JSON, Markdown, CSV |
| PowerPoint | .pptx, .ppt | JSON, Markdown, TXT |

## Configuration

Set environment variables:

```bash
# For AI vision features
export ANTHROPIC_API_KEY="your-api-key"

# For web server
export SECRET_KEY="your-secret-key"
```

## Limitations

- Maximum file size: 50MB
- No OCR support (scanned documents won't extract text)
- Password-protected files not supported
- .doc and .xls formats have limited support (use .docx and .xlsx)

## Example Output

**PDF → JSON:**
```json
{
  "filename": "report.pdf",
  "file_type": "pdf",
  "parsed_at": "2024-01-15T10:30:00",
  "metadata": {
    "Author": "John Doe",
    "Title": "Annual Report",
    "page_count": 12
  },
  "content": {
    "total_pages": 12,
    "pages": [
      {"page_number": 1, "text": "..."}
    ]
  },
  "tables": [],
  "images": []
}
```

**PowerPoint → Markdown:**
```markdown
# Quarterly Review

## Slide 1: Introduction
Welcome to the Q4 review...

## Slide 2: Key Metrics
[Image: Bar chart showing 15% revenue growth]

| Metric | Q3 | Q4 |
|--------|-------|-------|
| Revenue | $1.2M | $1.4M |
```

## License

MIT License

## Slide 2: Key Metrics
[Image: Bar chart showing 15% revenue growth]
```

## Getting Started

Simply upload a document or provide a file path, and tell me what format you'd like the output in. I'll handle the rest.
