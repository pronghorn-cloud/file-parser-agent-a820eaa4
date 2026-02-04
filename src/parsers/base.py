"""Base document parser with abstract interface."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, Optional
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class ParsedDocument:
    """Structured representation of a parsed document."""
    filename: str
    file_type: str
    parsed_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)
    content: Dict[str, Any] = field(default_factory=dict)
    tables: list = field(default_factory=list)
    images: list = field(default_factory=list)
    errors: list = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            'filename': self.filename,
            'file_type': self.file_type,
            'parsed_at': self.parsed_at,
            'metadata': self.metadata,
            'content': self.content,
            'tables': self.tables,
            'images': self.images,
            'errors': self.errors
        }


class BaseDocumentParser(ABC):
    """Abstract base class for document parsers.
    
    Implements the Strategy pattern - each file type has its own
    parser implementation that follows this interface.
    """
    
    # Subclasses should define supported extensions
    SUPPORTED_EXTENSIONS: list = []
    
    def __init__(self, file_path: Path):
        """Initialize parser with file path.
        
        Args:
            file_path: Path to the document file
        """
        self.file_path = Path(file_path)
        self._validate_file()
    
    def _validate_file(self) -> None:
        """Validate that file exists and has correct extension."""
        if not self.file_path.exists():
            raise FileNotFoundError(f"File not found: {self.file_path}")
        
        if self.file_path.suffix.lower() not in self.SUPPORTED_EXTENSIONS:
            raise ValueError(
                f"Unsupported file extension: {self.file_path.suffix}. "
                f"Supported: {self.SUPPORTED_EXTENSIONS}"
            )
    
    @abstractmethod
    def parse(self) -> ParsedDocument:
        """Parse the document and return structured content.
        
        Returns:
            ParsedDocument with extracted content
        """
        pass
    
    @abstractmethod
    def extract_text(self) -> str:
        """Extract plain text content from document.
        
        Returns:
            Plain text string
        """
        pass
    
    @abstractmethod
    def extract_metadata(self) -> Dict[str, Any]:
        """Extract document metadata.
        
        Returns:
            Dictionary of metadata fields
        """
        pass
    
    def extract_tables(self) -> list:
        """Extract tables from document.
        
        Returns:
            List of table data structures
        """
        # Default implementation - override in subclasses that support tables
        return []
    
    def extract_images(self) -> list:
        """Extract image references from document.
        
        Returns:
            List of image data/references
        """
        # Default implementation - override in subclasses that support images
        return []
    
    @classmethod
    def can_parse(cls, file_path: Path) -> bool:
        """Check if this parser can handle the given file.
        
        Args:
            file_path: Path to check
            
        Returns:
            True if parser supports this file type
        """
        return Path(file_path).suffix.lower() in cls.SUPPORTED_EXTENSIONS
