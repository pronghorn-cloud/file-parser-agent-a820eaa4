"""Output management for parsed documents."""

import json
import csv
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from datetime import datetime
import logging
import os

from ..config import OUTPUTS_DIR, OUTPUT_FORMATS
from ..parsers.base import ParsedDocument

logger = logging.getLogger(__name__)


class OutputManager:
    """Handles format conversion and persistence of parsed output.
    
    Supports output formats:
    - JSON: Machine-readable structured data
    - Markdown: Human-readable formatted text
    - CSV: Tabular data export
    - TXT: Plain text export
    """
    
    def __init__(self, output_dir: Path = None):
        """Initialize output manager.
        
        Args:
            output_dir: Directory for saving outputs (default: outputs/)
        """
        self.output_dir = Path(output_dir) if output_dir else OUTPUTS_DIR
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def save(
        self,
        document: Union[ParsedDocument, Dict[str, Any]],
        output_format: str = 'json',
        filename: str = None
    ) -> Path:
        """Save parsed document to file.
        
        Args:
            document: ParsedDocument or dict to save
            output_format: Output format ('json', 'markdown', 'csv', 'txt')
            filename: Custom filename (without extension)
            
        Returns:
            Path to saved file
        """
        output_format = output_format.lower()
        if output_format not in OUTPUT_FORMATS:
            raise ValueError(f"Unsupported format: {output_format}. Supported: {OUTPUT_FORMATS}")
        
        # Convert ParsedDocument to dict if needed
        if isinstance(document, ParsedDocument):
            data = document.to_dict()
        else:
            data = document
        
        # Generate filename if not provided
        if not filename:
            base_name = data.get('filename', 'output')
            base_name = Path(base_name).stem  # Remove original extension
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{base_name}_{timestamp}"
        
        # Add appropriate extension
        ext_map = {
            'json': '.json',
            'markdown': '.md',
            'csv': '.csv',
            'txt': '.txt'
        }
        output_path = self.output_dir / f"{filename}{ext_map[output_format]}"
        
        # Convert and save
        if output_format == 'json':
            self._save_json(data, output_path)
        elif output_format == 'markdown':
            self._save_markdown(data, output_path)
        elif output_format == 'csv':
            self._save_csv(data, output_path)
        elif output_format == 'txt':
            self._save_txt(data, output_path)
        
        logger.info(f"Saved output to: {output_path}")
        return output_path
    
    def _save_json(self, data: Dict[str, Any], path: Path) -> None:
        """Save as JSON."""
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)
    
    def _save_markdown(self, data: Dict[str, Any], path: Path) -> None:
        """Convert to Markdown and save."""
        md_content = self._to_markdown(data)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(md_content)
    
    def _save_csv(self, data: Dict[str, Any], path: Path) -> None:
        """Extract tables and save as CSV."""
        tables = data.get('tables', [])
        
        if not tables:
            # If no tables, create a simple key-value CSV
            with open(path, 'w', encoding='utf-8', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['Key', 'Value'])
                for key, value in self._flatten_dict(data).items():
                    writer.writerow([key, value])
        else:
            # Save first table (or combine tables)
            with open(path, 'w', encoding='utf-8', newline='') as f:
                writer = csv.writer(f)
                for table in tables:
                    table_data = table.get('data', [])
                    headers = table.get('headers', [])
                    if headers:
                        writer.writerow(headers)
                    for row in table_data:
                        writer.writerow(row)
                    writer.writerow([])  # Blank row between tables
    
    def _save_txt(self, data: Dict[str, Any], path: Path) -> None:
        """Extract plain text and save."""
        text_content = self._to_plain_text(data)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(text_content)
    
    def _to_markdown(self, data: Dict[str, Any]) -> str:
        """Convert parsed document to Markdown format."""
        lines = []
        
        # Title
        filename = data.get('filename', 'Document')
        lines.append(f"# {filename}\n")
        
        # Metadata
        metadata = data.get('metadata', {})
        if metadata:
            lines.append("## Metadata\n")
            for key, value in metadata.items():
                lines.append(f"- **{key}**: {value}")
            lines.append("")
        
        # Content based on file type
        file_type = data.get('file_type', '')
        content = data.get('content', {})
        
        if file_type == 'pdf':
            lines.extend(self._pdf_to_markdown(content))
        elif file_type == 'word':
            lines.extend(self._word_to_markdown(content))
        elif file_type == 'excel':
            lines.extend(self._excel_to_markdown(content))
        elif file_type == 'powerpoint':
            lines.extend(self._powerpoint_to_markdown(content))
        else:
            # Generic content
            lines.append("## Content\n")
            lines.append(str(content))
        
        # Tables
        tables = data.get('tables', [])
        if tables:
            lines.append("\n## Tables\n")
            for i, table in enumerate(tables, 1):
                lines.append(f"### Table {i}\n")
                lines.extend(self._table_to_markdown(table))
                lines.append("")
        
        # Images
        images = data.get('images', [])
        if images:
            lines.append("\n## Images\n")
            for i, img in enumerate(images, 1):
                desc = img.get('description', 'Image')
                lines.append(f"- **Image {i}**: {desc}")
        
        return "\n".join(lines)
    
    def _pdf_to_markdown(self, content: Dict) -> List[str]:
        """Convert PDF content to Markdown."""
        lines = []
        pages = content.get('pages', [])
        total_pages = content.get('total_pages', len(pages))
        
        lines.append(f"## Content ({total_pages} pages)\n")
        
        for page in pages:
            page_num = page.get('page_number', '?')
            text = page.get('text', '')
            lines.append(f"### Page {page_num}\n")
            lines.append(text)
            lines.append("")
        
        return lines
    
    def _word_to_markdown(self, content: Dict) -> List[str]:
        """Convert Word content to Markdown."""
        lines = []
        paragraphs = content.get('paragraphs', [])
        
        lines.append("## Content\n")
        
        for para in paragraphs:
            text = para.get('text', '')
            if para.get('is_heading'):
                level = para.get('heading_level', 2)
                # Offset heading levels (## for H1, ### for H2, etc.)
                lines.append(f"{'#' * (level + 1)} {text}\n")
            else:
                lines.append(text)
                lines.append("")
        
        return lines
    
    def _excel_to_markdown(self, content: Dict) -> List[str]:
        """Convert Excel content to Markdown."""
        lines = []
        sheets = content.get('sheets', [])
        
        for sheet in sheets:
            sheet_name = sheet.get('name', 'Sheet')
            lines.append(f"## {sheet_name}\n")
            
            data = sheet.get('data', [])
            if data:
                # Create markdown table
                if len(data) > 0:
                    # Header row
                    headers = data[0] if data else []
                    if headers:
                        lines.append("| " + " | ".join(str(h) if h else '' for h in headers) + " |")
                        lines.append("| " + " | ".join(['---'] * len(headers)) + " |")
                    
                    # Data rows
                    for row in data[1:]:
                        lines.append("| " + " | ".join(str(c) if c else '' for c in row) + " |")
            
            lines.append("")
        
        return lines
    
    def _powerpoint_to_markdown(self, content: Dict) -> List[str]:
        """Convert PowerPoint content to Markdown."""
        lines = []
        slides = content.get('slides', [])
        
        for slide in slides:
            slide_num = slide.get('slide_number', '?')
            title = slide.get('title', f'Slide {slide_num}')
            
            lines.append(f"## Slide {slide_num}: {title}\n")
            
            # Content
            for text in slide.get('content', []):
                if text and text.strip():
                    lines.append(text)
            
            # Images
            for img in slide.get('images', []):
                desc = img.get('description', 'Image')
                lines.append(f"\n*[Image: {desc}]*\n")
            
            # Charts
            for chart in slide.get('charts', []):
                title = chart.get('title', 'Chart')
                chart_type = chart.get('chart_type', 'Unknown')
                lines.append(f"\n*[{chart_type}: {title}]*\n")
            
            # Notes
            notes = slide.get('notes')
            if notes:
                lines.append(f"\n> **Speaker Notes**: {notes}\n")
            
            lines.append("---\n")
        
        return lines
    
    def _table_to_markdown(self, table: Dict) -> List[str]:
        """Convert table data to Markdown table."""
        lines = []
        headers = table.get('headers', [])
        data = table.get('data', [])
        
        # If no separate headers, use first row
        if not headers and data:
            headers = data[0]
            data = data[1:]
        
        if headers:
            lines.append("| " + " | ".join(str(h) if h else '' for h in headers) + " |")
            lines.append("| " + " | ".join(['---'] * len(headers)) + " |")
        
        for row in data:
            lines.append("| " + " | ".join(str(c) if c else '' for c in row) + " |")
        
        return lines
    
    def _to_plain_text(self, data: Dict[str, Any]) -> str:
        """Convert parsed document to plain text."""
        lines = []
        
        # Title
        filename = data.get('filename', 'Document')
        lines.append(f"{filename}")
        lines.append("=" * len(filename))
        lines.append("")
        
        # Extract text based on file type
        file_type = data.get('file_type', '')
        content = data.get('content', {})
        
        if file_type == 'pdf':
            for page in content.get('pages', []):
                lines.append(page.get('text', ''))
                lines.append("")
        elif file_type == 'word':
            for para in content.get('paragraphs', []):
                lines.append(para.get('text', ''))
        elif file_type == 'excel':
            for sheet in content.get('sheets', []):
                lines.append(f"\n[{sheet.get('name', 'Sheet')}]\n")
                for row in sheet.get('data', []):
                    lines.append("\t".join(str(c) if c else '' for c in row))
        elif file_type == 'powerpoint':
            for slide in content.get('slides', []):
                title = slide.get('title', f"Slide {slide.get('slide_number')}")
                lines.append(f"\n[{title}]\n")
                for text in slide.get('content', []):
                    if text:
                        lines.append(text)
        
        return "\n".join(lines)
    
    def _flatten_dict(self, d: Dict, parent_key: str = '', sep: str = '.') -> Dict:
        """Flatten nested dictionary."""
        items = []
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(self._flatten_dict(v, new_key, sep).items())
            elif isinstance(v, list):
                items.append((new_key, str(v)))
            else:
                items.append((new_key, v))
        return dict(items)
    
    def list_outputs(self) -> List[Dict[str, Any]]:
        """List all saved output files.
        
        Returns:
            List of file info dictionaries
        """
        outputs = []
        for path in self.output_dir.iterdir():
            if path.is_file():
                stat = path.stat()
                outputs.append({
                    'filename': path.name,
                    'path': str(path),
                    'size_bytes': stat.st_size,
                    'created': datetime.fromtimestamp(stat.st_ctime).isoformat(),
                    'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    'format': path.suffix.lstrip('.')
                })
        
        return sorted(outputs, key=lambda x: x['modified'], reverse=True)
    
    def delete_output(self, filename: str) -> bool:
        """Delete an output file.
        
        Args:
            filename: Name of file to delete
            
        Returns:
            True if deleted, False if not found
        """
        path = self.output_dir / filename
        if path.exists() and path.is_file():
            path.unlink()
            logger.info(f"Deleted output: {filename}")
            return True
        return False
    
    def clear_outputs(self) -> int:
        """Delete all output files.
        
        Returns:
            Number of files deleted
        """
        count = 0
        for path in self.output_dir.iterdir():
            if path.is_file():
                path.unlink()
                count += 1
        
        logger.info(f"Cleared {count} output files")
        return count
    
    def get_output(self, filename: str) -> Optional[Path]:
        """Get path to an output file.
        
        Args:
            filename: Name of file to get
            
        Returns:
            Path if exists, None otherwise
        """
        path = self.output_dir / filename
        return path if path.exists() else None
