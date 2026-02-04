"""CLI commands for File Parser Agent.

Provides command-line interface for:
- Parsing documents
- Interactive chat mode
- Listing and managing outputs
"""

import argparse
import json
import sys
import os
from pathlib import Path
from typing import Optional

from ..api.wrapper import FileParserAgent
from ..config import OUTPUT_FORMATS


def create_parser() -> argparse.ArgumentParser:
    """Create argument parser."""
    parser = argparse.ArgumentParser(
        prog='file-parser-cli',
        description='File Parser Agent - Extract structured content from documents',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  file-parser-cli parse document.pdf
  file-parser-cli parse report.docx --format markdown --output report.md
  file-parser-cli extract-text presentation.pptx
  file-parser-cli extract-tables data.xlsx --format csv
  file-parser-cli list
  file-parser-cli chat
"""
    )
    
    # Global options
    parser.add_argument(
        '--api-key',
        help='Anthropic API key for vision features (or set ANTHROPIC_API_KEY env var)',
        default=os.environ.get('ANTHROPIC_API_KEY')
    )
    parser.add_argument(
        '--no-vision',
        action='store_true',
        help='Disable AI vision analysis'
    )
    parser.add_argument(
        '--output-dir',
        type=Path,
        help='Directory for output files'
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Parse command
    parse_parser = subparsers.add_parser(
        'parse',
        help='Parse a document file'
    )
    parse_parser.add_argument(
        'file',
        type=Path,
        help='Document file to parse'
    )
    parse_parser.add_argument(
        '-f', '--format',
        choices=OUTPUT_FORMATS,
        default='json',
        help='Output format (default: json)'
    )
    parse_parser.add_argument(
        '-o', '--output',
        type=Path,
        help='Output file path (default: auto-generated)'
    )
    parse_parser.add_argument(
        '--no-images',
        action='store_true',
        help='Skip image analysis'
    )
    parse_parser.add_argument(
        '--stdout',
        action='store_true',
        help='Output to stdout instead of file'
    )
    
    # Extract text command
    text_parser = subparsers.add_parser(
        'extract-text',
        help='Extract plain text from document'
    )
    text_parser.add_argument(
        'file',
        type=Path,
        help='Document file'
    )
    text_parser.add_argument(
        '-o', '--output',
        type=Path,
        help='Output file (default: stdout)'
    )
    
    # Extract tables command
    tables_parser = subparsers.add_parser(
        'extract-tables',
        help='Extract tables from document'
    )
    tables_parser.add_argument(
        'file',
        type=Path,
        help='Document file'
    )
    tables_parser.add_argument(
        '-f', '--format',
        choices=['json', 'csv'],
        default='json',
        help='Output format (default: json)'
    )
    tables_parser.add_argument(
        '-o', '--output',
        type=Path,
        help='Output file (default: stdout)'
    )
    
    # Analyze image command
    image_parser = subparsers.add_parser(
        'analyze-image',
        help='Analyze an image with AI vision'
    )
    image_parser.add_argument(
        'file',
        type=Path,
        help='Image file to analyze'
    )
    image_parser.add_argument(
        '--prompt',
        help='Custom analysis prompt'
    )
    
    # List outputs command
    list_parser = subparsers.add_parser(
        'list',
        help='List saved output files'
    )
    list_parser.add_argument(
        '--json',
        action='store_true',
        help='Output as JSON'
    )
    
    # Delete output command
    delete_parser = subparsers.add_parser(
        'delete',
        help='Delete an output file'
    )
    delete_parser.add_argument(
        'filename',
        help='Filename to delete'
    )
    
    # Clear outputs command
    subparsers.add_parser(
        'clear',
        help='Delete all output files'
    )
    
    # Info command
    subparsers.add_parser(
        'info',
        help='Show supported formats and parser info'
    )
    
    # Chat command
    chat_parser = subparsers.add_parser(
        'chat',
        help='Interactive chat mode'
    )
    
    return parser


def cmd_parse(agent: FileParserAgent, args) -> int:
    """Handle parse command."""
    try:
        print(f"Parsing: {args.file}", file=sys.stderr)
        
        result = agent.parse_document(
            args.file,
            analyze_images=not args.no_images
        )
        
        if args.stdout:
            # Output to stdout
            formatted = agent.format_output(result, args.format)
            print(formatted)
        else:
            # Save to file
            output_name = args.output.stem if args.output else None
            path = agent.save_output(result, args.format, output_name)
            print(f"Saved to: {path}", file=sys.stderr)
        
        return 0
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def cmd_extract_text(agent: FileParserAgent, args) -> int:
    """Handle extract-text command."""
    try:
        text = agent.extract_text(args.file)
        
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(text)
            print(f"Saved to: {args.output}", file=sys.stderr)
        else:
            print(text)
        
        return 0
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def cmd_extract_tables(agent: FileParserAgent, args) -> int:
    """Handle extract-tables command."""
    try:
        tables = agent.extract_tables(args.file)
        
        if args.format == 'json':
            output = json.dumps(tables, indent=2, default=str)
        else:  # csv
            import csv
            import io
            buffer = io.StringIO()
            writer = csv.writer(buffer)
            for table in tables:
                if table.get('headers'):
                    writer.writerow(table['headers'])
                for row in table.get('data', []):
                    writer.writerow(row)
                writer.writerow([])  # Blank row between tables
            output = buffer.getvalue()
        
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(output)
            print(f"Saved to: {args.output}", file=sys.stderr)
        else:
            print(output)
        
        return 0
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def cmd_analyze_image(agent: FileParserAgent, args) -> int:
    """Handle analyze-image command."""
    try:
        result = agent.analyze_image(args.file, prompt=args.prompt)
        
        if result.get('success'):
            print(result['description'])
        else:
            print(f"Error: {result.get('error')}", file=sys.stderr)
            return 1
        
        return 0
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def cmd_list(agent: FileParserAgent, args) -> int:
    """Handle list command."""
    outputs = agent.list_outputs()
    
    if args.json:
        print(json.dumps(outputs, indent=2))
    else:
        if not outputs:
            print("No output files found.")
        else:
            print(f"{'Filename':<40} {'Size':>10} {'Modified'}")
            print("-" * 70)
            for f in outputs:
                size = f'{f["size_bytes"]:,} B'
                print(f"{f['filename']:<40} {size:>10} {f['modified'][:19]}")
    
    return 0


def cmd_delete(agent: FileParserAgent, args) -> int:
    """Handle delete command."""
    if agent.delete_output(args.filename):
        print(f"Deleted: {args.filename}")
        return 0
    else:
        print(f"File not found: {args.filename}", file=sys.stderr)
        return 1


def cmd_clear(agent: FileParserAgent, args) -> int:
    """Handle clear command."""
    confirm = input("Delete all output files? (y/N): ")
    if confirm.lower() == 'y':
        count = agent.clear_outputs()
        print(f"Deleted {count} files.")
        return 0
    else:
        print("Cancelled.")
        return 0


def cmd_info(agent: FileParserAgent, args) -> int:
    """Handle info command."""
    formats = agent.get_supported_formats()
    parsers = agent.get_parser_info()
    
    print("File Parser Agent")
    print("=" * 40)
    print()
    print("Supported Input Formats:")
    for ext in formats['input']:
        print(f"  {ext}")
    print()
    print("Supported Output Formats:")
    for fmt in formats['output']:
        print(f"  {fmt}")
    print()
    print("Available Parsers:")
    for name, info in parsers.items():
        print(f"  {name}: {info['extensions']}")
    
    return 0


def cmd_chat(agent: FileParserAgent, args) -> int:
    """Handle chat command - interactive mode."""
    print("File Parser Agent - Interactive Mode")
    print("Type 'help' for commands, 'quit' to exit.")
    print()
    
    while True:
        try:
            user_input = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        
        if not user_input:
            continue
        
        cmd = user_input.lower().split()[0]
        args_str = user_input[len(cmd):].strip()
        
        if cmd in ('quit', 'exit', 'q'):
            break
        
        elif cmd == 'help':
            print("""
Commands:
  parse <file> [format]  - Parse a document
  text <file>            - Extract text
  tables <file>          - Extract tables
  image <file>           - Analyze image
  list                   - List outputs
  formats                - Show supported formats
  quit                   - Exit
""")
        
        elif cmd == 'parse':
            parts = args_str.split()
            if not parts:
                print("Usage: parse <file> [format]")
                continue
            file_path = parts[0]
            fmt = parts[1] if len(parts) > 1 else 'json'
            try:
                result = agent.parse_document(file_path)
                formatted = agent.format_output(result, fmt)
                print(formatted[:2000])  # Limit output
                if len(formatted) > 2000:
                    print(f"\n... ({len(formatted)} total characters)")
            except Exception as e:
                print(f"Error: {e}")
        
        elif cmd == 'text':
            if not args_str:
                print("Usage: text <file>")
                continue
            try:
                text = agent.extract_text(args_str)
                print(text[:2000])
                if len(text) > 2000:
                    print(f"\n... ({len(text)} total characters)")
            except Exception as e:
                print(f"Error: {e}")
        
        elif cmd == 'tables':
            if not args_str:
                print("Usage: tables <file>")
                continue
            try:
                tables = agent.extract_tables(args_str)
                print(json.dumps(tables, indent=2)[:2000])
            except Exception as e:
                print(f"Error: {e}")
        
        elif cmd == 'image':
            if not args_str:
                print("Usage: image <file>")
                continue
            try:
                result = agent.analyze_image(args_str)
                if result.get('success'):
                    print(result['description'])
                else:
                    print(f"Error: {result.get('error')}")
            except Exception as e:
                print(f"Error: {e}")
        
        elif cmd == 'list':
            outputs = agent.list_outputs()
            for f in outputs[:10]:
                print(f"  {f['filename']}")
            if len(outputs) > 10:
                print(f"  ... and {len(outputs) - 10} more")
        
        elif cmd == 'formats':
            formats = agent.get_supported_formats()
            print(f"Input: {', '.join(formats['input'])}")
            print(f"Output: {', '.join(formats['output'])}")
        
        else:
            print(f"Unknown command: {cmd}. Type 'help' for commands.")
    
    print("Goodbye!")
    return 0


def main():
    """Main entry point."""
    parser = create_parser()
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 0
    
    # Initialize agent
    agent = FileParserAgent(
        output_dir=args.output_dir,
        enable_vision=not args.no_vision,
        anthropic_api_key=args.api_key
    )
    
    # Dispatch to command handler
    commands = {
        'parse': cmd_parse,
        'extract-text': cmd_extract_text,
        'extract-tables': cmd_extract_tables,
        'analyze-image': cmd_analyze_image,
        'list': cmd_list,
        'delete': cmd_delete,
        'clear': cmd_clear,
        'info': cmd_info,
        'chat': cmd_chat,
    }
    
    handler = commands.get(args.command)
    if handler:
        return handler(agent, args)
    else:
        parser.print_help()
        return 1


if __name__ == '__main__':
    sys.exit(main())
