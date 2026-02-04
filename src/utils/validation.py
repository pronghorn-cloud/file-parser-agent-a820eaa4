"""File validation utilities."""

import os
from pathlib import Path
from typing import Tuple, Optional
import logging

try:
    import magic
    HAS_MAGIC = True
except ImportError:
    HAS_MAGIC = False

from ..config import (
    MAX_FILE_SIZE_BYTES,
    MAX_FILE_SIZE_MB,
    ALL_SUPPORTED_EXTENSIONS,
    SUPPORTED_EXTENSIONS
)

logger = logging.getLogger(__name__)


# MIME type mappings for supported files
MIME_TYPE_MAP = {
    'application/pdf': '.pdf',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document': '.docx',
    'application/msword': '.doc',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': '.xlsx',
    'application/vnd.ms-excel': '.xls',
    'application/vnd.openxmlformats-officedocument.presentationml.presentation': '.pptx',
    'application/vnd.ms-powerpoint': '.ppt',
}


class ValidationError(Exception):
    """Custom exception for validation errors."""
    pass


class FileValidator:
    """Validates uploaded files meet specified criteria.
    
    Ensures files meet:
    - Maximum size limit (50MB default)
    - Supported file extension
    - Valid content type (MIME type verification)
    """
    
    def __init__(
        self,
        max_size_bytes: int = MAX_FILE_SIZE_BYTES,
        allowed_extensions: list = None
    ):
        """Initialize validator.
        
        Args:
            max_size_bytes: Maximum allowed file size in bytes
            allowed_extensions: List of allowed extensions (with dots)
        """
        self.max_size_bytes = max_size_bytes
        self.allowed_extensions = allowed_extensions or ALL_SUPPORTED_EXTENSIONS
    
    def validate(self, file_path: Path) -> Tuple[bool, Optional[str]]:
        """Validate a file.
        
        Args:
            file_path: Path to the file to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        file_path = Path(file_path)
        
        # Check file exists
        if not file_path.exists():
            return False, f"File not found: {file_path}"
        
        # Check file is actually a file
        if not file_path.is_file():
            return False, f"Not a file: {file_path}"
        
        # Check file size
        is_valid, error = self._validate_size(file_path)
        if not is_valid:
            return False, error
        
        # Check extension
        is_valid, error = self._validate_extension(file_path)
        if not is_valid:
            return False, error
        
        # Check content type (MIME)
        is_valid, error = self._validate_content_type(file_path)
        if not is_valid:
            return False, error
        
        return True, None
    
    def _validate_size(self, file_path: Path) -> Tuple[bool, Optional[str]]:
        """Validate file size."""
        file_size = file_path.stat().st_size
        
        if file_size == 0:
            return False, "File is empty"
        
        if file_size > self.max_size_bytes:
            size_mb = file_size / (1024 * 1024)
            max_mb = self.max_size_bytes / (1024 * 1024)
            return False, f"File too large: {size_mb:.1f}MB exceeds maximum {max_mb:.0f}MB"
        
        return True, None
    
    def _validate_extension(self, file_path: Path) -> Tuple[bool, Optional[str]]:
        """Validate file extension."""
        ext = file_path.suffix.lower()
        
        if not ext:
            return False, "File has no extension"
        
        if ext not in self.allowed_extensions:
            return False, f"Unsupported file type: {ext}. Supported: {', '.join(self.allowed_extensions)}"
        
        return True, None
    
    def _validate_content_type(self, file_path: Path) -> Tuple[bool, Optional[str]]:
        """Validate file content type using magic bytes."""
        if not HAS_MAGIC:
            logger.debug("python-magic not available, skipping content type validation")
            return True, None
        
        try:
            mime_type = magic.from_file(str(file_path), mime=True)
            expected_ext = file_path.suffix.lower()
            
            # Check if MIME type matches expected extension
            if mime_type in MIME_TYPE_MAP:
                actual_ext = MIME_TYPE_MAP[mime_type]
                # Allow for format families (e.g., .doc and .docx are both Word)
                expected_family = self._get_format_family(expected_ext)
                actual_family = self._get_format_family(actual_ext)
                
                if expected_family != actual_family:
                    return False, f"File content doesn't match extension. Expected {expected_ext}, detected {actual_ext}"
            else:
                logger.warning(f"Unknown MIME type: {mime_type} for {file_path}")
            
            return True, None
            
        except Exception as e:
            logger.warning(f"Could not verify content type: {e}")
            return True, None  # Allow on error
    
    def _get_format_family(self, ext: str) -> Optional[str]:
        """Get the format family for an extension."""
        for family, extensions in SUPPORTED_EXTENSIONS.items():
            if ext in extensions:
                return family
        return None
    
    def get_file_type(self, file_path: Path) -> Optional[str]:
        """Get the file type category for a file.
        
        Args:
            file_path: Path to file
            
        Returns:
            Type string ('pdf', 'word', 'excel', 'powerpoint') or None
        """
        ext = Path(file_path).suffix.lower()
        return self._get_format_family(ext)
