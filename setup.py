"""Setup script for File Parser Agent."""

from setuptools import setup, find_packages
from pathlib import Path

# Read README
readme_path = Path(__file__).parent / "README.md"
long_description = readme_path.read_text(encoding='utf-8') if readme_path.exists() else ""

setup(
    name="file-parser-agent",
    version="1.0.0",
    author="File Parser Agent",
    description="Document processing tool that extracts structured content from business documents",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/file-parser-agent/file-parser-agent",
    packages=find_packages(),
    package_data={
        'src.web': ['templates/*.html', 'static/*'],
    },
    include_package_data=True,
    python_requires=">=3.9",
    install_requires=[
        "PyPDF2>=3.0.0",
        "python-docx>=1.1.0",
        "openpyxl>=3.1.0",
        "python-pptx>=0.6.23",
        "flask>=3.0.0",
        "Pillow>=10.0.0",
    ],
    extras_require={
        "vision": [
            "anthropic>=0.18.0",
        ],
        "mcp": [
            "mcp>=1.0.0",
        ],
        "validation": [
            "python-magic>=0.4.27",
        ],
        "all": [
            "anthropic>=0.18.0",
            "mcp>=1.0.0",
            "python-magic>=0.4.27",
        ],
    },
    entry_points={
        "console_scripts": [
            "file-parser-cli=src.cli.commands:main",
            "file-parser-mcp=src.mcp.server:run_server",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Text Processing :: General",
        "Topic :: Office/Business",
    ],
    keywords="pdf word excel powerpoint document parser extractor converter",
)
