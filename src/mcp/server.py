"""MCP Server implementation for Claude Desktop.

Provides Model Context Protocol server that exposes file parsing
functionality as tools for Claude Desktop.
"""

import asyncio
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import (
        Tool,
        TextContent,
        CallToolResult,
        ListToolsResult
    )
    HAS_MCP = True
except ImportError:
    HAS_MCP = False

from ..api.wrapper import FileParserAgent
from ..config import UPLOADS_DIR, OUTPUTS_DIR

logger = logging.getLogger(__name__)


# Tool definitions
TOOLS = [
    {
        "name": "parse_document",
        "description": "Parse a document file and extract structured content including text, tables, metadata, and images. Supports PDF, Word (.docx), Excel (.xlsx), and PowerPoint (.pptx) files.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "Path to the document file to parse"
                },
                "analyze_images": {
                    "type": "boolean",
                    "description": "Whether to analyze images using AI vision (default: true)",
                    "default": True
                }
            },
            "required": ["file_path"]
        }
    },
    {
        "name": "extract_text",
        "description": "Extract only the plain text content from a document.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "Path to the document file"
                }
            },
            "required": ["file_path"]
        }
    },
    {
        "name": "extract_tables",
        "description": "Extract only tables from a document. Returns structured table data with rows and columns.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "Path to the document file"
                }
            },
            "required": ["file_path"]
        }
    },
    {
        "name": "analyze_image",
        "description": "Analyze an image file using AI vision to get a detailed description.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "image_path": {
                    "type": "string",
                    "description": "Path to the image file"
                },
                "prompt": {
                    "type": "string",
                    "description": "Custom prompt for the analysis (optional)"
                }
            },
            "required": ["image_path"]
        }
    },
    {
        "name": "format_output",
        "description": "Convert parsed document data to a specific format (JSON, Markdown, or plain text).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "document_data": {
                    "type": "object",
                    "description": "Parsed document data (from parse_document)"
                },
                "format": {
                    "type": "string",
                    "enum": ["json", "markdown", "txt"],
                    "description": "Output format",
                    "default": "markdown"
                }
            },
            "required": ["document_data"]
        }
    },
    {
        "name": "save_output",
        "description": "Save parsed document to a file in the specified format.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "document_data": {
                    "type": "object",
                    "description": "Parsed document data (from parse_document)"
                },
                "format": {
                    "type": "string",
                    "enum": ["json", "markdown", "csv", "txt"],
                    "description": "Output format",
                    "default": "json"
                },
                "filename": {
                    "type": "string",
                    "description": "Custom filename without extension (optional)"
                }
            },
            "required": ["document_data"]
        }
    },
    {
        "name": "list_outputs",
        "description": "List all previously saved output files.",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "get_supported_formats",
        "description": "Get information about supported input and output formats.",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    }
]


class MCPServer:
    """MCP Server for File Parser Agent.
    
    Exposes document parsing functionality as MCP tools
    for integration with Claude Desktop.
    """
    
    def __init__(self, anthropic_api_key: str = None):
        """Initialize MCP server.
        
        Args:
            anthropic_api_key: API key for vision features
        """
        if not HAS_MCP:
            raise ImportError(
                "mcp library is required for MCP server. "
                "Install with: pip install mcp"
            )
        
        self.agent = FileParserAgent(
            enable_vision=bool(anthropic_api_key),
            anthropic_api_key=anthropic_api_key
        )
        self.server = Server("file-parser-agent")
        self._setup_handlers()
    
    def _setup_handlers(self):
        """Set up MCP request handlers."""
        
        @self.server.list_tools()
        async def list_tools() -> List[Tool]:
            """Return list of available tools."""
            return [
                Tool(
                    name=tool["name"],
                    description=tool["description"],
                    inputSchema=tool["inputSchema"]
                )
                for tool in TOOLS
            ]
        
        @self.server.call_tool()
        async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
            """Handle tool calls."""
            try:
                result = await self._execute_tool(name, arguments)
                return [TextContent(
                    type="text",
                    text=json.dumps(result, indent=2, default=str)
                )]
            except Exception as e:
                logger.error(f"Tool execution error: {e}")
                return [TextContent(
                    type="text",
                    text=json.dumps({"error": str(e)})
                )]
    
    async def _execute_tool(
        self,
        name: str,
        arguments: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute a tool and return result."""
        
        if name == "parse_document":
            file_path = arguments["file_path"]
            analyze_images = arguments.get("analyze_images", True)
            return self.agent.parse_document(file_path, analyze_images)
        
        elif name == "extract_text":
            file_path = arguments["file_path"]
            text = self.agent.extract_text(file_path)
            return {"text": text}
        
        elif name == "extract_tables":
            file_path = arguments["file_path"]
            tables = self.agent.extract_tables(file_path)
            return {"tables": tables, "count": len(tables)}
        
        elif name == "analyze_image":
            image_path = arguments["image_path"]
            prompt = arguments.get("prompt")
            return self.agent.analyze_image(image_path, prompt=prompt)
        
        elif name == "format_output":
            document_data = arguments["document_data"]
            format_type = arguments.get("format", "markdown")
            formatted = self.agent.format_output(document_data, format_type)
            return {"formatted": formatted, "format": format_type}
        
        elif name == "save_output":
            document_data = arguments["document_data"]
            format_type = arguments.get("format", "json")
            filename = arguments.get("filename")
            path = self.agent.save_output(document_data, format_type, filename)
            return {"saved_to": path, "format": format_type}
        
        elif name == "list_outputs":
            outputs = self.agent.list_outputs()
            return {"outputs": outputs, "count": len(outputs)}
        
        elif name == "get_supported_formats":
            return self.agent.get_supported_formats()
        
        else:
            raise ValueError(f"Unknown tool: {name}")
    
    async def run(self):
        """Run the MCP server."""
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                self.server.create_initialization_options()
            )


def run_server(anthropic_api_key: str = None):
    """Run the MCP server.
    
    Args:
        anthropic_api_key: Optional API key for vision features
    """
    if not HAS_MCP:
        print("Error: mcp library not installed.")
        print("Install with: pip install mcp")
        return
    
    server = MCPServer(anthropic_api_key)
    asyncio.run(server.run())


if __name__ == "__main__":
    import os
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    run_server(api_key)
