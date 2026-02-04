"""PDF document parser using PyPDF2."""

from pathlib import Path
from typing import Any, Dict, List
import logging

try:
    from PyPDF2 import PdfReader
    HAS_PYPDF2 = True
except ImportError:
    HAS_PYPDF2 = False

from .base import BaseDocumentParser, ParsedDocument

logger = logging.getLogger(__name__)


class PDFParser(BaseDocumentParser):
    """Parser for PDF documents.
    
    Extracts text, page structure, and metadata from PDF files
    using the PyPDF2 library.
    """
    
    SUPPORTED_EXTENSIONS = ['.pdf']
    
    def __init__(self, file_path: Path):
        if not HAS_PYPDF2:
            raise ImportError("PyPDF2 is required for PDF parsing. Install with: pip install PyPDF2")
        super().__init__(file_path)
        self._reader = None
    
    @property
    def reader(self) -> 'PdfReader':
        """Lazy-load PDF reader."""
        if self._reader is None:
            self._reader = PdfReader(str(self.file_path))
        return self._reader
    
    def parse(self) -> ParsedDocument:
        """Parse PDF and return structured content."""
        logger.info(f"Parsing PDF: {self.file_path}")
        
        doc = ParsedDocument(
            filename=self.file_path.name,
            file_type='pdf'
        )
        
        try:
            doc.metadata = self.extract_metadata()
            doc.content = {
                'total_pages': len(self.reader.pages),
                'pages': self._extract_pages()
            }
            doc.tables = self.extract_tables()
            doc.images = self.extract_images()
        except Exception as e:
            logger.error(f"Error parsing PDF: {e}")
            doc.errors.append(str(e))
        
        return doc
    
    def extract_text(self) -> str:
        """Extract all text from PDF."""
        text_parts = []
        for page in self.reader.pages:
            text = page.extract_text()
            if text:
                text_parts.append(text)
        return "\n\n".join(text_parts)
    
    def extract_metadata(self) -> Dict[str, Any]:
        """Extract PDF metadata."""
        metadata = {}
        if self.reader.metadata:
            # PyPDF2 metadata keys start with '/'
            for key, value in self.reader.metadata.items():
                clean_key = key.lstrip('/')
                if value:
                    metadata[clean_key] = str(value)
        
        metadata['page_count'] = len(self.reader.pages)
        return metadata
    
    def _extract_pages(self) -> List[Dict[str, Any]]:
        """Extract content from each page."""
        pages = []
        for i, page in enumerate(self.reader.pages, start=1):
            page_data = {
                'page_number': i,
                'text': page.extract_text() or '',
            }
            
            # Get page dimensions if available
            if page.mediabox:
                page_data['width'] = float(page.mediabox.width)
                page_data['height'] = float(page.mediabox.height)
            
            pages.append(page_data)
        
        return pages
    
    def extract_tables(self) -> List[Dict[str, Any]]:
        """Extract tables from PDF.
        
        Note: PyPDF2 doesn't have native table extraction.
        This is a basic implementation that could be enhanced
        with additional libraries like tabula-py or camelot.
        """
        # Basic implementation - tables are hard to detect in PDFs
        # without specialized libraries
        logger.debug("PDF table extraction is limited without tabula-py")
        return []
    
    def extract_images(self) -> List[Dict[str, Any]]:
        """Extract image references from PDF.
        
        Note: This extracts image metadata, not the actual images.
        Full image extraction requires additional processing.
        """
        images = []
        for page_num, page in enumerate(self.reader.pages, start=1):
            if '/XObject' in page.get('/Resources', {}):
                xobjects = page['/Resources']['/XObject'].get_object()
                for obj_name in xobjects:
                    obj = xobjects[obj_name]
                    if obj.get('/Subtype') == '/Image':
                        images.append({
                            'page': page_num,
                            'name': str(obj_name),
                            'width': obj.get('/Width'),
                            'height': obj.get('/Height'),
                            'color_space': str(obj.get('/ColorSpace', 'Unknown'))
                        })
        return images
