"""Main entry point for running File Parser Agent as a module.

Usage:
    python -m src [command] [args]
    python -m src --help
"""

import sys


def main():
    """Main entry point."""
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == 'cli':
            # Run CLI
            sys.argv = sys.argv[1:]  # Remove 'cli' from args
            from .cli.commands import main as cli_main
            return cli_main()
        
        elif command == 'web':
            # Run web server
            from .web.app import app
            port = 5000
            if len(sys.argv) > 2:
                try:
                    port = int(sys.argv[2])
                except ValueError:
                    pass
            print(f"Starting web server on http://localhost:{port}")
            app.run(debug=True, port=port)
            return 0
        
        elif command == 'mcp':
            # Run MCP server
            import os
            from .mcp.server import run_server
            api_key = os.environ.get('ANTHROPIC_API_KEY')
            run_server(api_key)
            return 0
        
        elif command == '--help' or command == '-h':
            print_help()
            return 0
        
        else:
            print(f"Unknown command: {command}")
            print_help()
            return 1
    else:
        print_help()
        return 0


def print_help():
    """Print help message."""
    print("""
File Parser Agent - Document Processing Tool

Usage:
    python -m src <command> [options]

Commands:
    cli [args]      Run the command-line interface
    web [port]      Start the web server (default port: 5000)
    mcp             Start the MCP server for Claude Desktop

Examples:
    python -m src cli parse document.pdf
    python -m src cli extract-text report.docx
    python -m src web 8080
    python -m src mcp

For CLI help:
    python -m src cli --help
""")


if __name__ == '__main__':
    sys.exit(main())
