"""Configuration settings for File Parser Agent."""

import os
from pathlib import Path

# Detect if running on Render.com (or similar cloud platform)
IS_RENDER = os.environ.get('RENDER', 'false').lower() == 'true'

# Base directories
BASE_DIR = Path(__file__).parent.parent

# On Render.com, use /tmp for ephemeral storage since the filesystem is read-only
# except for /tmp directory
if IS_RENDER:
    UPLOADS_DIR = Path('/tmp/uploads')
    OUTPUTS_DIR = Path('/tmp/outputs')
    LOGS_DIR = Path('/tmp/logs')
else:
    UPLOADS_DIR = BASE_DIR / "uploads"
    OUTPUTS_DIR = BASE_DIR / "outputs"
    LOGS_DIR = BASE_DIR / "logs"

# Create directories if they don't exist
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)

# File constraints
MAX_FILE_SIZE_MB = 50
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024

# Supported file extensions
SUPPORTED_EXTENSIONS = {
    'pdf': ['.pdf'],
    'word': ['.docx', '.doc'],
    'excel': ['.xlsx', '.xls'],
    'powerpoint': ['.pptx', '.ppt']
}

ALL_SUPPORTED_EXTENSIONS = [ext for exts in SUPPORTED_EXTENSIONS.values() for ext in exts]

# Output formats
OUTPUT_FORMATS = ['json', 'markdown', 'csv', 'txt']

# API Configuration
ANTHROPIC_API_KEY = os.environ.get('ANTHROPIC_API_KEY', '')
CLAUDE_MODEL = 'claude-sonnet-4-20250514'
MAX_IMAGE_SIZE_MB = 5
MAX_IMAGE_SIZE_BYTES = MAX_IMAGE_SIZE_MB * 1024 * 1024

# Logging
LOG_FILE = LOGS_DIR / "parser.log"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
