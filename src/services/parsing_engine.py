"""Parsing engine that orchestrates document parsing."""

import base64
from pathlib import Path
from typing import Any, Dict, Optional, Type
import logging

from ..parsers.base import BaseDocumentParser, ParsedDocument
from ..parsers.pdf_parser import PDFParser
from ..parsers.word_parser import WordParser
from ..parsers.excel_parser import ExcelParser
from ..parsers.powerpoint_parser import PowerPointParser
from ..utils.validation import FileValidator, ValidationError
from .vision import VisionService

logger = logging.getLogger(__name__)


# Registry of available parsers
PARSER_REGISTRY: Dict[str, Type[BaseDocumentParser]] = {
    'pdf': PDFParser,
    'word': WordParser,
    'excel': ExcelParser,
    'powerpoint': PowerPointParser,
}


class ParsingEngine:
    """Central parsing engine that orchestrates document processing.
    
    Features:
    - Automatic parser selection based on file type
    - File validation before parsing
    - Optional AI vision integration for images
    - Unified interface for all document types
    """
    
    def __init__(
        self,
        enable_vision: bool = True,
        vision_service: VisionService = None
    ):
        """Initialize parsing engine.
        
        Args:
            enable_vision: Whether to enable AI image analysis
            vision_service: Custom vision service instance
        """
        self.validator = FileValidator()
        self.enable_vision = enable_vision
        self._vision_service = vision_service
    
    @property
    def vision_service(self) -> Optional[VisionService]:
        """Lazy-load vision service."""
        if self.enable_vision and self._vision_service is None:
            try:
                self._vision_service = VisionService()
            except ImportError as e:
                logger.warning(f"Vision service unavailable: {e}")
                self.enable_vision = False
        return self._vision_service
    
    def parse(
        self,
        file_path: Path,
        analyze_images: bool = True
    ) -> ParsedDocument:
        """Parse a document file.
        
        Args:
            file_path: Path to document
            analyze_images: Whether to analyze images with AI
            
        Returns:
            ParsedDocument with extracted content
            
        Raises:
            ValidationError: If file fails validation
            ValueError: If file type is unsupported
        """
        file_path = Path(file_path)
        logger.info(f"Parsing document: {file_path}")
        
        # Validate file
        is_valid, error = self.validator.validate(file_path)
        if not is_valid:
            raise ValidationError(error)
        
        # Get parser for file type
        parser = self._get_parser(file_path)
        
        # Parse document
        document = parser.parse()
        
        # Analyze images if enabled
        if analyze_images and self.enable_vision and document.images:
            document = self._analyze_document_images(document)
        
        return document
    
    def parse_to_dict(self, file_path: Path, **kwargs) -> Dict[str, Any]:
        """Parse document and return as dictionary.
        
        Args:
            file_path: Path to document
            **kwargs: Additional arguments for parse()
            
        Returns:
            Dictionary representation of parsed document
        """
        doc = self.parse(file_path, **kwargs)
        return doc.to_dict()
    
    def extract_text(self, file_path: Path) -> str:
        """Extract plain text from document.
        
        Args:
            file_path: Path to document
            
        Returns:
            Plain text content
        """
        file_path = Path(file_path)
        
        # Validate
        is_valid, error = self.validator.validate(file_path)
        if not is_valid:
            raise ValidationError(error)
        
        parser = self._get_parser(file_path)
        return parser.extract_text()
    
    def extract_tables(self, file_path: Path) -> list:
        """Extract only tables from document.
        
        Args:
            file_path: Path to document
            
        Returns:
            List of table data structures
        """
        file_path = Path(file_path)
        
        # Validate
        is_valid, error = self.validator.validate(file_path)
        if not is_valid:
            raise ValidationError(error)
        
        parser = self._get_parser(file_path)
        return parser.extract_tables()
    
    def extract_metadata(self, file_path: Path) -> Dict[str, Any]:
        """Extract only metadata from document.
        
        Args:
            file_path: Path to document
            
        Returns:
            Dictionary of metadata
        """
        file_path = Path(file_path)
        
        # Validate
        is_valid, error = self.validator.validate(file_path)
        if not is_valid:
            raise ValidationError(error)
        
        parser = self._get_parser(file_path)
        return parser.extract_metadata()
    
    def _get_parser(self, file_path: Path) -> BaseDocumentParser:
        """Get appropriate parser for file type.
        
        Args:
            file_path: Path to file
            
        Returns:
            Parser instance
            
        Raises:
            ValueError: If no parser available
        """
        file_type = self.validator.get_file_type(file_path)
        
        if file_type not in PARSER_REGISTRY:
            raise ValueError(f"No parser available for file type: {file_type}")
        
        parser_class = PARSER_REGISTRY[file_type]
        return parser_class(file_path)
    
    def _analyze_document_images(
        self,
        document: ParsedDocument
    ) -> ParsedDocument:
        """Analyze images in document using vision service.
        
        Args:
            document: Parsed document with images
            
        Returns:
            Document with image descriptions added
        """
        if not self.vision_service or not self.vision_service.is_available:
            logger.warning("Vision service not available for image analysis")
            return document
        
        analyzed_images = []
        for img in document.images:
            # Check if image has blob data
            blob_b64 = img.get('blob')
            if blob_b64:
                try:
                    blob = base64.b64decode(blob_b64)
                    content_type = img.get('content_type', 'image/png')
                    
                    # Determine analysis type
                    if 'chart' in str(img.get('name', '')).lower():
                        result = self.vision_service.analyze_chart(blob, content_type)
                    else:
                        result = self.vision_service.analyze_image(blob, content_type)
                    
                    if result.get('success'):
                        img['description'] = result.get('description', '')
                        img['ai_analyzed'] = True
                    else:
                        img['description'] = 'Image analysis failed'
                        img['ai_error'] = result.get('error')
                        
                except Exception as e:
                    logger.error(f"Error analyzing image: {e}")
                    img['description'] = 'Error analyzing image'
                    img['ai_error'] = str(e)
            
            analyzed_images.append(img)
        
        document.images = analyzed_images
        return document
    
    @staticmethod
    def get_supported_extensions() -> list:
        """Get list of all supported file extensions."""
        extensions = []
        for parser_class in PARSER_REGISTRY.values():
            extensions.extend(parser_class.SUPPORTED_EXTENSIONS)
        return extensions
    
    @staticmethod
    def get_parser_info() -> Dict[str, Dict[str, Any]]:
        """Get information about available parsers."""
        info = {}
        for name, parser_class in PARSER_REGISTRY.items():
            info[name] = {
                'class': parser_class.__name__,
                'extensions': parser_class.SUPPORTED_EXTENSIONS,
                'description': parser_class.__doc__.split('\n')[0] if parser_class.__doc__ else ''
            }
        return info
