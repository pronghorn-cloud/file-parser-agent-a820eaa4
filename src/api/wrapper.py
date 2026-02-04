"""Main Python API wrapper for File Parser Agent."""

import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import logging

from ..config import UPLOADS_DIR, OUTPUTS_DIR, OUTPUT_FORMATS
from ..services.parsing_engine import ParsingEngine
from ..services.vision import VisionService
from ..utils.output_manager import OutputManager
from ..utils.validation import FileValidator, ValidationError
from ..parsers.base import ParsedDocument

logger = logging.getLogger(__name__)


class FileParserAgent:
    """Unified Python API for all document parsing operations.
    
    This is the main entry point for using the File Parser Agent.
    It provides a clean, high-level interface for:
    - Parsing documents (PDF, Word, Excel, PowerPoint)
    - Extracting specific content (text, tables, metadata)
    - Converting to output formats (JSON, Markdown, CSV, TXT)
    - Managing outputs (save, list, delete)
    - AI vision analysis of images/charts
    
    Example:
        >>> agent = FileParserAgent()
        >>> result = agent.parse_document('report.pdf')
        >>> agent.save_output(result, format='markdown')
    """
    
    def __init__(
        self,
        output_dir: Path = None,
        enable_vision: bool = True,
        anthropic_api_key: str = None
    ):
        """Initialize the File Parser Agent.
        
        Args:
            output_dir: Directory for saving outputs (default: outputs/)
            enable_vision: Enable AI vision for image analysis
            anthropic_api_key: API key for Anthropic Claude (for vision)
        """
        self.output_manager = OutputManager(output_dir)
        
        # Initialize vision service if API key provided
        vision_service = None
        if enable_vision and anthropic_api_key:
            try:
                vision_service = VisionService(api_key=anthropic_api_key)
            except ImportError:
                logger.warning("Vision service unavailable")
        
        self.parsing_engine = ParsingEngine(
            enable_vision=enable_vision,
            vision_service=vision_service
        )
        self.validator = FileValidator()
    
    # ==================== Document Parsing ====================
    
    def parse_document(
        self,
        file_path: Union[str, Path],
        analyze_images: bool = True
    ) -> Dict[str, Any]:
        """Parse a document and extract all content.
        
        This is the main parsing method that extracts text, tables,
        metadata, and optionally analyzes images.
        
        Args:
            file_path: Path to document file
            analyze_images: Whether to use AI for image analysis
            
        Returns:
            Dictionary with parsed content:
            {
                'filename': str,
                'file_type': str,
                'parsed_at': str,
                'metadata': dict,
                'content': dict,
                'tables': list,
                'images': list,
                'errors': list
            }
            
        Raises:
            ValidationError: If file is invalid
            ValueError: If file type unsupported
        """
        return self.parsing_engine.parse_to_dict(
            Path(file_path),
            analyze_images=analyze_images
        )
    
    def extract_text(self, file_path: Union[str, Path]) -> str:
        """Extract plain text from a document.
        
        Args:
            file_path: Path to document
            
        Returns:
            Plain text string
        """
        return self.parsing_engine.extract_text(Path(file_path))
    
    def extract_tables(self, file_path: Union[str, Path]) -> List[Dict[str, Any]]:
        """Extract tables from a document.
        
        Args:
            file_path: Path to document
            
        Returns:
            List of table dictionaries with structure:
            [
                {
                    'name': str (optional),
                    'rows': int,
                    'columns': int,
                    'headers': list,
                    'data': list[list]
                },
                ...
            ]
        """
        return self.parsing_engine.extract_tables(Path(file_path))
    
    def extract_metadata(self, file_path: Union[str, Path]) -> Dict[str, Any]:
        """Extract metadata from a document.
        
        Args:
            file_path: Path to document
            
        Returns:
            Dictionary of metadata fields
        """
        return self.parsing_engine.extract_metadata(Path(file_path))
    
    # ==================== Image Analysis ====================
    
    def analyze_image(
        self,
        image_path: Union[str, Path, bytes],
        content_type: str = 'image/png',
        prompt: str = None
    ) -> Dict[str, Any]:
        """Analyze an image using AI vision.
        
        Args:
            image_path: Path to image file or raw bytes
            content_type: MIME type if providing bytes
            prompt: Custom analysis prompt
            
        Returns:
            {
                'success': bool,
                'description': str (if success),
                'error': str (if failed)
            }
        """
        if not self.parsing_engine.vision_service:
            return {
                'success': False,
                'error': 'Vision service not configured'
            }
        
        # Load image if path provided
        if isinstance(image_path, (str, Path)):
            path = Path(image_path)
            with open(path, 'rb') as f:
                image_data = f.read()
            
            # Detect content type from extension
            ext_map = {
                '.png': 'image/png',
                '.jpg': 'image/jpeg',
                '.jpeg': 'image/jpeg',
                '.gif': 'image/gif',
                '.webp': 'image/webp'
            }
            content_type = ext_map.get(path.suffix.lower(), 'image/png')
        else:
            image_data = image_path
        
        return self.parsing_engine.vision_service.analyze_image(
            image_data,
            content_type,
            prompt
        )
    
    # ==================== Output Management ====================
    
    def save_output(
        self,
        document: Union[Dict[str, Any], ParsedDocument],
        format: str = 'json',
        filename: str = None
    ) -> str:
        """Save parsed document to file.
        
        Args:
            document: Parsed document dict or ParsedDocument
            format: Output format ('json', 'markdown', 'csv', 'txt')
            filename: Custom filename (without extension)
            
        Returns:
            Path to saved file
        """
        path = self.output_manager.save(
            document,
            output_format=format,
            filename=filename
        )
        return str(path)
    
    def format_output(
        self,
        document: Union[Dict[str, Any], ParsedDocument],
        format: str = 'json'
    ) -> str:
        """Convert document to specified format without saving.
        
        Args:
            document: Parsed document
            format: Output format
            
        Returns:
            Formatted string content
        """
        import json
        
        if isinstance(document, ParsedDocument):
            data = document.to_dict()
        else:
            data = document
        
        format = format.lower()
        if format == 'json':
            return json.dumps(data, indent=2, default=str)
        elif format == 'markdown':
            return self.output_manager._to_markdown(data)
        elif format == 'txt':
            return self.output_manager._to_plain_text(data)
        else:
            raise ValueError(f"Unsupported format for in-memory conversion: {format}")
    
    def list_outputs(self) -> List[Dict[str, Any]]:
        """List all saved output files.
        
        Returns:
            List of file info dictionaries
        """
        return self.output_manager.list_outputs()
    
    def get_output(self, filename: str) -> Optional[str]:
        """Get path to a saved output file.
        
        Args:
            filename: Name of output file
            
        Returns:
            Path string if exists, None otherwise
        """
        path = self.output_manager.get_output(filename)
        return str(path) if path else None
    
    def delete_output(self, filename: str) -> bool:
        """Delete a saved output file.
        
        Args:
            filename: Name of file to delete
            
        Returns:
            True if deleted, False if not found
        """
        return self.output_manager.delete_output(filename)
    
    def clear_outputs(self) -> int:
        """Delete all saved output files.
        
        Returns:
            Number of files deleted
        """
        return self.output_manager.clear_outputs()
    
    # ==================== Utility Methods ====================
    
    def validate_file(self, file_path: Union[str, Path]) -> Dict[str, Any]:
        """Validate a file before parsing.
        
        Args:
            file_path: Path to file
            
        Returns:
            {
                'valid': bool,
                'error': str (if invalid),
                'file_type': str (if valid)
            }
        """
        path = Path(file_path)
        is_valid, error = self.validator.validate(path)
        
        result = {'valid': is_valid}
        if is_valid:
            result['file_type'] = self.validator.get_file_type(path)
        else:
            result['error'] = error
        
        return result
    
    @staticmethod
    def get_supported_formats() -> Dict[str, List[str]]:
        """Get supported input and output formats.
        
        Returns:
            {
                'input': ['pdf', 'docx', ...],
                'output': ['json', 'markdown', ...]
            }
        """
        return {
            'input': ParsingEngine.get_supported_extensions(),
            'output': OUTPUT_FORMATS
        }
    
    @staticmethod
    def get_parser_info() -> Dict[str, Dict[str, Any]]:
        """Get information about available parsers."""
        return ParsingEngine.get_parser_info()
    
    # ==================== Convenience Methods ====================
    
    def parse_and_save(
        self,
        file_path: Union[str, Path],
        output_format: str = 'json',
        output_filename: str = None,
        analyze_images: bool = True
    ) -> Dict[str, Any]:
        """Parse a document and save output in one step.
        
        Args:
            file_path: Path to document
            output_format: Desired output format
            output_filename: Custom output filename
            analyze_images: Whether to analyze images
            
        Returns:
            {
                'parsed': dict (parsed content),
                'output_path': str (saved file path)
            }
        """
        parsed = self.parse_document(file_path, analyze_images=analyze_images)
        output_path = self.save_output(
            parsed,
            format=output_format,
            filename=output_filename
        )
        
        return {
            'parsed': parsed,
            'output_path': output_path
        }
